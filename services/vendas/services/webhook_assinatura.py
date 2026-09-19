"""
Assinatura HMAC dos webhooks do Mercado Pago (V5).

A rota `/loja/{slug}/webhook/mercadopago` é pública e não autenticada: quem
souber o slug podia postar qualquer coisa nela. O Mercado Pago assina cada
notificação v2 com o segredo da aplicação do lojista, e o cabeçalho estava
sendo apenas logado.

Molde do manifesto (documentação do MP):

    id:<data.id>;request-id:<x-request-id>;ts:<ts>;

Campo que não veio sai do molde inteiro, chave junto — por isso o manifesto é
montado por partes e não por format(). O `data.id` entra minúsculo quando tem
letra. O digest é HMAC-SHA256 hexadecimal, comparado em tempo constante.

Função pura, sem ORM e sem HTTP: o teste do formato não precisa de banco.
"""
import hashlib
import hmac


def _partes_da_assinatura(x_signature: str) -> dict[str, str]:
    """`ts=1704908010,v1=abc...` -> {'ts': '...', 'v1': '...'}."""
    partes = {}
    for pedaco in x_signature.split(","):
        chave, _, valor = pedaco.partition("=")
        if valor:
            partes[chave.strip()] = valor.strip()
    return partes


def montar_manifesto(data_id: str, x_request_id: str | None, ts: str) -> str:
    """Molde do MP, omitindo o campo (e sua chave) que não veio."""
    campos = [f"id:{data_id.lower()};"]
    if x_request_id:
        campos.append(f"request-id:{x_request_id};")
    campos.append(f"ts:{ts};")
    return "".join(campos)


def assinatura_valida(
    x_signature: str | None,
    x_request_id: str | None,
    data_id: str | None,
    segredo: str,
) -> bool:
    """
    True se `x-signature` confere com o segredo do lojista.

    Cabeçalho ausente, malformado ou sem `v1` é inválido — quem decide o que
    fazer com isso é a rota (hoje a ausência do cabeçalho ainda passa, ver
    routers/webhook.py).

    Não há janela de validade no `ts`: o handler não confia no corpo, ele
    relê o pagamento na API do MP pelo id, então repetir uma notificação
    antiga não muda nada que a idempotência do WebhookProcessado já não cubra.
    """
    if not x_signature or not data_id or not segredo:
        return False

    partes = _partes_da_assinatura(x_signature)
    ts, recebido = partes.get("ts"), partes.get("v1")
    if not ts or not recebido:
        return False

    esperado = hmac.new(
        segredo.encode(),
        montar_manifesto(data_id, x_request_id, ts).encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(esperado, recebido)
