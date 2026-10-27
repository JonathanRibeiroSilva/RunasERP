"""Regressão de auth do cliente, por requisição real (card 95).

Duas correções só tinham guard estático (regex sobre o código) ou nenhum teste:

- `POST /auth/cliente/registrar-interno` (G2, #91): segredo errado é 404, a rota
  se esconde. O 404 é proposital — não "corrija" para 403.
- `cliente_id` no JWT (39e0454): o login do cliente tem de emitir o token com ele,
  porque é por ele que o resto do sistema acha os dados do comprador.

Postgres de verdade (fixture `client`), como os demais testes do gateway: o commit
da rota vira savepoint e o rollback do fim limpa a conta criada.
"""
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from structlog.testing import capture_logs

from auth.jwt import verify_token
from auth.redis_client import get_redis
from config import settings
from main import app
from middleware.auditoria_middleware import AuditoriaMiddleware
from models.cliente_auth import ClienteAuth
from repositories.cliente_auth_repository import ClienteAuthRepository
from routers import auth_cliente

HEADER = "X-Registro-Interno-Token"
SEGREDO = "segredo-do-registro-interno-so-de-teste"


@pytest.fixture(autouse=True)
def _sem_auditoria(monkeypatch):
    """A trilha grava em sessão própria, fora do rollback do teste: sem isto cada
    run deixaria linhas em gateway.auditoria. Não é o que se prova aqui."""
    async def _nada(*_args, **_kwargs):
        pass

    monkeypatch.setattr(AuditoriaMiddleware, "_gravar", _nada)


def _corpo() -> dict:
    return {
        "email": f"{uuid4().hex}@exemplo.com",
        "senha_hash": "hash-irrelevante-para-esta-regra",
        "cliente_id": str(uuid4()),
        "empresa_id": 1,
    }


async def _conta_existe(db, email: str) -> bool:
    return await ClienteAuthRepository(db).buscar_por_email(email) is not None


@pytest.mark.asyncio
async def test_registrar_interno_com_segredo_errado_da_404_e_nao_cria_conta(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REGISTRO_INTERNO_TOKEN", SEGREDO)
    corpo = _corpo()

    resp = await client.post("/auth/cliente/registrar-interno", json=corpo, headers={HEADER: "errado"})

    assert resp.status_code == 404
    assert not await _conta_existe(db, corpo["email"])


@pytest.mark.asyncio
async def test_registrar_interno_com_segredo_certo_cria_a_conta(client, db, monkeypatch):
    monkeypatch.setattr(settings, "REGISTRO_INTERNO_TOKEN", SEGREDO)
    corpo = _corpo()

    resp = await client.post("/auth/cliente/registrar-interno", json=corpo, headers={HEADER: SEGREDO})

    assert resp.status_code == 201
    assert resp.json()["cliente_id"] == corpo["cliente_id"]
    conta = (await db.execute(
        select(ClienteAuth).where(ClienteAuth.cliente_id == UUID(corpo["cliente_id"]))
    )).scalar_one()
    assert conta.email == corpo["email"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "segredo_do_gateway, headers",
    [
        ("", {}),          # a env nova ainda não chegou ao gateway
        (SEGREDO, {}),     # o vendas ainda não carimba o header
    ],
)
async def test_registrar_interno_sem_segredo_passa_enquanto_o_fail_open_existir(
    client, db, monkeypatch, segredo_do_gateway, headers
):
    """Documenta o fail-open de propósito (card 03): passa e loga.

    Quando o card 03 fechar a janela, estes dois casos passam a dar 404 e este
    teste deve ser invertido — a falha aqui é o aviso, não um bug.
    """
    monkeypatch.setattr(settings, "REGISTRO_INTERNO_TOKEN", segredo_do_gateway)
    corpo = _corpo()

    with capture_logs() as logs:
        resp = await client.post("/auth/cliente/registrar-interno", json=corpo, headers=headers)

    assert resp.status_code == 201
    assert await _conta_existe(db, corpo["email"])
    # É o log que o card 03 mede para decidir quando fechar o fail-open.
    assert any(l["event"] == "cliente.internal_register.sem_segredo" for l in logs)


class _RedisFake:
    async def setex(self, chave, ttl, valor):
        pass


@pytest.mark.asyncio
async def test_login_do_cliente_emite_token_com_cliente_id(client, db, monkeypatch):
    cliente_id = uuid4()
    senha = "senha-so-de-teste-123"
    conta = await ClienteAuthRepository(db).criar(
        email=f"{uuid4().hex}@exemplo.com", senha=senha, cliente_id=cliente_id, empresa_id=1
    )

    async def _cliente_fake(_cliente_id, _empresa_id):
        return {"id": str(cliente_id), "nome": "Comprador de Teste"}

    # O serviço de clientes não sobe no leg do gateway; o que se prova aqui é o
    # token que o gateway emite.
    monkeypatch.setattr(auth_cliente, "_fetch_cliente", _cliente_fake)
    app.dependency_overrides[get_redis] = _RedisFake  # o fixture `client` limpa no fim

    resp = await client.post(
        "/auth/cliente/login", data={"username": conta.email, "password": senha}
    )

    assert resp.status_code == 200
    payload = verify_token(resp.json()["access_token"])
    assert payload["cliente_id"] == str(cliente_id)
    assert payload["sub"] == str(conta.id)
    assert payload["user_type"] == "cliente"
