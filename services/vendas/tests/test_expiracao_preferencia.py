"""V3 — o link de pagamento expira junto com a venda.

A preferência ia para o Mercado Pago com `expires: True` e as duas datas em
None, que para o MP é o mesmo que não expirar. O comentário ao lado dizia
"5 minutos (calculado no momento)" e nada calculava nada. Resultado: o job
cancelava a venda aos 5 minutos e devolvia o estoque, e o link continuava
pagável — para sempre, e em quantas abas o comprador tivesse aberto.

O que os testes prendem é o acoplamento, não o número: se alguém mexer no
prazo do job sem mexer no da preferência (ou vice-versa), sobra de novo link
pagável de venda cancelada.
"""
import os
import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet

from models.venda import ConfiguracaoPagamento, StatusVenda
from repositories.venda_repository import ItemVendaRepository, VendaRepository
from services import mercadopago_service
from services.mercadopago_service import TIMEOUT_PAGAMENTO, MercadoPagoService, _agora_mp

EMPRESA = 990_601


class RespostaFake:
    status_code = 201
    text = ""
    headers: dict = {}

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "id": "PREF-1",
            "init_point": "https://mp.exemplo/checkout",
            "sandbox_init_point": "https://mp.exemplo/sandbox",
        }


@pytest.fixture(autouse=True)
def chave_de_cifra():
    """O access token é gravado cifrado; sem a chave o setter levanta."""
    from config import settings
    from utils import crypto

    os.environ.setdefault("INTEGRACOES_SECRET_KEY", Fernet.generate_key().decode())
    settings.INTEGRACOES_SECRET_KEY = os.environ["INTEGRACOES_SECRET_KEY"]
    crypto._fernet.cache_clear()
    yield
    crypto._fernet.cache_clear()


@pytest_asyncio.fixture
async def payload(db, monkeypatch):
    """Cria a preferência de uma venda real e devolve o JSON que iria ao MP."""
    capturado = {}

    class ClienteFake:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None, **kwargs):
            capturado.update(json or {})
            return RespostaFake()

    monkeypatch.setattr(mercadopago_service.httpx, "AsyncClient", ClienteFake)

    db.add(ConfiguracaoPagamento(
        empresa_id=EMPRESA,
        mercadopago_access_token="APP_USR-fake",
        mercadopago_public_key="APP_USR-fake",
        ativo=True,
    ))
    venda = await VendaRepository.criar(
        db,
        empresa_id=EMPRESA,
        numero_venda=f"T-{uuid.uuid4().hex[:8]}",
        subtotal=Decimal("10"),
        valor_total=Decimal("10"),
        status=StatusVenda.PENDENTE_PAGAMENTO.value,
    )
    await ItemVendaRepository.criar(
        db,
        venda_id=venda.id,
        produto_id=uuid.uuid4(),
        descricao_produto="Produto",
        quantidade=Decimal("1"),
        preco_unitario=Decimal("10"),
        subtotal=Decimal("10"),
    )
    await db.commit()

    venda = await VendaRepository.buscar_por_id(db, EMPRESA, venda.id, com_relacionamentos=True)
    _, _, _, erro = await MercadoPagoService.criar_preferencia(
        db=db, venda=venda, empresa_id=EMPRESA, empresa_slug="loja-teste"
    )
    assert erro is None, erro
    return capturado


def _data(valor: str) -> datetime:
    return datetime.fromisoformat(valor)


def test_formato_da_data_e_o_que_o_mercado_pago_exige():
    """ISO-8601 com milissegundos e offset. Sem os .SSS o MP recusa a preferência."""
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}", _agora_mp())


@pytest.mark.asyncio
async def test_preferencia_vai_com_as_duas_datas(payload):
    assert payload["expires"] is True
    assert payload["expiration_date_from"], "link sem data de início continua sem expirar"
    assert payload["expiration_date_to"], "link sem data de fim continua pagável para sempre"


@pytest.mark.asyncio
async def test_janela_do_link_e_o_mesmo_prazo_do_job(payload):
    inicio = _data(payload["expiration_date_from"])
    fim = _data(payload["expiration_date_to"])

    assert fim - inicio == TIMEOUT_PAGAMENTO, (
        "o link vive mais (ou menos) do que a venda: o job cancela em "
        f"{TIMEOUT_PAGAMENTO} e este expira em {fim - inicio}"
    )
    assert abs(inicio - datetime.now(inicio.tzinfo)) < timedelta(minutes=1), (
        "a janela não começa agora — link criado com data de início no passado "
        "nasce parte do prazo já gasto"
    )


def test_job_e_preferencia_leem_a_mesma_constante():
    """Duas cópias do 5 é como o bug volta: mexem numa e esquecem a outra."""
    from jobs import verificar_pagamentos_pendentes

    assert verificar_pagamentos_pendentes.TIMEOUT_PAGAMENTO is TIMEOUT_PAGAMENTO
