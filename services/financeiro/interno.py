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

    # ponytail: fail-open enquanto o segredo não estiver nos 8 containers em
    # prod. O deploy não é blue-green — o stack velho cai antes do novo subir
    # (deploy.yml:26-28), então há uma janela em que o chamador já carimba e o
    # validador ainda não tem a env, ou o contrário. Fechar junto com o deploy
    # seria 403 no checkout, na baixa de estoque e no job de reconciliação.
    # Medir servico_interno.ausente em prod; zerado, troca-se o log.warning
    # abaixo pelo mesmo `return` do ramo seguinte — uma linha.
    if not esperado or not recebido:
        log.warning(
            "servico_interno.ausente",
            path=request.url.path,
            configurado=bool(esperado),
            recebido=bool(recebido),
        )
        return await call_next(request)

    # encode(): compare_digest recusa str não-ASCII com TypeError, e o header vem
    # de fora — um byte acentuado viraria 500 em vez de 403.
    if not secrets.compare_digest(recebido.encode(), esperado.encode()):
        log.warning("servico_interno.invalido", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Forbidden"},
        )

    return await call_next(request)
