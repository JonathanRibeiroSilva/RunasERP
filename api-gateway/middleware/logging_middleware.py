"""
Middleware de logging estruturado e de correlação.

Gera (ou repassa) o X-Request-Id, amarra request_id/usuario_id/empresa_id ao
contexto do structlog — toda linha de log da requisição sai com eles — e devolve
o id no header da resposta. Fica por fora de todos os outros (ver main.py), para
que até o 402 da inadimplência e o 429 do rate limit saiam com id.
"""
import re
import time
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from middleware.auditoria_middleware import AuditoriaMiddleware


log = structlog.get_logger()

# O id vem de fora: sem o filtro, um header com quebra de linha ou 10KB entraria
# no log. O X-Request-Id do Mercado Pago (UUID) passa.
ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def request_id_de(request: Request) -> str:
    """O id desta requisição; gera um se o middleware ainda não rodou."""
    return getattr(request.state, "request_id", None) or uuid.uuid4().hex


def acao_de(request: Request) -> str:
    """Rota casada, não a URL: `GET /vendas/{venda_id}` agrupa, `GET /vendas/42` não."""
    rota = request.scope.get("route")
    return f"{request.method} {getattr(rota, 'path', request.url.path)}"


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para log estruturado de todas as requisições."""

    async def dispatch(self, request: Request, call_next):
        """Processa a requisição e loga."""
        start_time = time.time()

        recebido = request.headers.get("x-request-id", "")
        request_id = recebido if ID_VALIDO.match(recebido) else uuid.uuid4().hex
        request.state.request_id = request_id
        usuario_id, empresa_id = AuditoriaMiddleware._identificar(request)

        # clear antes de bind: em teste (ASGITransport) todas as requisições
        # dividem a mesma task, e o contexto da anterior vazaria para esta.
        clear_contextvars()
        bind_contextvars(request_id=request_id, usuario_id=usuario_id, empresa_id=empresa_id)

        log.info(
            "request.started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        )

        response = await call_next(request)

        duration = time.time() - start_time
        log.info(
            "request.completed",
            method=request.method,
            path=request.url.path,
            action=acao_de(request),
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )

        response.headers["X-Request-Id"] = request_id
        return response
