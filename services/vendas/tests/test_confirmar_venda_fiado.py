"""
Gate de crédito na confirmação de venda fiada (C3, Onda 6).

Antes, `confirmar_venda` só checava "tem cliente identificado" para FIADO — o
teto de crédito nunca era checado, e o próprio ledger de crédito nunca era
debitado. Qualquer venda fiada passava, não importa o limite do cliente.

O gate de crédito roda ANTES do de estoque: o débito é reversível com uma
chamada idempotente (creditar de volta), a baixa de estoque não. HTTP para
clientes e estoque é substituído; o banco é o Postgres de verdade.
"""
import uuid
from decimal import Decimal

import pytest

from models.venda import StatusVenda
from repositories.venda_repository import ItemVendaRepository, VendaRepository
from schemas.venda import ConfirmarVendaRequest, PagamentoVendaCreate
from services.credito_resultado import ResultadoDebitoCredito
from services.estoque_resultado import ResultadoBaixaEstoque
from services.venda_service import CreditoIndeterminadoError, VendaService

EMPRESA = 990_401
VALOR = Decimal("20.00")


@pytest.fixture
def estoque_ok(monkeypatch):
    """Estoque sempre dá certo — o que está sob teste é o gate de crédito."""
    chamadas = {"baixas": 0}

    async def baixar(empresa_id, venda):
        chamadas["baixas"] += 1
        return (ResultadoBaixaEstoque.SUCESSO, None)

    monkeypatch.setattr(VendaService, "baixar_estoque_venda", staticmethod(baixar))
    return chamadas


@pytest.fixture
def credito(monkeypatch):
    """Registra o que a confirmação pede ao ledger de crédito e decide a resposta."""
    chamadas = {"debitos": [], "creditos": []}
    config = {"resultado": ResultadoDebitoCredito.SUCESSO}

    async def debitar(empresa_id, cliente_id, valor, documento):
        chamadas["debitos"].append((cliente_id, valor, documento))
        return config["resultado"]

    async def creditar(empresa_id, cliente_id, valor, documento):
        chamadas["creditos"].append((cliente_id, valor, documento))
        return True

    monkeypatch.setattr(VendaService, "debitar_credito_cliente", staticmethod(debitar))
    monkeypatch.setattr(VendaService, "creditar_credito_cliente", staticmethod(creditar))
    return chamadas, config


async def _venda_fiada(db, cliente_id):
    venda = await VendaRepository.criar(
        db,
        empresa_id=EMPRESA,
        numero_venda=f"T-{uuid.uuid4().hex[:8]}",
        subtotal=VALOR,
        valor_total=VALOR,
        status=StatusVenda.PEDIDO.value,
        cliente_id=cliente_id,
    )
    await ItemVendaRepository.criar(
        db,
        venda_id=venda.id,
        produto_id=uuid.uuid4(),
        descricao_produto="Produto",
        quantidade=Decimal("1"),
        preco_unitario=VALOR,
        subtotal=VALOR,
        estoque_reservado=True,
        estoque_baixado=False,
    )
    await db.commit()
    return venda


def _confirmar_fiado():
    return ConfirmarVendaRequest(pagamentos=[
        PagamentoVendaCreate(forma_pagamento="FIADO", valor_pago=VALOR)
    ])


@pytest.mark.asyncio
async def test_credito_insuficiente_recusa_a_venda_sem_tocar_no_estoque(db, estoque_ok, credito):
    chamadas, config = credito
    config["resultado"] = ResultadoDebitoCredito.SEM_CREDITO
    cliente_id = uuid.uuid4()
    venda = await _venda_fiada(db, cliente_id)
    # Capturados antes: o rollback do serviço expira as instâncias da sessão, e ler
    # um atributo expirado fora de await é um lazy-load síncrono (MissingGreenlet).
    venda_id, numero_venda = venda.id, venda.numero_venda

    with pytest.raises(ValueError, match="[Cc]rédito"):
        await VendaService.confirmar_venda(db, EMPRESA, venda_id, _confirmar_fiado())

    assert estoque_ok["baixas"] == 0, "checou o estoque antes de saber se o crédito cobria"
    assert chamadas["debitos"] == [(cliente_id, VALOR, numero_venda)]

    venda_recarregada = await VendaRepository.buscar_por_id(db, EMPRESA, venda_id)
    assert venda_recarregada.status == StatusVenda.PEDIDO.value, (
        "recusar por falta de crédito não devia mudar o status da venda"
    )


@pytest.mark.asyncio
async def test_credito_indeterminado_marca_reconciliacao_sem_cancelar(db, estoque_ok, credito):
    chamadas, config = credito
    config["resultado"] = ResultadoDebitoCredito.INDETERMINADO
    venda = await _venda_fiada(db, uuid.uuid4())
    venda_id = venda.id  # capturado antes: ver nota em test_credito_insuficiente_recusa...

    with pytest.raises(CreditoIndeterminadoError):
        await VendaService.confirmar_venda(db, EMPRESA, venda_id, _confirmar_fiado())

    assert estoque_ok["baixas"] == 0

    venda_recarregada = await VendaRepository.buscar_por_id(db, EMPRESA, venda_id)
    assert venda_recarregada.status == StatusVenda.PEDIDO.value, "não pode cancelar no incerto"
    assert venda_recarregada.reconciliacao_credito_pendente is True
    assert venda_recarregada.reconciliacao_estoque_pendente is False, (
        "reconciliação de crédito não pode acender a de estoque — são eventos distintos"
    )


@pytest.mark.asyncio
async def test_venda_fiada_confirmada_debita_o_credito(db, estoque_ok, credito):
    chamadas, _ = credito
    cliente_id = uuid.uuid4()
    venda = await _venda_fiada(db, cliente_id)
    venda_id, numero_venda = venda.id, venda.numero_venda

    await VendaService.confirmar_venda(db, EMPRESA, venda_id, _confirmar_fiado())

    assert chamadas["debitos"] == [(cliente_id, VALOR, numero_venda)]
    venda_recarregada = await VendaRepository.buscar_por_id(db, EMPRESA, venda_id)
    assert venda_recarregada.status == StatusVenda.CONFIRMADA.value


@pytest.mark.asyncio
async def test_sem_estoque_depois_do_credito_debitado_devolve_o_credito(db, credito, monkeypatch):
    """O gate de crédito vem antes do de estoque — se o estoque falhar depois,
    o crédito que já foi debitado tem que voltar, senão o cliente perde limite
    de uma venda que nunca se efetivou."""
    chamadas, _ = credito

    async def baixar_sem_estoque(empresa_id, venda):
        return (ResultadoBaixaEstoque.SEM_ESTOQUE, "sem estoque para o item")

    async def liberar_noop(empresa_id, produto_id, variante_id, quantidade, documento):
        return True

    monkeypatch.setattr(VendaService, "baixar_estoque_venda", staticmethod(baixar_sem_estoque))
    monkeypatch.setattr(VendaService, "liberar_reserva_estoque", staticmethod(liberar_noop))

    cliente_id = uuid.uuid4()
    venda = await _venda_fiada(db, cliente_id)
    venda_id, numero_venda = venda.id, venda.numero_venda

    with pytest.raises(ValueError, match="[Ee]stoque"):
        await VendaService.confirmar_venda(db, EMPRESA, venda_id, _confirmar_fiado())

    assert chamadas["creditos"] == [(cliente_id, VALOR, numero_venda)], (
        "estoque recusou depois do crédito debitado — o crédito tem que voltar"
    )
