"""
Logout revoga o access token: grava `blacklist:{token}` até o `exp`, e o
get_current_user recusa o token gravado. Sem Redis nem banco — dublês bastam,
porque a recusa acontece antes de qualquer consulta ao usuário.
"""
import asyncio
import os
import uuid

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

# As settings do gateway exigem estas variáveis no import.
os.environ.setdefault("SECRET_KEY", "test-secret-key-super-secure-min-32-chars")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
for _servico in ("EMPRESAS", "CLIENTES", "PRODUTOS", "ESTOQUE", "VENDAS",
                 "FINANCEIRO", "NOTIFICACOES"):
    os.environ.setdefault(f"{_servico}_URL", f"http://{_servico.lower()}:8000")

from auth.jwt import create_access_token  # noqa: E402
from auth.oauth2 import get_current_user  # noqa: E402
from config import settings  # noqa: E402
from routers.auth import logout  # noqa: E402


class RedisFake:
    def __init__(self):
        self.dados = {}
        self.ttls = {}

    async def set(self, chave, valor, ex=None):
        self.dados[chave] = valor
        self.ttls[chave] = ex

    async def get(self, chave):
        return self.dados.get(chave)

    async def delete(self, chave):
        self.dados.pop(chave, None)


class UsuarioFake:
    id = uuid.uuid4()


def request_vazio():
    return Request({"type": "http", "headers": [], "query_string": b""})


def test_logout_grava_blacklist_com_ttl_do_que_falta():
    redis, token = RedisFake(), create_access_token(UsuarioFake.id, "ADMIN")

    asyncio.run(logout(Response(), UsuarioFake, redis, token))

    ttl = redis.ttls[f"blacklist:{token}"]
    assert 0 < ttl <= settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_token_depois_do_logout_da_401():
    redis, token = RedisFake(), create_access_token(UsuarioFake.id, "ADMIN")
    asyncio.run(logout(Response(), UsuarioFake, redis, token))

    with pytest.raises(HTTPException) as erro:
        asyncio.run(get_current_user(request_vazio(), token, None, redis))

    assert erro.value.status_code == 401
