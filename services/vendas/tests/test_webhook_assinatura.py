"""V5 — a rota do webhook confere a assinatura do Mercado Pago.

`/loja/{slug}/webhook/mercadopago` é pública: o `x-signature` chegava, era
logado e ignorado. Quem soubesse o slug podia postar notificação de pagamento.

Este arquivo prende as três decisões da rota, incluindo as duas janelas
deliberadamente abertas — que existem para não derrubar pagamento de quem
ainda não colou o segredo, e que um dia fecham. Se alguém fechar sem querer,
dois destes testes ficam vermelhos e dizem qual janela era.

O formato do manifesto está em tests/unit/test_webhook_assinatura.py (puro).
"""
import hashlib
import hmac
import os
import uuid

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet

from models.venda import ConfiguracaoPagamento
from routers import webhook
from services.mercadopago_service import MercadoPagoService

EMPRESA = 990_501
SLUG = "loja-teste-assinatura"
SEGREDO = "segredo-do-lojista"
TS = "1704908010"


def _assinar(data_id: str, request_id: str, segredo: str = SEGREDO) -> dict[str, str]:
    manifesto = f"id:{data_id};request-id:{request_id};ts:{TS};"
    v1 = hmac.new(segredo.encode(), manifesto.encode(), hashlib.sha256).hexdigest()
    return {"x-signature": f"ts={TS},v1={v1}", "x-request-id": request_id}


@pytest.fixture(autouse=True)
def chave_de_cifra():
    """Sem INTEGRACOES_SECRET_KEY o setter do segredo levanta — ver utils/crypto.py."""
    from config import settings
    from utils import crypto

    os.environ.setdefault("INTEGRACOES_SECRET_KEY", Fernet.generate_key().decode())
    settings.INTEGRACOES_SECRET_KEY = os.environ["INTEGRACOES_SECRET_KEY"]
    crypto._fernet.cache_clear()
    yield
    crypto._fernet.cache_clear()


@pytest_asyncio.fixture
async def loja(db, monkeypatch):
    """Empresa resolvida pelo slug, sem o serviço de empresas, e sem chamar o MP."""
    processados = []

    async def por_slug(db_, slug):
        return EMPRESA if slug == SLUG else None

    async def processar(db, empresa_id, payment_id, tipo_evento):
        processados.append(payment_id)
        return True, None

    # A rota importou o nome direto (`from utils.tenant import ...`), então o
    # que precisa ser trocado é o atributo do módulo da rota, não o de origem.
    monkeypatch.setattr(webhook, "get_empresa_id_by_slug", por_slug)
    monkeypatch.setattr(
        MercadoPagoService, "processar_webhook_payment", staticmethod(processar)
    )
    return processados


async def _config(db, com_segredo: bool):
    config = ConfiguracaoPagamento(
        empresa_id=EMPRESA,
        mercadopago_access_token="APP_USR-fake",
        mercadopago_public_key="APP_USR-fake",
        mercadopago_webhook_secret=SEGREDO if com_segredo else None,
        ativo=True,
    )
    db.add(config)
    await db.commit()
    return config


async def _postar(client, payment_id, headers=None):
    return await client.post(
        f"/loja/{SLUG}/webhook/mercadopago",
        json={"type": "payment", "action": "payment.updated", "data": {"id": payment_id}},
        headers=headers or {},
    )


@pytest.mark.asyncio
async def test_assinatura_valida_processa(client, db, loja):
    await _config(db, com_segredo=True)
    payment_id = str(uuid.uuid4().int % 10**9)

    resposta = await _postar(client, payment_id, _assinar(payment_id, "req-1"))

    assert resposta.status_code == 200, resposta.text
    assert loja == [payment_id]


@pytest.mark.asyncio
async def test_assinatura_de_outro_segredo_e_recusada(client, db, loja):
    await _config(db, com_segredo=True)
    payment_id = "123456789"

    resposta = await _postar(client, payment_id, _assinar(payment_id, "req-1", "segredo-do-atacante"))

    assert resposta.status_code == 401, resposta.text
    assert loja == [], "recusou depois de já ter processado o pagamento"


@pytest.mark.asyncio
async def test_assinatura_de_outro_pagamento_e_recusada(client, db, loja):
    """Envelope legítimo reaproveitado para outro id — o manifesto inclui o id."""
    await _config(db, com_segredo=True)

    resposta = await _postar(client, "987654321", _assinar("123456789", "req-1"))

    assert resposta.status_code == 401, resposta.text
    assert loja == []


@pytest.mark.asyncio
async def test_janela_aberta_lojista_sem_segredo_gravado(client, db, loja):
    """Até o lojista colar o segredo do painel, a rota segue como era antes."""
    await _config(db, com_segredo=False)

    resposta = await _postar(client, "111222333")

    assert resposta.status_code == 200, resposta.text
    assert loja == ["111222333"]


@pytest.mark.asyncio
async def test_janela_aberta_notificacao_sem_cabecalho(client, db, loja):
    """O IPN legado (cartão com 3DS) não assina. Negar aqui é perder venda."""
    await _config(db, com_segredo=True)

    resposta = await _postar(client, "444555666")

    assert resposta.status_code == 200, resposta.text
    assert loja == ["444555666"]
