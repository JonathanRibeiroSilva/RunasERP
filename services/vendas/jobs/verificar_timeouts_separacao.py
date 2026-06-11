"""
Job para verificar timeouts de separação de vendas.
- Alerta em 12h (aviso para separar)
- Alerta em 24h (aviso crítico)
- Auto-cancelamento em 48h (timeout final)

Deve rodar a cada 1 hora via cron ou scheduler.
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
from models.venda import Venda, StatusVenda
from services.historico_status_service import HistoricoStatusService
from services.notificacao_service import NotificacaoService
from repositories.venda_repository import VendaRepository

log = structlog.get_logger()


async def verificar_timeouts():
    """
    Verifica timeouts de separação de vendas CONFIRMADAS.
    
    Fluxo:
    - 12h: Alerta para separação (log + notificação interna)
    - 24h: Alerta crítico (log + notificação interna)
    - 48h: Auto-cancelamento (muda status para CANCELADA)
    """
    log.info("job_verificar_timeouts_iniciado")
    
    # Criar engine e sessão
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            agora = datetime.utcnow()
            
            # 1. Buscar vendas CONFIRMADAS
            query = select(Venda).where(
                and_(
                    Venda.status == StatusVenda.CONFIRMADA.value,
                    Venda.data_confirmacao.isnot(None)
                )
            )
            
            result = await session.execute(query)
            vendas = result.scalars().all()
            
            alertas_12h = 0
            alertas_24h = 0
            canceladas_48h = 0
            
            for venda in vendas:
                tempo_decorrido = agora - venda.data_confirmacao
                horas_decorridas = tempo_decorrido.total_seconds() / 3600
                
                # 2. TIMEOUT 48h - Auto-cancelamento
                if horas_decorridas >= 48:
                    try:
                        # Cancelar venda
                        await VendaRepository.atualizar(
                            session,
                            venda.empresa_id,
                            venda.id,
                            status=StatusVenda.CANCELADA.value,
                            data_cancelada=agora,
                            motivo_cancelamento="Cancelamento automático: timeout de 48h para separação"
                        )
                        
                        # Registrar histórico
                        await HistoricoStatusService.registrar_mudanca(
                            session,
                            venda.id,
                            StatusVenda.CONFIRMADA.value,
                            StatusVenda.CANCELADA.value,
                            None,  # Sistema
                            "Cancelamento automático por timeout de 48h"
                        )
                        
                        await session.commit()
                        
                        canceladas_48h += 1
                        
                        log.warning(
                            "venda_cancelada_timeout_48h",
                            venda_id=str(venda.id),
                            numero_venda=venda.numero_venda,
                            empresa_id=venda.empresa_id,
                            horas_decorridas=horas_decorridas
                        )
                        
                        # Enviar notificação ao cliente (se tiver telefone)
                        if venda.cliente_convidado_telefone:
                            try:
                                await NotificacaoService.enviar_pedido_cancelado(
                                    venda.cliente_convidado_telefone,
                                    venda.numero_venda,
                                    "Timeout de separação (48h)"
                                )
                            except Exception as e:
                                log.warning(
                                    "erro_enviar_notificacao_cancelamento",
                                    venda_id=str(venda.id),
                                    error=str(e)
                                )
                        
                    except Exception as e:
                        await session.rollback()
                        log.error(
                            "erro_cancelar_venda_timeout",
                            venda_id=str(venda.id),
                            error=str(e)
                        )
                
                # 3. ALERTA 24h - Crítico
                elif horas_decorridas >= 24:
                    alertas_24h += 1
                    
                    log.warning(
                        "alerta_separacao_24h",
                        venda_id=str(venda.id),
                        numero_venda=venda.numero_venda,
                        empresa_id=venda.empresa_id,
                        horas_decorridas=horas_decorridas,
                        tempo_restante_horas=48 - horas_decorridas
                    )
                    
                    # TODO: Enviar notificação interna para admin/lojista
                    # (implementar quando tiver sistema de notificações internas)
                
                # 4. ALERTA 12h - Aviso
                elif horas_decorridas >= 12:
                    alertas_12h += 1
                    
                    log.info(
                        "alerta_separacao_12h",
                        venda_id=str(venda.id),
                        numero_venda=venda.numero_venda,
                        empresa_id=venda.empresa_id,
                        horas_decorridas=horas_decorridas
                    )
            
            log.info(
                "job_verificar_timeouts_concluido",
                vendas_verificadas=len(vendas),
                alertas_12h=alertas_12h,
                alertas_24h=alertas_24h,
                canceladas_48h=canceladas_48h
            )
            
        except Exception as e:
            log.error(
                "job_verificar_timeouts_erro",
                error=str(e)
            )
        finally:
            await engine.dispose()


if __name__ == "__main__":
    """
    Executar:
    python jobs/verificar_timeouts_separacao.py
    
    Configurar cron (Linux) - a cada 1 hora:
    0 * * * * cd /path/to/vendas-service && python jobs/verificar_timeouts_separacao.py
    
    Configurar Task Scheduler (Windows):
    - Trigger: A cada 1 hora
    - Action: python.exe jobs/verificar_timeouts_separacao.py
    """
    asyncio.run(verificar_timeouts())
