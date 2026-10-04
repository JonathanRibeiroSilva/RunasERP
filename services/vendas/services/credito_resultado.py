"""
Classificação do resultado de débito/crédito no ledger do cliente (C3, Onda 6).

Mesmo molde de `estoque_resultado.py` — o endpoint de crédito segue o mesmo
contrato HTTP de `/estoque/reservar` (400 = recusa definitiva, resto = incerto):
- SUCESSO       : débito/crédito aplicado (ou já aplicado — idempotente).
- SEM_CREDITO   : 4xx definitivo — teto de crédito insuficiente, cliente
                  inexistente/bloqueado. Nada foi debitado; recusar a venda é seguro.
- INDETERMINADO : timeout/erro de rede/5xx. NÃO se sabe se debitou. NUNCA cancelar
                  uma venda paga nesse caso — marcar para reconciliação assíncrona.

Sem dependência de banco/HTTP — testável isoladamente.
"""
from enum import Enum


class ResultadoDebitoCredito(str, Enum):
    """Resultado de uma tentativa de debitar/creditar o ledger de crédito do cliente."""
    SUCESSO = "SUCESSO"
    SEM_CREDITO = "SEM_CREDITO"
    INDETERMINADO = "INDETERMINADO"


def classificar_credito_http(status_code: int) -> ResultadoDebitoCredito:
    """
    Classifica a resposta de POST /clientes/{id}/credito/ajustar.

    - 200/201 → SUCESSO
    - 4xx     → SEM_CREDITO (teto insuficiente ou cliente inválido; nada mudou)
    - demais  → INDETERMINADO (5xx/timeout: pode ter debitado antes de falhar)
    """
    if status_code in (200, 201):
        return ResultadoDebitoCredito.SUCESSO
    if 400 <= status_code < 500:
        return ResultadoDebitoCredito.SEM_CREDITO
    return ResultadoDebitoCredito.INDETERMINADO
