"""Fixtures dos testes deste serviço: Postgres de verdade, schema das migrations.

Não há create_all aqui. O schema é o que `alembic upgrade head` construiu antes
do pytest — na CI, a partir de um banco vazio; local, o boot do docker-compose
dev já rodou. Testar contra create_all seria testar os models contra eles
mesmos, e é exatamente assim que prod divergiu das migrations sem ninguém ver.

SQLite saiu: não tem SELECT ... FOR UPDATE, e parte do que estes testes guardam
é concorrência.
"""
import os

# As settings exigem estas variáveis no import. Os defaults apontam para o
# Postgres e o Redis do docker-compose dev, que ficam publicados no host; a CI
# define as suas. Redis no db 15 para nunca encostar no db 0 do dev.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://erp:erp@localhost:5432/erp")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("SECRET_KEY", "test-secret-key-super-secure-min-32-chars")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from database import engine, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest_asyncio.fixture
async def db():
    """Sessão presa numa transação que nunca é commitada de verdade.

    O commit() do código sob teste vira RELEASE SAVEPOINT (join_transaction_mode),
    e o rollback no fim desfaz tudo: cada teste parte do schema limpo.

    Usa o engine do próprio serviço, não um criado aqui: é ele que carrega o
    search_path do schema. O dispose no fim devolve o pool — o pytest-asyncio
    abre um event loop por teste, e conexão asyncpg de um loop não serve no outro.
    """
    async with engine.connect() as conexao:
        transacao = await conexao.begin()
        sessao = AsyncSession(
            bind=conexao, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield sessao
        finally:
            await sessao.close()
            await transacao.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db):
    """O app inteiro via ASGI, sem subir servidor, na sessão do teste.

    ASGITransport não dispara o lifespan: o init_db (alembic no boot) não roda
    aqui, o schema já foi construído antes.
    """
    async def _db():
        yield db

    app.dependency_overrides[get_db] = _db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()
