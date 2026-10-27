"""
Tokens JWT do gateway: ida e volta, expiração, assinatura, e compatibilidade com
os tokens que o python-jose (removido, CVE-2026-85394 sem correção) já emitiu.

Teste puro de lógica — sem banco, sem Redis. A compatibilidade importa porque o
deploy não desloga ninguém: access/refresh em circulação foram assinados pelo
jose e têm de continuar validando no PyJWT.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt

# As settings do gateway exigem estas variáveis no import.
os.environ.setdefault("SECRET_KEY", "test-secret-key-super-secure-min-32-chars")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
for _servico in ("EMPRESAS", "CLIENTES", "PRODUTOS", "ESTOQUE", "VENDAS",
                 "FINANCEIRO", "NOTIFICACOES"):
    os.environ.setdefault(f"{_servico}_URL", f"http://{_servico.lower()}:8000")

from auth.jwt import create_access_token, create_refresh_token, verify_token  # noqa: E402
from config import settings  # noqa: E402

# Gerado por python-jose 3.5.0, HS256, com esta chave (a SECRET_KEY do ambiente
# varia: a CI define a sua, por isso o teste a fixa).
CHAVE_DO_TOKEN_JOSE = "test-secret-key-super-secure-min-32-chars"
# exp em 2100 (não expira); iat 2023-11-14.
TOKEN_EMITIDO_PELO_JOSE = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMTExMTExMS0xMTExLTExMTEtMTExMS0xMTExMTExMTExMTEiLCJyb2xlIjoiQURNSU4i"
    "LCJ1c2VyX3R5cGUiOiJ1c3VhcmlvIiwiZXhwIjo0MTAyNDQ0ODAwLCJpYXQiOjE3MDAwMDAwMDB9."
    "5gxBVfT3m_PJLc2nPbXhzNRQV_GttMcXhyPeFBNPN0M"
)


def test_access_token_ida_e_volta():
    uid = uuid.uuid4()
    payload = verify_token(create_access_token(uid, "ADMIN"))
    assert payload["sub"] == str(uid)
    assert payload["role"] == "ADMIN"
    assert payload["user_type"] == "usuario"


def test_access_token_carrega_cliente_id_quando_recebe():
    """O token do cliente leva `cliente_id` (39e0454); o de usuário não ganha o claim."""
    uid, cid = uuid.uuid4(), uuid.uuid4()
    do_cliente = verify_token(
        create_access_token(uid, "CLIENTE", "cliente", empresa_id=1, cliente_id=cid)
    )
    assert do_cliente["cliente_id"] == str(cid)
    assert "cliente_id" not in verify_token(create_access_token(uid, "ADMIN"))


def test_refresh_token_ida_e_volta():
    uid = uuid.uuid4()
    payload = verify_token(create_refresh_token(uid))
    assert payload["sub"] == str(uid)
    assert payload["type"] == "refresh"


def test_iat_nao_fica_no_futuro():
    """O PyJWT rejeita iat futuro; utcnow().timestamp() o empurrava em fuso != UTC."""
    agora = datetime.now(timezone.utc).timestamp()
    iat = verify_token(create_access_token(uuid.uuid4(), "ADMIN"))["iat"]
    assert abs(iat - agora) < 5


def test_token_do_jose_continua_valido(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", CHAVE_DO_TOKEN_JOSE)
    payload = verify_token(TOKEN_EMITIDO_PELO_JOSE)
    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert payload["role"] == "ADMIN"


def test_token_expirado_vira_none():
    expirado = jwt.encode(
        {"sub": "x", "exp": int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp())},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    assert verify_token(expirado) is None


def test_assinatura_errada_vira_none():
    forjado = jwt.encode({"sub": "x"}, "outra-chave-qualquer-com-32-bytes-ou-mais", algorithm="HS256")
    assert verify_token(forjado) is None


def test_alg_none_e_lixo_viram_none():
    sem_assinatura = jwt.encode({"sub": "x"}, None, algorithm="none")
    assert verify_token(sem_assinatura) is None
    assert verify_token("nao-e-um-jwt") is None
