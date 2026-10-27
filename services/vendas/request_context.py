"""
Contexto de log da requisição: o mesmo request_id do gateway em todas as linhas.

O gateway gera o id e o manda em X-Correlation-Id (ver service_proxy.py); aqui ele
entra no contexto do structlog junto com empresa_id e usuario_id, que também vêm
dos headers do gateway. Sem o header (chamada direta, entre serviços) nasce um id novo.
"""
import re
import time
import uuid

import structlog
from fastapi import Request
from structlog.contextvars import bind_contextvars, clear_contextvars

log = structlog.get_logger()

# O header vem de dentro, mas a porta de um serviço já foi alcançável: filtra igual ao gateway.
ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

# O healthcheck do Docker bate aqui a cada poucos segundos; logar enche o disco de nada.
SEM_LOG = frozenset({"/health"})


def request_id_de(request: Request) -> str:
    """O id desta requisição; gera um se o middleware ainda não rodou."""
    return getattr(request.state, "request_id", None) or uuid.uuid4().hex


def acao_de(request: Request) -> str:
    """Rota casada, não a URL: `GET /vendas/{venda_id}` agrupa, `GET /vendas/42` não."""
    rota = request.scope.get("route")
    return f"{request.method} {getattr(rota, 'path', request.url.path)}"


async def contexto_requisicao(request: Request, call_next):
    """Amarra request_id/usuario_id/empresa_id ao log e mede duration_ms."""
    inicio = time.time()
    recebido = request.headers.get("x-correlation-id", "")
    request_id = recebido if ID_VALIDO.match(recebido) else uuid.uuid4().hex
    request.state.request_id = request_id

    # clear antes de bind: em teste (ASGITransport) as requisições dividem a task.
    clear_contextvars()
    bind_contextvars(
        request_id=request_id,
        usuario_id=request.headers.get("x-usuario-id"),
        empresa_id=request.headers.get("x-empresa-id"),
    )

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id

    if request.url.path not in SEM_LOG:
        log.info(
            "request.completed",
            method=request.method,
            path=request.url.path,
            action=acao_de(request),
            status_code=response.status_code,
            duration_ms=round((time.time() - inicio) * 1000, 2),
        )
    return response
