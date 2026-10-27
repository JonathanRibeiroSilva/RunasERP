"""
request_id de ponta a ponta no gateway (card 69).

O que precisa valer para um 500 em produção ser rastreável: o id existe em toda
resposta, o 500 o devolve no corpo, o contexto do log o carrega, e os serviços o
recebem sem o cliente poder forjá-lo. Sem banco nem Redis — app mínimo com o
middleware e o handler reais, e o proxy com httpx trocado por dublê.
"""
import asyncio
import os
import re

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from structlog.contextvars import get_contextvars

# As settings do gateway exigem estas variáveis no import.
os.environ.setdefault("SECRET_KEY", "test-secret-key-super-secure-min-32-chars")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
for _servico in ("EMPRESAS", "CLIENTES", "PRODUTOS", "ESTOQUE", "VENDAS",
                 "FINANCEIRO", "NOTIFICACOES"):
    os.environ.setdefault(f"{_servico}_URL", f"http://{_servico.lower()}:8000")

import main  # noqa: E402
from middleware.logging_middleware import LoggingMiddleware  # noqa: E402
from proxy import service_proxy  # noqa: E402

ID_MP = "a1b2c3d4-0000-4000-8000-123456789abc"


def _app():
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    app.add_exception_handler(Exception, main.global_exception_handler)

    @app.get("/ok/{item}")
    async def ok(item: str):
        return get_contextvars()

    @app.get("/boom")
    async def boom():
        raise RuntimeError("falha de teste")

    return app


def _get(caminho, headers=None):
    async def chamar():
        # raise_app_exceptions=False: o 500 sai como resposta, como em produção.
        transporte = ASGITransport(app=_app(), raise_app_exceptions=False)
        async with AsyncClient(transport=transporte, base_url="http://test") as c:
            return await c.get(caminho, headers=headers)

    return asyncio.run(chamar())


def test_gera_id_quando_o_cliente_nao_manda():
    resposta = _get("/ok/1")

    assert re.fullmatch(r"[0-9a-f]{32}", resposta.headers["x-request-id"])


def test_repassa_id_valido_e_descarta_o_suspeito():
    assert _get("/ok/1", {"x-request-id": ID_MP}).headers["x-request-id"] == ID_MP

    suspeito = _get("/ok/1", {"x-request-id": "curto"}).headers["x-request-id"]
    assert suspeito != "curto"


def test_contexto_do_log_carrega_o_id():
    resposta = _get("/ok/1", {"x-request-id": ID_MP})

    assert resposta.json()["request_id"] == ID_MP


def test_500_devolve_o_id_no_corpo_e_no_header():
    resposta = _get("/boom", {"x-request-id": ID_MP})

    assert resposta.status_code == 500
    assert resposta.json()["request_id"] == ID_MP
    assert resposta.headers["x-request-id"] == ID_MP
    assert "falha de teste" not in resposta.text  # a exceção não vaza para o cliente


def test_acao_usa_o_template_da_rota():
    from middleware.logging_middleware import acao_de

    rota = type("Rota", (), {"path": "/vendas/{venda_id}"})()
    request = Request({"type": "http", "method": "GET", "path": "/vendas/42",
                       "headers": [], "route": rota})

    assert acao_de(request) == "GET /vendas/{venda_id}"


class _ClienteFake:
    chamadas: list[dict] = []

    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, **kwargs):
        type(self).chamadas.append(kwargs)
        return type("R", (), {"status_code": 200, "content": b"{}",
                              "headers": {"content-type": "application/json"}})()


class _Usuario:
    id = "11111111-1111-1111-1111-111111111111"
    empresa_id = 7
    cliente_id = None


def _encaminhar(headers, request_id="gateway-id-0001"):
    scope = {"type": "http", "method": "GET", "path": "/vendas", "query_string": b"",
             "headers": [(k.encode(), v.encode()) for k, v in headers.items()]}
    request = Request(scope)
    request.state.request_id = request_id
    asyncio.run(service_proxy.ServiceProxy.proxy_request(request, "/vendas", _Usuario))
    return _ClienteFake.chamadas[-1]["headers"]


@pytest.fixture(autouse=True)
def _httpx_fake(monkeypatch):
    _ClienteFake.chamadas = []
    monkeypatch.setattr(service_proxy.httpx, "AsyncClient", _ClienteFake)


def test_proxy_manda_o_id_e_o_usuario_aos_servicos():
    headers = _encaminhar({})

    assert headers["X-Correlation-Id"] == "gateway-id-0001"
    assert headers["X-Usuario-Id"] == _Usuario.id


def test_proxy_nao_aceita_id_nem_usuario_forjados_pelo_cliente():
    headers = _encaminhar({"x-correlation-id": "forjado", "x-usuario-id": "forjado"})

    assert headers["X-Correlation-Id"] == "gateway-id-0001"
    assert headers["X-Usuario-Id"] == _Usuario.id
    assert "x-correlation-id" not in headers and "x-usuario-id" not in headers


def test_proxy_nao_toca_no_x_request_id_da_assinatura_da_mp():
    """O manifesto do webhook da MP assina o x-request-id dela: tem de chegar intacto."""
    assert _encaminhar({"x-request-id": ID_MP})["x-request-id"] == ID_MP
