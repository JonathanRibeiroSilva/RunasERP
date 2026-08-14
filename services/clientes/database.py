"""
Configuração do banco de dados.
"""
import asyncio
import subprocess

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": "clientes,public"}}
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
    """Brings the schema to the Alembic head before the app serves traffic.

    Replaces the unconditional create_all(), which never altered an existing
    table — every schema change since the first deploy silently did not reach a
    running database.

    ponytail: this service's history starts at an ALTER, not a CREATE TABLE, so
    a fresh database cannot be replayed from it — it is built from the models
    and stamped instead. Squash the versions into a real baseline migration and
    this branch collapses into a plain `alembic upgrade head`.
    """
    async with engine.begin() as conn:
        managed = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table(
                "alembic_version", schema="clientes"
            )
        )
        if not managed:
            await conn.run_sync(Base.metadata.create_all)

    # Subprocess, not alembic's Python API: alembic/env.py calls fileConfig(),
    # which would replace the running app's logging configuration.
    await asyncio.to_thread(
        subprocess.run,
        ["alembic", "upgrade" if managed else "stamp", "head"],
        check=True,
    )
