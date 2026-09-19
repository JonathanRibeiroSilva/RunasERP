"""
Política de decisão de webhooks de pagamento (anti-downgrade de status — C2).

Função pura que decide a ação a tomar a partir do status atual da venda e do status do
pagamento no Mercado Pago. Centraliza a regra que impede que webhooks atrasados,
duplicados ou fora de ordem rebaixem uma venda já confirmada/finalizada.

Sem dependência de ORM (usa os valores string de StatusVenda, que são varchar no banco) —
testável isoladamente.
"""
from enum import Enum
from typing import Optional


class AcaoWebhook(str, Enum):
    """Ação a executar para um evento de webhook de pagamento."""
    AGUARDAR = "AGUARDAR"            # pagamento em status não-final → esperar webhook final
    CONFIRMAR = "CONFIRMAR"         # aprovado e venda ainda não confirmada → confirmar venda
    IGNORAR = "IGNORAR"             # evento que NÃO deve alterar a venda (anti-downgrade)
    MARCAR_PENDENTE = "MARCAR_PENDENTE"  # negado em venda não paga → manter p/ nova tentativa
    REEMBOLSO = "REEMBOLSO"        # refunded/charged_back


# Espelham os valores de StatusVenda (varchar no banco). Mantidos locais para o módulo
# permanecer sem dependência de ORM. São estáveis (fazem parte do contrato de status).
_CONFIRMADA_OU_ALEM = frozenset({
    "CONFIRMADA", "SEPARADA", "EM_ENTREGA", "ENTREGUE", "FINALIZADA",
})
_STATUS_FINAIS = _CONFIRMADA_OU_ALEM | frozenset({"CANCELADA", "REEMBOLSADA"})
_STATUS_NOVA_TENTATIVA = frozenset({"PEDIDO", "PENDENTE_PAGAMENTO"})

# Status de pagamento do Mercado Pago.
_PAGAMENTO_NAO_FINAL = frozenset({"pending", "in_process", "in_mediation", "authorized"})
_PAGAMENTO_NEGADO = frozenset({"rejected", "cancelled"})
_PAGAMENTO_REEMBOLSO = frozenset({"refunded", "charged_back"})


def decidir_acao_webhook(status_venda: str, status_pagamento: Optional[str]) -> AcaoWebhook:
    """
    Decide a ação para um evento de pagamento, preservando a monotonicidade do status.

    Regras (C2):
    - Pagamento não-final (ou ausente) → AGUARDAR (não marcar processado: o webhook final
      do mesmo pagamento ainda precisa ser aceito).
    - approved:
        * venda já CONFIRMADA ou além → IGNORAR (idempotente; nunca reconfirmar/sobrescrever).
        * venda CANCELADA/REEMBOLSADA → IGNORAR (pago após cancelamento exige ação manual,
          nunca reativar automaticamente).
        * caso contrário → CONFIRMAR.
    - rejected/cancelled:
        * venda em estado final (confirmada/cancelada/...) → IGNORAR (anti-downgrade: nunca
          rebaixar uma venda já confirmada por um evento negado atrasado/fora de ordem).
        * caso contrário → MARCAR_PENDENTE (mantém a venda para nova tentativa).
    - refunded/charged_back:
        * venda já REEMBOLSADA → IGNORAR (idempotente).
        * caso contrário → REEMBOLSO (devolve estoque e marca reembolsada).
    """
    if status_pagamento is None or status_pagamento in _PAGAMENTO_NAO_FINAL:
        return AcaoWebhook.AGUARDAR

    if status_pagamento == "approved":
        if status_venda in _STATUS_FINAIS:
            return AcaoWebhook.IGNORAR
        return AcaoWebhook.CONFIRMAR

    if status_pagamento in _PAGAMENTO_NEGADO:
        if status_venda in _STATUS_NOVA_TENTATIVA:
            return AcaoWebhook.MARCAR_PENDENTE
        return AcaoWebhook.IGNORAR  # confirmada/terminal → não rebaixar

    if status_pagamento in _PAGAMENTO_REEMBOLSO:
        if status_venda == "REEMBOLSADA":
            return AcaoWebhook.IGNORAR  # já reembolsada → idempotente
        return AcaoWebhook.REEMBOLSO

    return AcaoWebhook.IGNORAR


def eh_cobranca_duplicada(
    status_venda: str,
    status_pagamento: Optional[str],
    payment_id,
    payment_id_da_venda: Optional[str],
) -> bool:
    """
    Pagamento aprovado DIFERENTE do que confirmou a venda: o cliente pagou duas vezes.

    decidir_acao_webhook devolve IGNORAR para "aprovado em venda já confirmada" — e
    está certo, a venda não deve ser reconfirmada. Mas IGNORAR junta dois casos que
    só o payment_id separa:
    - o mesmo pagamento chegando de novo (replay): inofensivo;
    - outro pagamento aprovado (dois links de pagamento pagos, aba antiga): dinheiro
      real capturado a mais, que ninguém devolve se ninguém souber.

    Venda confirmada sem payment_id foi confirmada fora do Mercado Pago (balcão):
    qualquer aprovação online para ela também é cobrança a mais.

    O payment_id do webhook pode chegar como número e o da venda é varchar — a
    comparação é em str, senão todo replay viraria falso alarme.
    """
    return (
        status_pagamento == "approved"
        and status_venda in _CONFIRMADA_OU_ALEM
        and str(payment_id) != str(payment_id_da_venda or "")
    )
