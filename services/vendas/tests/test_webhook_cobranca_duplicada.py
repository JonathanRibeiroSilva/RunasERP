"""Segundo pagamento aprovado numa venda já confirmada vira alerta, não um log.info.

O webhook decide IGNORAR tanto para o replay do pagamento que confirmou a venda
quanto para um pagamento novo aprovado depois — dois links pagos, uma aba antiga.
O segundo é dinheiro capturado a mais, e caía no mesmo log.info do replay:
ninguém via, ninguém devolvia. A regra pura está em
tests/unit/test_hardening_consistencia.py; aqui é a fiação, ponta a ponta pelo
processar_webhook_payment, com a API do Mercado Pago substituída e banco real.
"""
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.venda import HistoricoStatusVenda, StatusVenda, Venda
from repositories.venda_repository import VendaRepository
from services import mercadopago_service
from services.mercadopago_service import MercadoPagoService

EMPRESA = 990_301


class Registro:
    """Substitui o `log` do módulo e guarda cada evento emitido."""

    def __init__(self):
        self.eventos = []

    def __getattr__(self, nivel):
        return lambda evento, **campos: self.eventos.append((nivel, evento, campos))

    def de(self, nivel):
        return [(e, c) for n, e, c in self.eventos if n == nivel]


@pytest_asyncio.fixture
async def venda_paga(db, monkeypatch):
    """Venda CONFIRMADA pelo pagamento P1, com a API do Mercado Pago substituída."""
    venda = await VendaRepository.criar(
        db,
        empresa_id=EMPRESA,
        numero_venda=f"T-{uuid.uuid4().hex[:8]}",
        subtotal=Decimal("20"),
        valor_total=Decimal("20"),
        status=StatusVenda.CONFIRMADA.value,
        mercadopago_payment_id="P1",
    )
    await db.commit()

    async def detalhes(db_, empresa_id, payment_id):
        return {
            "status": "approved",
            "external_reference": str(venda.id),
            "transaction_amount": 20.0,
        }

    monkeypatch.setattr(MercadoPagoService, "obter_detalhes_pagamento", staticmethod(detalhes))
    registro = Registro()
    monkeypatch.setattr(mercadopago_service, "log", registro)
    return venda, registro


@pytest.mark.asyncio
async def test_segundo_pagamento_aprovado_vira_alerta_de_reembolso(db, venda_paga):
    venda, registro = venda_paga

    ok, erro = await MercadoPagoService.processar_webhook_payment(db, EMPRESA, "P2", "payment.updated")

    assert (ok, erro) == (True, None)
    criticos = registro.de("critical")
    assert [e for e, _ in criticos] == ["pagamento_duplicado_reembolso_necessario"], registro.eventos
    assert criticos[0][1]["payment_id"] == "P2"
    assert criticos[0][1]["payment_id_da_venda"] == "P1"

    atual = await db.get(Venda, venda.id)
    await db.refresh(atual)
    assert atual.mercadopago_payment_id == "P1", "o pagamento que confirmou a venda foi sobrescrito"
    historico = (await db.execute(
        select(HistoricoStatusVenda).where(HistoricoStatusVenda.venda_id == venda.id)
    )).scalars().all()
    assert any("duplicidade" in (h.observacao or "") for h in historico), (
        "o alerta só existe no stdout — o histórico da venda não diz nada"
    )


@pytest.mark.asyncio
async def test_replay_do_pagamento_que_confirmou_nao_alarma(db, venda_paga):
    _, registro = venda_paga

    ok, _ = await MercadoPagoService.processar_webhook_payment(db, EMPRESA, "P1", "payment.updated")

    assert ok is True
    assert registro.de("critical") == [], f"replay inofensivo virou alarme: {registro.eventos}"
    assert "webhook_ignorado_anti_downgrade" in [e for e, _ in registro.de("info")]
