"""
Job para verificar pagamentos online pendentes.
- Timeout Mercado Pago: 5 minutos
- Se expirar sem pagamento, cancela venda e libera estoque

Race-safe (C3): cada venda é processada sob lock de linha (FOR UPDATE SKIP LOCKED), com
re-leitura do status dentro da transação e revalidação do pagamento no Mercado Pago antes
de cancelar. Seguro para múltiplas instâncias da API rodando o loop simultaneamente.

Deve rodar a cada ~1 minuto (loop no lifespan do serviço; ver main.py).
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
import structlog

from config import settings
from models.venda import Venda, StatusVenda, StatusReserva
from schemas.venda import ConfirmarVendaRequest, PagamentoVendaCreate
from services.historico_status_service import HistoricoStatusService
from services.notificacao_service import NotificacaoService
from services.mercadopago_service import TIMEOUT_PAGAMENTO, MercadoPagoService
from services.venda_service import VendaService, EstoqueIndeterminadoError
from repositories.venda_repository import VendaRepository, ReservaEstoqueVendaRepository

log = structlog.get_logger()

# TIMEOUT_PAGAMENTO vem de services.mercadopago_service: é o mesmo prazo que a
# preferência do MP carrega em expiration_date_to. Duas cópias do número
# deixariam link pagável de venda já cancelada aqui.


async def _restaurar_carrinho_se_necessario(session: AsyncSession, venda) -> None:
    """
    Recria o carrinho no Redis a partir dos itens da venda cancelada.

    Mantém o pedido recuperável: ao abandonar/expirar o pagamento, o cliente reencontra
    seus itens no carrinho (mesma sessao_carrinho_id) e pode refazer o checkout.
    Não faz nada se a venda não tem sessão associada ou se o carrinho ainda existe.
    """
    from services.carrinho_service import CarrinhoService
    from schemas.loja import ItemCarrinhoCreate

    sessao_id = venda.sessao_carrinho_id
    if not sessao_id:
        return

    if await CarrinhoService.carrinho_existe(sessao_id, venda.empresa_id):
        return  # Carrinho intacto — nada a restaurar

    itens_restaurados = 0
    for item in venda.itens:
        try:
            await CarrinhoService.adicionar_item(
                sessao_id,
                venda.empresa_id,
                ItemCarrinhoCreate(
                    produto_id=item.produto_id,
                    variante_id=item.variante_id,
                    quantidade=item.quantidade
                ),
                session
            )
            itens_restaurados += 1
        except Exception as e:
            # Best-effort: o cancelamento já foi confirmado. Falha ao restaurar um item
            # (sem estoque, Redis/produtos indisponível) não deve interromper o job.
            log.warning(
                "restaurar_carrinho_item_falhou",
                venda_id=str(venda.id),
                produto_id=str(item.produto_id),
                erro=str(e)
            )

    log.info(
        "carrinho_restaurado_apos_cancelamento",
        venda_id=str(venda.id),
        sessao_id=sessao_id,
        itens_restaurados=itens_restaurados
    )


async def _confirmar_venda_revalidada(
    session: AsyncSession, venda, pagamento_aprovado: dict
) -> str:
    """
    Venda expirada mas com pagamento APROVADO no Mercado Pago → confirmar em vez de cancelar.

    Protege contra a corrida em que o pagamento é aprovado bem no limite do timeout e o
    webhook ainda não chegou. confirmar_venda é idempotente e faz a baixa de estoque.
    """
    payment_id = str(pagamento_aprovado.get("id"))
    venda.mercadopago_payment_id = payment_id
    await session.flush()  # confirmar_venda precisa enxergar o payment_id

    confirmar_data = ConfirmarVendaRequest(
        pagamentos=[
            PagamentoVendaCreate(
                forma_pagamento=MercadoPagoService._mapear_forma_pagamento(pagamento_aprovado),
                valor_pago=venda.valor_total,
                comprovante=payment_id,
            )
        ]
    )
    try:
        await VendaService.confirmar_venda(session, venda.empresa_id, venda.id, confirmar_data)
        log.warning(
            "venda_confirmada_na_revalidacao_timeout",
            venda_id=str(venda.id), payment_id=payment_id
        )
        return "confirmada_na_revalidacao"
    except EstoqueIndeterminadoError:
        # Marcada para reconciliação; não cancelar.
        return "reconciliacao_pendente"
    except ValueError:
        # Estoque insuficiente → confirmar_venda já cancelou e registrou reembolso necessário.
        return "cancelada_sem_estoque_na_revalidacao"


async def _cancelar_venda_timeout(session: AsyncSession, venda, agora: datetime) -> None:
    """Cancela uma venda expirada sem pagamento aprovado e libera as reservas de estoque."""
    # Liberar reservas de estoque (best-effort no serviço de estoque)
    for item in venda.itens:
        if item.estoque_reservado and not item.estoque_baixado:
            sucesso = await VendaService.liberar_reserva_estoque(
                venda.empresa_id, item.produto_id, item.variante_id,
                item.quantidade, venda.numero_venda
            )
            if not sucesso:
                log.warning(
                    "falha_liberar_reserva_timeout_pagamento",
                    produto_id=str(item.produto_id), venda_id=str(venda.id)
                )

    # Atualizar reservas no banco
    reservas = await ReservaEstoqueVendaRepository.listar_por_venda(session, venda.id)
    for reserva in reservas:
        if reserva.status == StatusReserva.RESERVADA.value:
            await ReservaEstoqueVendaRepository.atualizar(
                session, reserva.id,
                status=StatusReserva.LIBERADA.value, liberada_em=agora
            )

    await VendaRepository.atualizar(
        session, venda.empresa_id, venda.id,
        status=StatusVenda.CANCELADA.value,
        data_cancelada=agora,
        motivo_cancelamento="Cancelamento automático: timeout de pagamento (5min)"
    )

    await HistoricoStatusService.registrar_mudanca(
        session, venda.id,
        StatusVenda.PENDENTE_PAGAMENTO.value, StatusVenda.CANCELADA.value,
        None,  # Sistema
        "Cancelamento automático por timeout de pagamento (5min)"
    )


async def _processar_venda_timeout(
    session: AsyncSession, empresa_id: int, venda_id, agora: datetime
) -> str:
    """
    Processa uma venda candidata a timeout sob lock de linha (race-safe).

    Returns um rótulo do resultado para fins de contagem/log.
    """
    # Lock da venda (SKIP LOCKED): se outra instância já está tratando, pula.
    venda = await VendaRepository.buscar_por_id(
        session, empresa_id, venda_id,
        com_relacionamentos=True, com_lock=True, skip_locked=True
    )
    if venda is None:
        await session.rollback()
        return "ignorada_lock"

    # Re-leitura dentro da transação: só cancela se AINDA está PENDENTE_PAGAMENTO.
    if venda.status != StatusVenda.PENDENTE_PAGAMENTO.value:
        await session.rollback()
        return "ja_resolvida"

    # Re-checar o prazo com o dado travado.
    if (agora - venda.data_pedido) <= TIMEOUT_PAGAMENTO:
        await session.rollback()
        return "ainda_no_prazo"

    # Revalidar com o Mercado Pago antes de cancelar: nunca cancelar venda já paga.
    # Se a revalidação for inconclusiva (MP indisponível), ADIA o cancelamento — não
    # cancelar com resultado incerto (mesma filosofia do C4). A próxima rodada tenta de novo.
    try:
        pagamento_aprovado = await MercadoPagoService.buscar_pagamento_aprovado_por_venda(
            session, empresa_id, venda.id
        )
    except Exception as e:
        await session.rollback()
        log.warning(
            "timeout_revalidacao_mp_indisponivel_adiando_cancelamento",
            venda_id=str(venda.id), error=str(e)
        )
        return "revalidacao_indisponivel"

    if pagamento_aprovado:
        # confirmar_venda gerencia o próprio commit.
        return await _confirmar_venda_revalidada(session, venda, pagamento_aprovado)

    # Sem pagamento aprovado → cancelar por timeout.
    await _cancelar_venda_timeout(session, venda, agora)
    await session.commit()

    # Restaurar carrinho (best-effort) e notificar (fora da transação principal).
    await _restaurar_carrinho_se_necessario(session, venda)

    log.warning(
        "venda_cancelada_timeout_pagamento",
        venda_id=str(venda.id), numero_venda=venda.numero_venda, empresa_id=empresa_id
    )

    if venda.cliente_convidado_telefone:
        try:
            await NotificacaoService.enviar_pedido_cancelado(
                venda.cliente_convidado_telefone, venda.numero_venda, "Timeout de pagamento (5min)"
            )
        except Exception as e:
            log.warning(
                "erro_enviar_notificacao_cancelamento_pagamento",
                venda_id=str(venda.id), error=str(e)
            )
    return "cancelada"


async def verificar_pagamentos_pendentes():
    """
    Verifica vendas PENDENTE_PAGAMENTO expiradas (>5min) e cancela as não pagas.

    Cada venda é processada de forma isolada e race-safe (lock + re-leitura + revalidação),
    de modo que múltiplas instâncias e webhooks concorrentes não causem dupla execução nem
    cancelamento de venda paga.
    """
    log.info("job_verificar_pagamentos_pendentes_iniciado")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            agora = datetime.utcnow()

            # Candidatos (sem lock): vendas PENDENTE_PAGAMENTO com preferência Mercado Pago.
            query = select(Venda.id, Venda.empresa_id).where(
                and_(
                    Venda.status == StatusVenda.PENDENTE_PAGAMENTO.value,
                    Venda.data_pedido.isnot(None),
                    Venda.data_pedido < (agora - TIMEOUT_PAGAMENTO),
                    Venda.mercadopago_preference_id.isnot(None),
                )
            )
            result = await session.execute(query)
            candidatos = result.all()
            await session.rollback()  # encerra a transação de leitura

            contagem = {}
            for venda_id, empresa_id in candidatos:
                try:
                    rotulo = await _processar_venda_timeout(session, empresa_id, venda_id, agora)
                except Exception as e:
                    await session.rollback()
                    rotulo = "erro"
                    log.error(
                        "erro_processar_venda_timeout",
                        venda_id=str(venda_id), error=str(e)
                    )
                contagem[rotulo] = contagem.get(rotulo, 0) + 1

            log.info(
                "job_verificar_pagamentos_pendentes_concluido",
                candidatos=len(candidatos),
                resultados=contagem
            )

        except Exception as e:
            log.error("job_verificar_pagamentos_pendentes_erro", error=str(e))
        finally:
            await engine.dispose()


if __name__ == "__main__":
    """
    Executar:
    python jobs/verificar_pagamentos_pendentes.py

    Configurar cron (Linux) - a cada 1 minuto:
    */1 * * * * cd /path/to/vendas-service && python jobs/verificar_pagamentos_pendentes.py
    """
    asyncio.run(verificar_pagamentos_pendentes())
