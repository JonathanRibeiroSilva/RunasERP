"""
Carimbo de origem interna nas chamadas que o gateway faz aos serviços.

O outro lado é `services/*/middleware_interno.py`, que valida. Aqui só carimba:
nada interno chama o gateway de volta, exceto `vendas/services/loja_service.py`,
que carimba por conta própria.

Deliberadamente opt-in, uma chamada por vez: o gateway também fala com Google,
Microsoft e Mercado Pago, e mandar o segredo interno para terceiro é vazar
credencial. Um hook global no httpx seria menos código e carimbaria esses três.
"""
from config import settings

HEADER = "X-Servico-Interno-Token"


def auth_interno(headers: dict[str, str] | None = None) -> dict[str, str]:
    """Devolve os headers com a prova de origem interna. Só para destino interno."""
    headers = dict(headers or {})
    # Vazio = fail-open: o validador do outro lado loga e deixa passar.
    if settings.SERVICO_INTERNO_TOKEN:
        headers[HEADER] = settings.SERVICO_INTERNO_TOKEN
    return headers
