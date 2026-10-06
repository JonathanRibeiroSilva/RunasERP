"""
Job de vencimento de lote (E4, Onda 6).

`LoteRepository.marcar_vencidos` existe desde antes deste plano e não tinha
nenhum chamador — um lote com `data_validade` passada ficava ATIVO para
sempre, sem nada o marcando VENCIDO. Este job fecha essa lacuna.

Cross-tenant de propósito: o job roda no lifespan do processo, sem contexto de
request — não há um `empresa_id` "do pedido" para usar. `empresas_com_lote_vencido`
faz uma única query sem filtro de tenant para achar quem tem lote vencido, e o
loop chama `marcar_vencidos` (tenant-scoped, como todo o resto do repository)
uma vez por empresa encontrada.

Cada empresa é commitada isoladamente: uma falha numa não derruba as outras
nem perde o que já foi marcado antes dela.
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

from config import settings
from repositories.estoque_repository import LoteRepository

log = structlog.get_logger()


async def marcar_lotes_vencidos():
    """Marca VENCIDO todo lote ATIVO com data_validade passada, em todas as empresas."""
    log.info("job_marcar_lotes_vencidos_iniciado")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            empresas = await LoteRepository.empresas_com_lote_vencido(session)
            await session.rollback()

            total_marcados = 0
            for empresa_id in empresas:
                try:
                    marcados = await LoteRepository.marcar_vencidos(session, empresa_id)
                    await session.commit()
                    total_marcados += marcados
                except Exception as e:
                    await session.rollback()
                    log.error(
                        "erro_marcar_lotes_vencidos_empresa",
                        empresa_id=empresa_id,
                        error=str(e)
                    )

            log.info(
                "job_marcar_lotes_vencidos_concluido",
                empresas=len(empresas),
                lotes_marcados=total_marcados
            )
        except Exception as e:
            log.error("job_marcar_lotes_vencidos_erro", error=str(e))
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(marcar_lotes_vencidos())
