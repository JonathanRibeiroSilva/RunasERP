"""
Configuração do banco de dados.
"""
import asyncio
import subprocess
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": "vendas,public"}}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Classe base para os modelos."""
    pass


async def get_db() -> AsyncSession:
    """Dependency para obter sessão do banco de dados."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Applies pending Alembic migrations before the app serves traffic.

    Replaces create_all(), which never altered an existing table — every schema
    change since the first deploy silently did not reach a running database.

    Runs as a subprocess, not through alembic's Python API: alembic/env.py calls
    fileConfig(), which would replace the running app's logging configuration.
    """
    # `alembic upgrade head` sai 0 quando não acha revision nenhuma — o mesmo
    # código de "já está no head". Sem esta guarda, uma imagem construída sem as
    # migrations sobe healthy com o schema vazio (o incidente que ensinou isso
    # está em services/empresas/database.py).
    if not [p for p in Path("alembic/versions").glob("*.py") if p.name != "__init__.py"]:
        raise RuntimeError(
            "alembic/versions/ sem revisions: a imagem foi construída sem as "
            "migrations (verifique o .dockerignore deste serviço)"
        )
    await asyncio.to_thread(
        subprocess.run, ["alembic", "upgrade", "head"], check=True
    )
