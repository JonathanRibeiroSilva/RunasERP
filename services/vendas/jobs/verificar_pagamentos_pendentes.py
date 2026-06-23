"""
Job para verificar pagamentos online pendentes.
- Timeout Mercado Pago: 5 minutos
- Se expirar sem pagamento, cancela venda e libera estoque

Deve rodar a cada 5 minutos via cron ou scheduler.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
import structlog

from config import settings
from models.venda import Venda, StatusVenda, StatusReserva
from services.historico_status_service import HistoricoStatusService
from services.notificacao_service import NotificacaoService
from repositories.venda_repository import VendaRepository
from repositories.venda_repository import ReservaEstoqueVendaRepository
from services.venda_service import VendaService

log = structlog.get_logger()


async def verificar_pagamentos_pendentes():
    """
    Verifica vendas com status PENDENTE_PAGAMENTO e cancela se expirou (5min).
    
    Fluxo:
    1. Busca vendas PENDENTE_PAGAMENTO
    2. Verifica se passaram 5min desde data_pedido
    3. Se sim: cancela venda, libera reservas, notifica cliente
    """
    log.info("job_verificar_pagamentos_pendentes_iniciado")
    
    # Criar engine e sessão
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            agora = datetime.utcnow()
            timeout = timedelta(minutes=5)
            
            # 1. Buscar vendas PENDENTE_PAGAMENTO
            query = select(Venda).where(
                and_(
                    Venda.status == StatusVenda.PENDENTE_PAGAMENTO.value,
                    Venda.data_pedido.isnot(None),
                    # Apenas vendas com preferência Mercado Pago (pagamento online)
                    Venda.mercadopago_preference_id.isnot(None)
                )
            )
            
            result = await session.execute(query)
            vendas = result.scalars().all()
            
            canceladas = 0
            
            for venda in vendas:
                tempo_decorrido = agora - venda.data_pedido
                
                # 2. Verificar se expirou (>5min)
                if tempo_decorrido > timeout:
                    try:
                        # 3. Buscar venda completa com relacionamentos
                        venda_completa = await VendaRepository.buscar_por_id(
                            session,
                            venda.empresa_id,
                            venda.id,
                            com_relacionamentos=True
                        )
                        
                        # 4. Liberar reservas de estoque
                        for item in venda_completa.itens:
                            if item.estoque_reservado and not item.estoque_baixado:
                                sucesso = await VendaService.liberar_reserva_estoque(
                                    venda.empresa_id,
                                    item.produto_id,
                                    item.variante_id,
                                    item.quantidade,
                                    venda.numero_venda
                                )
                                
                                if not sucesso:
                                    log.warning(
                                        "falha_liberar_reserva_timeout_pagamento",
                                        produto_id=str(item.produto_id),
                                        venda_id=str(venda.id)
                                    )
                        
                        # 5. Atualizar reservas no banco
                        reservas = await ReservaEstoqueVendaRepository.listar_por_venda(
                            session,
                            venda.id
                        )
                        
                        for reserva in reservas:
                            if reserva.status == StatusReserva.RESERVADA.value:
                                await ReservaEstoqueVendaRepository.atualizar(
                                    session,
                                    reserva.id,
                                    status=StatusReserva.LIBERADA.value,
                                    liberada_em=agora
                                )
                        
                        # 6. Cancelar venda
                        await VendaRepository.atualizar(
                            session,
                            venda.empresa_id,
                            venda.id,
                            status=StatusVenda.CANCELADA.value,
                            data_cancelada=agora,
                            motivo_cancelamento="Cancelamento automático: timeout de pagamento (5min)"
                        )
                        
                        # 7. Registrar histórico
                        await HistoricoStatusService.registrar_mudanca(
                            session,
                            venda.id,
                            StatusVenda.PENDENTE_PAGAMENTO.value,
                            StatusVenda.CANCELADA.value,
                            None,  # Sistema
                            "Cancelamento automático por timeout de pagamento (5min)"
                        )
                        
                        await session.commit()
                        
                        canceladas += 1
                        
                        log.warning(
                            "venda_cancelada_timeout_pagamento",
                            venda_id=str(venda.id),
                            numero_venda=venda.numero_venda,
                            empresa_id=venda.empresa_id,
                            minutos_decorridos=tempo_decorrido.total_seconds() / 60
                        )
                        
                        # 8. Enviar notificação ao cliente (se tiver telefone)
                        telefone = None
                        if venda.cliente_convidado_telefone:
                            telefone = venda.cliente_convidado_telefone
                        
                        if telefone:
                            try:
                                await NotificacaoService.enviar_pedido_cancelado(
                                    telefone,
                                    venda.numero_venda,
                                    "Timeout de pagamento (5min)"
                                )
                            except Exception as e:
                                log.warning(
                                    "erro_enviar_notificacao_cancelamento_pagamento",
                                    venda_id=str(venda.id),
                                    error=str(e)
                                )
                    
                    except Exception as e:
                        await session.rollback()
                        log.error(
                            "erro_cancelar_venda_timeout_pagamento",
                            venda_id=str(venda.id),
                            error=str(e)
                        )
            
            log.info(
                "job_verificar_pagamentos_pendentes_concluido",
                vendas_verificadas=len(vendas),
                vendas_canceladas=canceladas
            )
            
        except Exception as e:
            log.error(
                "job_verificar_pagamentos_pendentes_erro",
                error=str(e)
            )
        finally:
            await engine.dispose()


if __name__ == "__main__":
    """
    Executar:
    python jobs/verificar_pagamentos_pendentes.py
    
    Configurar cron (Linux) - a cada 5 minutos:
    */5 * * * * cd /path/to/vendas-service && python jobs/verificar_pagamentos_pendentes.py
    
    Configurar Task Scheduler (Windows):
    - Trigger: A cada 5 minutos
    - Action: python.exe jobs/verificar_pagamentos_pendentes.py
    """
    asyncio.run(verificar_pagamentos_pendentes())
