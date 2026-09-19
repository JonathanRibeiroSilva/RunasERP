"""V5 — formato do manifesto assinado pelo Mercado Pago.

Os digests abaixo foram calculados fora daqui, contra o molde da documentação
do MP. Recalculá-los com a mesma função que está sob teste não provaria nada:
qualquer mudança no molde (a ordem dos campos, o `;` final, a chave que sai
junto com o campo ausente, o id minúsculo) continuaria "passando" porque os
dois lados mudariam juntos. Hardcoded, um molde errado fica vermelho.

A fiação na rota — quem é recusado e quem ainda passa — está em
services/vendas/tests/test_webhook_assinatura.py.
"""
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_RAIZ / "services" / "vendas" / "services"))

from webhook_assinatura import assinatura_valida, montar_manifesto  # noqa: E402

SEGREDO = "segredo-de-teste"
TS = "1704908010"
# id:123456789;request-id:req-1;ts:1704908010;
V1_COM_REQUEST_ID = "8cc05d40599db738fe4d394e42abe2db721751947936bfc5ae8737b48b00eebf"
# id:123456789;ts:1704908010;  (sem x-request-id a chave sai do molde também)
V1_SEM_REQUEST_ID = "29510bde29a6f408cae773f7cdf0f446e929befdb25cd3b19cb995856775d619"
# id:abc-def;request-id:req-1;ts:1704908010;  (id chega em maiúsculas)
V1_ID_MINUSCULO = "b9f44a84100908ef27dba92aaf790e2a64241128734f46ed56b51bcf9004f07a"


def test_manifesto_segue_o_molde_do_mercado_pago():
    assert montar_manifesto("123456789", "req-1", TS) == "id:123456789;request-id:req-1;ts:1704908010;"


def test_campo_ausente_sai_do_molde_com_a_chave():
    assert montar_manifesto("123456789", None, TS) == "id:123456789;ts:1704908010;"


def test_assinatura_correta_e_aceita():
    assert assinatura_valida(f"ts={TS},v1={V1_COM_REQUEST_ID}", "req-1", "123456789", SEGREDO)


def test_assinatura_sem_request_id_e_aceita():
    assert assinatura_valida(f"ts={TS},v1={V1_SEM_REQUEST_ID}", None, "123456789", SEGREDO)


def test_id_com_letra_e_normalizado_para_minusculo():
    assert assinatura_valida(f"ts={TS},v1={V1_ID_MINUSCULO}", "req-1", "ABC-DEF", SEGREDO)


def test_segredo_errado_e_recusado():
    assert not assinatura_valida(f"ts={TS},v1={V1_COM_REQUEST_ID}", "req-1", "123456789", "outro")


def test_id_trocado_e_recusado():
    """O ataque que a assinatura existe para barrar: mesmo envelope, outro pagamento."""
    assert not assinatura_valida(f"ts={TS},v1={V1_COM_REQUEST_ID}", "req-1", "987654321", SEGREDO)


def test_ts_trocado_e_recusado():
    assert not assinatura_valida(f"ts=1,v1={V1_COM_REQUEST_ID}", "req-1", "123456789", SEGREDO)


def test_request_id_trocado_e_recusado():
    assert not assinatura_valida(f"ts={TS},v1={V1_COM_REQUEST_ID}", "req-2", "123456789", SEGREDO)


def test_cabecalho_ausente_ou_malformado_e_recusado():
    for cabecalho in [None, "", "v1=", f"ts={TS}", V1_COM_REQUEST_ID, "lixo"]:
        assert not assinatura_valida(cabecalho, "req-1", "123456789", SEGREDO), cabecalho


def test_sem_segredo_ou_sem_id_e_recusado():
    """Quem decide o que fazer com 'não dá para verificar' é a rota, não esta função."""
    assert not assinatura_valida(f"ts={TS},v1={V1_COM_REQUEST_ID}", "req-1", "123456789", "")
    assert not assinatura_valida(f"ts={TS},v1={V1_COM_REQUEST_ID}", "req-1", None, SEGREDO)
