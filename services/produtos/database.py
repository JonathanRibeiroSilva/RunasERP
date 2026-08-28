"""
Configuração do banco de dados.
"""
import asyncio
import subprocess

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": "produtos,public"}}
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
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


async def init_db():
    """Applies pending Alembic migrations before the app serves traffic.

    Runs as a subprocess, not through alembic's Python API: alembic/env.py calls
    fileConfig(), which would replace the running app's logging configuration.
    A failure here kills startup on purpose — serving on a stale schema is worse
    than a container that restarts.
    """
    await asyncio.to_thread(
        subprocess.run, ["alembic", "upgrade", "head"], check=True
    )
