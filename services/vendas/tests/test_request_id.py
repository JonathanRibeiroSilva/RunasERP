"""
request_id no vendas (card 69): o id que o gateway manda em X-Correlation-Id entra
no contexto do log com empresa_id/usuario_id, e o 500 o devolve no corpo.

App mínimo com o middleware e o handler reais; não toca no banco.
"""
import asyncio
import re

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from structlog.contextvars import get_contextvars

import main
from request_context import contexto_requisicao

ID_GATEWAY = "gateway-id-0001"


def _get(caminho, headers=None):
    app = FastAPI()
    app.middleware("http")(contexto_requisicao)
    app.add_exception_handler(Exception, main.global_exception_handler)

    @app.get("/ok")
    async def ok():
        return get_contextvars()

    @app.get("/boom")
    async def boom():
        raise RuntimeError("falha de teste")

    async def chamar():
        transporte = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transporte, base_url="http://test") as c:
            return await c.get(caminho, headers=headers)

    return asyncio.run(chamar())


def test_contexto_do_log_vem_dos_headers_do_gateway():
    resposta = _get("/ok", {"x-correlation-id": ID_GATEWAY, "x-empresa-id": "7",
                            "x-usuario-id": "u-1"})

    assert resposta.json() == {"request_id": ID_GATEWAY, "empresa_id": "7", "usuario_id": "u-1"}
    assert resposta.headers["x-request-id"] == ID_GATEWAY


def test_sem_o_header_nasce_um_id_novo():
    resposta = _get("/ok")

    assert re.fullmatch(r"[0-9a-f]{32}", resposta.headers["x-request-id"])


def test_500_devolve_o_mesmo_id_do_gateway():
    resposta = _get("/boom", {"x-correlation-id": ID_GATEWAY})

    assert resposta.status_code == 500
    assert resposta.json()["request_id"] == ID_GATEWAY
    assert resposta.headers["x-request-id"] == ID_GATEWAY
