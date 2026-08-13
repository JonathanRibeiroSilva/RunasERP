"""
Job de reconciliação de estoque (cross-service consistency — C4).

Trata vendas PAGAS cuja baixa de estoque ficou com resultado INDETERMINADO (timeout/erro
de comunicação com o serviço de estoque na confirmação). Essas vendas foram marcadas com
reconciliacao_estoque_pendente=True em vez de canceladas (nunca cancelar venda paga sem
saber o resultado real).

Para cada venda marcada: retenta a confirmação (que faz a baixa de estoque IDEMPOTENTE —
C1). Resultados possíveis:
- baixa OK            → venda confirmada, flag limpa.
- estoque insuficiente→ venda cancelada (reembolso necessário é logado em confirmar_venda).
- ainda indeterminado → permanece marcada para a próxima rodada.

Race-safe: lock por venda (FOR UPDATE SKIP LOCKED), seguro para múltiplas instâncias.
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
import structlog

from config import settings
from models.venda import Venda
from schemas.venda import ConfirmarVendaRequest, PagamentoVendaCreate
from services.mercadopago_service import MercadoPagoService
from services.venda_service import VendaService, EstoqueIndeterminadoError
from repositories.venda_repository import VendaRepository

log = structlog.get_logger()


async def _reconciliar_venda(session: AsyncSession, empresa_id: int, venda_id) -> str:
    """Reconcilia uma venda marcada, sob lock de linha. Retorna rótulo do resultado."""
    venda = await VendaRepository.buscar_por_id(
        session, empresa_id, venda_id,
        com_relacionamentos=True, com_lock=True, skip_locked=True
    )
    if venda is None:
        await session.rollback()
        return "ignorada_lock"

    # Re-leitura: outra execução/webhook pode já ter resolvido.
    if not venda.reconciliacao_estoque_pendente:
        await session.rollback()
        return "ja_reconciliada"

    # Reconstruir o pagamento aprovado para reexecutar a confirmação idempotente.
    payment_data = {}
    if venda.mercadopago_payment_id:
        payment_data = await MercadoPagoService.obter_detalhes_pagamento(
            session, empresa_id, venda.mercadopago_payment_id
        ) or {}

    confirmar_data = ConfirmarVendaRequest(
        pagamentos=[
            PagamentoVendaCreate(
                forma_pagamento=MercadoPagoService._mapear_forma_pagamento(payment_data),
                valor_pago=venda.valor_total,
                comprovante=venda.mercadopago_payment_id or "reconciliacao",
            )
        ]
    )

    try:
        # confirmar_venda gerencia o próprio commit; baixa de estoque é idempotente (C1).
        await VendaService.confirmar_venda(session, empresa_id, venda.id, confirmar_data)
        log.info("reconciliacao_estoque_confirmada", venda_id=str(venda.id))
        return "confirmada"
    except EstoqueIndeterminadoError:
        # Ainda indeterminado → permanece marcada para a próxima rodada.
        return "ainda_indeterminada"
    except ValueError:
        # Estoque insuficiente → confirmar_venda já cancelou e logou reembolso necessário.
        log.warning("reconciliacao_estoque_cancelada_sem_estoque", venda_id=str(venda.id))
        return "cancelada_sem_estoque"


async def reconciliar_estoque_vendas():
    """Reconcilia todas as vendas pagas com baixa de estoque indeterminada."""
    log.info("job_reconciliar_estoque_iniciado")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            query = select(Venda.id, Venda.empresa_id).where(
                and_(
                    Venda.reconciliacao_estoque_pendente.is_(True),
                    Venda.mercadopago_payment_id.isnot(None),
                )
            )
            result = await session.execute(query)
            candidatos = result.all()
            await session.rollback()

            contagem = {}
            for venda_id, empresa_id in candidatos:
                try:
                    rotulo = await _reconciliar_venda(session, empresa_id, venda_id)
                except Exception as e:
                    await session.rollback()
                    rotulo = "erro"
                    log.error("erro_reconciliar_venda", venda_id=str(venda_id), error=str(e))
                contagem[rotulo] = contagem.get(rotulo, 0) + 1

            log.info(
                "job_reconciliar_estoque_concluido",
                candidatos=len(candidatos),
                resultados=contagem
            )
        except Exception as e:
            log.error("job_reconciliar_estoque_erro", error=str(e))
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reconciliar_estoque_vendas())
