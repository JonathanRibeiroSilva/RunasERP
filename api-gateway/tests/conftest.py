"""Fixtures dos testes do gateway: Postgres de verdade, schema das migrations.

Mesmo desenho dos conftest dos serviços (services/*/tests/conftest.py): nada de
create_all, o schema é o que `alembic upgrade head` construiu antes do pytest.
A diferença é o que as settings do gateway exigem no import — as URLs de todos
os serviços que ele encaminha.
"""
import os

# Os defaults apontam para o docker-compose dev publicado no host; a CI define os
# seus. Redis no db 15, o mesmo que test_idempotencia_redis.py já usa.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://erp:erp@localhost:5432/erp")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("SECRET_KEY", "test-secret-key-super-secure-min-32-chars")
for _servico, _porta in (("CLIENTES", 8001), ("PRODUTOS", 8002), ("ESTOQUE", 8003),
                         ("VENDAS", 8004), ("FINANCEIRO", 8005), ("NOTIFICACOES", 8006),
                         ("EMPRESAS", 8007)):
    os.environ.setdefault(f"{_servico}_URL", f"http://localhost:{_porta}")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from database import engine, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest_asyncio.fixture
async def db():
    """Sessão presa numa transação que nunca é commitada de verdade.

    O commit() do código sob teste vira RELEASE SAVEPOINT (join_transaction_mode),
    e o rollback no fim desfaz tudo: cada teste parte do schema limpo. O dispose
    devolve o pool — o pytest-asyncio abre um event loop por teste.
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
    """O app inteiro via ASGI, sem subir servidor, na sessão do teste."""
    async def _db():
        yield db

    app.dependency_overrides[get_db] = _db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()
