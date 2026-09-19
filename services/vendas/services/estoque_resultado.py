"""
Classificação do resultado da baixa de estoque (cross-service consistency — C4).

Distingue três resultados que exigem tratamentos diferentes na confirmação da venda:
- SUCESSO       : estoque baixado (ou já baixado — idempotente). Pode confirmar.
- SEM_ESTOQUE   : 409 definitivo, NADA foi baixado (baixa é atômica). Cancelar é seguro.
- INDETERMINADO : timeout/erro de rede/5xx. NÃO se sabe se o estoque baixou. NUNCA cancelar
                  uma venda paga nesse caso — marcar para reconciliação assíncrona.

Sem dependência de banco/HTTP — testável isoladamente.
"""
from enum import Enum
from typing import Optional


class ResultadoBaixaEstoque(str, Enum):
    """Resultado de uma tentativa de baixar o estoque de uma venda."""
    SUCESSO = "SUCESSO"
    SEM_ESTOQUE = "SEM_ESTOQUE"
    INDETERMINADO = "INDETERMINADO"


def classificar_status_http(status_code: int) -> ResultadoBaixaEstoque:
    """
    Classifica a resposta HTTP do serviço de estoque.

    - 200/201 → SUCESSO
    - 409     → SEM_ESTOQUE (regra de negócio: estoque insuficiente, baixa não ocorreu)
    - demais  → INDETERMINADO (5xx ou inesperado: o resultado real é desconhecido)
    """
    if status_code in (200, 201):
        return ResultadoBaixaEstoque.SUCESSO
    if status_code == 409:
        return ResultadoBaixaEstoque.SEM_ESTOQUE
    return ResultadoBaixaEstoque.INDETERMINADO


def classificar_reserva_http(status_code: int) -> ResultadoBaixaEstoque:
    """
    Classifica a resposta de POST /estoque/reservar.

    Não é a mesma tabela da baixa: /reservar devolve 400 quando falta estoque
    (ValueError no router), não 409. Qualquer 4xx aqui significa que o estoque
    respondeu e NÃO reservou — insuficiente, produto sem linha de estoque, tenant
    divergente, payload inválido. É definitivo: a venda pode ser recusada sem
    nada a desfazer por este item.

    - 200/201 → SUCESSO
    - 4xx     → SEM_ESTOQUE
    - demais  → INDETERMINADO (5xx: pode ter reservado antes de falhar)
    """
    if status_code in (200, 201):
        return ResultadoBaixaEstoque.SUCESSO
    if 400 <= status_code < 500:
        return ResultadoBaixaEstoque.SEM_ESTOQUE
    return ResultadoBaixaEstoque.INDETERMINADO
