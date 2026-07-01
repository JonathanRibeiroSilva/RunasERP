"""
Testes unitários da lógica de consistência de produção (C1–C4).

Cobrem as funções de decisão puras (sem banco) que são o núcleo das correções:
- C1: ordenação determinística de locks e detecção de deadlock recuperável.
- C2: política anti-downgrade de status de webhook.
- C4: classificação de 3 estados do resultado da baixa de estoque.

As garantias que dependem do PostgreSQL (locks FOR UPDATE, unique constraint, SKIP LOCKED,
retry de deadlock real) exigem ambiente de integração com Postgres — ver seção de validação
no relatório.
"""
import sys
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_RAIZ / "services" / "vendas" / "services"))
sys.path.insert(0, str(_RAIZ / "services" / "estoque" / "utils"))

from webhook_politica import AcaoWebhook, decidir_acao_webhook  # noqa: E402
from estoque_resultado import ResultadoBaixaEstoque, classificar_status_http  # noqa: E402
import concorrencia  # noqa: E402


# ----------------------------- C2: anti-downgrade -----------------------------

STATUS_CONFIRMADA_OU_ALEM = ["CONFIRMADA", "SEPARADA", "EM_ENTREGA", "ENTREGUE", "FINALIZADA"]
STATUS_NOVA_TENTATIVA = ["PEDIDO", "PENDENTE_PAGAMENTO"]


@pytest.mark.parametrize("status_venda", STATUS_NOVA_TENTATIVA)
def test_aprovado_em_venda_nao_confirmada_confirma(status_venda):
    assert decidir_acao_webhook(status_venda, "approved") is AcaoWebhook.CONFIRMAR


@pytest.mark.parametrize("status_venda", STATUS_CONFIRMADA_OU_ALEM)
def test_aprovado_em_venda_ja_confirmada_e_idempotente(status_venda):
    # Webhook approved duplicado / fora de ordem não reconfirma.
    assert decidir_acao_webhook(status_venda, "approved") is AcaoWebhook.IGNORAR


@pytest.mark.parametrize("status_venda", STATUS_CONFIRMADA_OU_ALEM)
@pytest.mark.parametrize("status_pagamento", ["rejected", "cancelled"])
def test_negado_apos_confirmacao_nunca_rebaixa(status_venda, status_pagamento):
    # CORE C2: evento negado atrasado NUNCA derruba uma venda já confirmada.
    assert decidir_acao_webhook(status_venda, status_pagamento) is AcaoWebhook.IGNORAR


@pytest.mark.parametrize("status_venda", STATUS_NOVA_TENTATIVA)
@pytest.mark.parametrize("status_pagamento", ["rejected", "cancelled"])
def test_negado_em_venda_nao_paga_mantem_para_nova_tentativa(status_venda, status_pagamento):
    assert decidir_acao_webhook(status_venda, status_pagamento) is AcaoWebhook.MARCAR_PENDENTE


@pytest.mark.parametrize("status_pagamento", ["pending", "in_process", "in_mediation", "authorized", None])
def test_status_pagamento_nao_final_aguarda(status_pagamento):
    assert decidir_acao_webhook("PEDIDO", status_pagamento) is AcaoWebhook.AGUARDAR


def test_aprovado_apos_cancelamento_nao_reativa():
    # Pago após cancelamento/timeout: exige revisão manual, não reativa automaticamente.
    assert decidir_acao_webhook("CANCELADA", "approved") is AcaoWebhook.IGNORAR
    assert decidir_acao_webhook("REEMBOLSADA", "approved") is AcaoWebhook.IGNORAR


def test_negado_em_venda_cancelada_e_ignorado():
    assert decidir_acao_webhook("CANCELADA", "rejected") is AcaoWebhook.IGNORAR


@pytest.mark.parametrize("status_pagamento", ["refunded", "charged_back"])
def test_reembolso(status_pagamento):
    assert decidir_acao_webhook("CONFIRMADA", status_pagamento) is AcaoWebhook.REEMBOLSO


# ------------------------- C4: classificação 3 estados ------------------------

@pytest.mark.parametrize("codigo", [200, 201])
def test_baixa_estoque_sucesso(codigo):
    assert classificar_status_http(codigo) is ResultadoBaixaEstoque.SUCESSO


def test_baixa_estoque_409_e_sem_estoque_definitivo():
    assert classificar_status_http(409) is ResultadoBaixaEstoque.SEM_ESTOQUE


@pytest.mark.parametrize("codigo", [500, 502, 503, 504, 400, 408, 429])
def test_baixa_estoque_erro_e_indeterminado(codigo):
    # Qualquer coisa fora de 200/201/409 → não se sabe se baixou → INDETERMINADO.
    assert classificar_status_http(codigo) is ResultadoBaixaEstoque.INDETERMINADO


# --------------------- C1: ordenação de locks e deadlock ---------------------

class _FakeOrig:
    def __init__(self, sqlstate):
        self.sqlstate = sqlstate


class _FakeDBError(Exception):
    def __init__(self, sqlstate):
        super().__init__("db error")
        self.orig = _FakeOrig(sqlstate)


def test_detecta_deadlock_40P01():
    assert concorrencia.eh_erro_transitorio(_FakeDBError("40P01")) is True


def test_detecta_serialization_failure_40001():
    assert concorrencia.eh_erro_transitorio(_FakeDBError("40001")) is True


def test_nao_retenta_erro_nao_transitorio():
    assert concorrencia.eh_erro_transitorio(_FakeDBError("23505")) is False  # unique violation
    assert concorrencia.eh_erro_transitorio(Exception("qualquer")) is False


def test_extrai_sqlstate_de_pgcode():
    class _ComPgcode(Exception):
        pgcode = "40P01"
    assert concorrencia.extrair_sqlstate(_ComPgcode()) == "40P01"


def test_ordenacao_deterministica_de_itens():
    # Itens em ordens diferentes produzem a MESMA sequência de chaves → mesma ordem de lock.
    a = ("11111111-1111-1111-1111-111111111111", None)
    b = ("22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333")
    chave = lambda par: concorrencia.chave_ordenacao_item(par[0], par[1])
    assert sorted([a, b], key=chave) == sorted([b, a], key=chave)


def test_chave_ordenacao_variante_none_e_estavel():
    assert concorrencia.chave_ordenacao_item("p", None) == ("p", "")
    assert concorrencia.chave_ordenacao_item("p", "v") == ("p", "v")


def test_backoff_cresce_exponencialmente():
    assert concorrencia.backoff_segundos(0) < concorrencia.backoff_segundos(1)
    assert concorrencia.backoff_segundos(1) < concorrencia.backoff_segundos(2)
