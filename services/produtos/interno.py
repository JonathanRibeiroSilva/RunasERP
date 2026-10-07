"""
Os dois lados do contrato de origem interna: validar o que chega, carimbar o que sai.

Os serviços tratam X-Empresa-Id e X-Cliente-Id como identidade. Quem alcançasse a
porta de um serviço direto escolhia o tenant que quisesse — o gateway era a única
coisa entre a internet e esses headers, e ele não deixava rastro nenhum no pedido
que encaminhava. Aqui está o rastro: um segredo compartilhado, o mesmo nos 8
containers, no header X-Servico-Interno-Token.

ponytail: token estático, não claim assinado. Ele responde "veio de dentro" e nada
mais — não diz QUAL serviço chamou nem expira. É o mesmo desenho de
PLATAFORMA_JOB_TOKEN e REGISTRO_INTERNO_TOKEN, que já rodam em prod. Se algum dia
a autorização precisar depender de quem é o chamador, aí sim vale um claim
assinado com SECRET_KEY — que 6 dos 7 serviços ainda nem têm.
"""
import secrets

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse

from config import settings

log = structlog.get_logger()

HEADER = "X-Servico-Interno-Token"

# /health é o único caminho que chega sem passar pelo gateway: o healthcheck do
# Docker bate em localhost:PORTA/health (docker-compose.prod.yml). Fechar aqui
# marca o container unhealthy e o Coolify derruba o stack.
ISENTOS = frozenset({"/health"})


def auth_interno(headers: dict[str, str] | None = None) -> dict[str, str]:
    """
    Devolve os headers com a prova de origem interna. **Só para destino interno.**

    Deliberadamente opt-in, uma chamada por vez: estes serviços também falam com
    Mercado Pago, viacep e Evolution API, e mandar o segredo interno para terceiro
    é vazar credencial. Um hook global no httpx seria menos código e carimbaria
    exatamente esses três.
    """
    headers = dict(headers or {})
    # Vazio = fail-open: o validador do outro lado loga e deixa passar.
    if settings.SERVICO_INTERNO_TOKEN:
        headers[HEADER] = settings.SERVICO_INTERNO_TOKEN
    return headers


async def validar_token_interno(request: Request, call_next):
    """Recusa a requisição que não provar que veio de dentro da malha."""
    if request.url.path in ISENTOS:
        return await call_next(request)

    esperado = settings.SERVICO_INTERNO_TOKEN
    recebido = request.headers.get(HEADER.lower())

    # Fail-closed desde 2026-10-04: servico_interno.ausente ficou em zero com
    # tráfego real (checkout completo, cancelamento, baixa de estoque) depois
    # do segredo confirmado nos 8 containers em prod — ver PR #107/#108 e o
    # plano de ação. financeiro e notificacoes fecharam depois, sem medição
    # (só têm /health, isento) — ver o interno.py deles.
    if not esperado or not recebido:
        log.warning("servico_interno.ausente", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Forbidden"},
        )

    # encode(): compare_digest recusa str não-ASCII com TypeError, e o header vem
    # de fora — um byte acentuado viraria 500 em vez de 403.
    if not secrets.compare_digest(recebido.encode(), esperado.encode()):
        log.warning("servico_interno.invalido", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Forbidden"},
        )

    return await call_next(request)
