"""
Job para limpar reservas temporárias expiradas.
Deve rodar a cada 1 minuto via cron ou scheduler.
"""
import asyncio
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

from config import settings
from services.reserva_temporaria_service import ReservaTemporariaService

log = structlog.get_logger()


async def limpar_reservas_expiradas():
    """
    Limpa reservas temporárias expiradas do banco de dados.
    """
    log.info("job_limpar_reservas_iniciado")
    
    # Criar engine e sessão
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Limpar reservas expiradas
            count = await ReservaTemporariaService.limpar_expiradas(session)
            
            log.info(
                "job_limpar_reservas_concluido",
                reservas_removidas=count
            )
            
        except Exception as e:
            log.error(
                "job_limpar_reservas_erro",
                error=str(e)
            )
        finally:
            await engine.dispose()


if __name__ == "__main__":
    """
    Executar:
    python jobs/limpar_reservas.py
    
    Configurar cron (Linux):
    * * * * * cd /path/to/vendas-service && python jobs/limpar_reservas.py
    
    Configurar Task Scheduler (Windows):
    - Trigger: A cada 1 minuto
    - Action: python.exe jobs/limpar_reservas.py
    """
    asyncio.run(limpar_reservas_expiradas())
