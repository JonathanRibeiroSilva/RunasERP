"""Cancelar venda já paga e separada: o estoque volta e o reembolso é sinalizado.

CONFIRMADA e SEPARADA já passaram pela baixa definitiva — e, na loja online, o
dinheiro já foi capturado. O cancelamento só liberava reserva de item não
baixado: o estoque dos baixados sumia do sistema, e o pagamento ficava retido sem
nada que avisasse. Um funcionário cancelando um pedido pago é operação normal.

Também guarda a ordem das operações: a reserva de um item baixado já foi
consumida pela baixa. Se o estoque_baixado for zerado antes do loop de liberar
reservas, esse item tem a reserva liberada de novo — e o contador é por produto,
então a liberação extra solta a reserva de outro pedido.

HTTP para o estoque é substituído; o banco é o Postgres de verdade.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from models.venda import HistoricoStatusVenda, ItemVenda, StatusReserva, StatusVenda, Venda
from repositories.venda_repository import (
    ItemVendaRepository,
    ReservaEstoqueVendaRepository,
    VendaRepository,
)
from schemas.venda import CancelarVendaRequest
from services import venda_service
from services.venda_service import EstoqueIndeterminadoError, VendaService

EMPRESA = 990_201
MOTIVO = "cliente desistiu da compra"


class Registro:
    """Substitui o `log` do módulo e guarda cada evento emitido."""

    def __init__(self):
        self.eventos = []

    def __getattr__(self, nivel):
        return lambda evento, **campos: self.eventos.append((nivel, evento, campos))


@pytest.fixture
def estoque(monkeypatch):
    """Registra o que o cancelamento pede ao estoque e decide a resposta."""
    chamadas = {"estornos": [], "liberados": []}
    config = {"estorno_ok": True}

    async def estornar(empresa_id, venda):
        chamadas["estornos"].append(venda.numero_venda)
        return (True, None) if config["estorno_ok"] else (False, "timeout no estoque")

    async def liberar(empresa_id, produto_id, variante_id, quantidade, documento):
        chamadas["liberados"].append(produto_id)
        return True

    monkeypatch.setattr(VendaService, "estornar_estoque_venda", staticmethod(estornar))
    monkeypatch.setattr(VendaService, "liberar_reserva_estoque", staticmethod(liberar))
    return chamadas, config


async def _venda(db, status, itens, payment_id=None):
    """itens: lista de (estoque_reservado, estoque_baixado)."""
    venda = await VendaRepository.criar(
        db,
        empresa_id=EMPRESA,
        numero_venda=f"T-{uuid.uuid4().hex[:8]}",
        subtotal=Decimal("20"),
        valor_total=Decimal("20"),
        status=status,
        mercadopago_payment_id=payment_id,
    )
    produtos = []
    for reservado, baixado in itens:
        produto_id = uuid.uuid4()
        await ItemVendaRepository.criar(
            db,
            venda_id=venda.id,
            produto_id=produto_id,
            descricao_produto="Produto",
            quantidade=Decimal("1"),
            preco_unitario=Decimal("10"),
            subtotal=Decimal("10"),
            estoque_reservado=reservado,
            estoque_baixado=baixado,
        )
        produtos.append(produto_id)
    # commit: o serviço dá rollback no erro, e sem isto o rollback levaria junto
    # o que o teste montou. A fixture `db` desfaz tudo no fim de qualquer jeito.
    await db.commit()
    return venda, produtos


async def _recarregar(db, venda_id):
    venda = await db.get(Venda, venda_id)
    await db.refresh(venda)
    itens = (await db.execute(
        select(ItemVenda).where(ItemVenda.venda_id == venda_id)
        .execution_options(populate_existing=True)
    )).scalars().all()
    return venda, itens


@pytest.mark.asyncio
async def test_cancelar_venda_separada_devolve_o_estoque_baixado(db, estoque):
    chamadas, _ = estoque
    venda, _ = await _venda(db, StatusVenda.SEPARADA.value, [(True, True), (True, True)])

    await VendaService.cancelar_venda(db, EMPRESA, venda.id, CancelarVendaRequest(motivo=MOTIVO))

    venda, itens = await _recarregar(db, venda.id)
    assert chamadas["estornos"] == [venda.numero_venda], "o estoque baixado não foi devolvido"
    assert venda.status == StatusVenda.CANCELADA.value
    assert all(not i.estoque_baixado for i in itens)


@pytest.mark.asyncio
async def test_item_baixado_nao_tem_a_reserva_liberada_de_novo(db, estoque):
    chamadas, _ = estoque
    venda, (baixado, so_reservado) = await _venda(
        db, StatusVenda.CONFIRMADA.value, [(True, True), (True, False)]
    )

    await VendaService.cancelar_venda(db, EMPRESA, venda.id, CancelarVendaRequest(motivo=MOTIVO))

    assert chamadas["liberados"] == [so_reservado], (
        "liberou a reserva de um item já baixado — a baixa já a consumiu, e soltar de "
        f"novo solta a de outro pedido: {chamadas['liberados']}"
    )


@pytest.mark.asyncio
async def test_estorno_indeterminado_nao_cancela_nem_mexe_em_nada(db, estoque):
    chamadas, config = estoque
    config["estorno_ok"] = False
    venda, _ = await _venda(db, StatusVenda.SEPARADA.value, [(True, True)])
    # O id sai antes: o rollback do serviço expira as instâncias da sessão, e ler um
    # atributo expirado fora de await é um lazy-load síncrono (MissingGreenlet).
    venda_id = venda.id

    with pytest.raises(EstoqueIndeterminadoError):
        await VendaService.cancelar_venda(db, EMPRESA, venda_id, CancelarVendaRequest(motivo=MOTIVO))

    venda, itens = await _recarregar(db, venda_id)
    assert venda.status == StatusVenda.SEPARADA.value, "cancelou sem saber se o estoque voltou"
    assert itens[0].estoque_baixado is True
    assert chamadas["liberados"] == [], "liberou reserva antes de saber do estorno"


@pytest.mark.asyncio
async def test_venda_paga_online_cancelada_pede_reembolso(db, estoque, monkeypatch):
    registro = Registro()
    monkeypatch.setattr(venda_service, "log", registro)
    venda, _ = await _venda(db, StatusVenda.CONFIRMADA.value, [(True, True)], payment_id="MP-777")

    await VendaService.cancelar_venda(db, EMPRESA, venda.id, CancelarVendaRequest(motivo=MOTIVO))

    criticos = [(e, c) for nivel, e, c in registro.eventos if nivel == "critical"]
    assert [e for e, _ in criticos] == ["venda_cancelada_paga_reembolso_necessario"], registro.eventos
    assert criticos[0][1]["payment_id"] == "MP-777"
    historico = (await db.execute(
        select(HistoricoStatusVenda).where(HistoricoStatusVenda.venda_id == venda.id)
    )).scalars().all()
    assert any("reembolso manual" in (h.observacao or "") for h in historico), (
        "o pedido de reembolso só existe no stdout — o histórico da venda não diz nada"
    )


@pytest.mark.asyncio
async def test_pedido_sem_baixa_so_libera_reserva(db, estoque):
    chamadas, _ = estoque
    venda, (produto,) = await _venda(db, StatusVenda.PEDIDO.value, [(True, False)])

    await VendaService.cancelar_venda(db, EMPRESA, venda.id, CancelarVendaRequest(motivo=MOTIVO))

    assert chamadas["liberados"] == [produto]


@pytest.mark.asyncio
async def test_falha_ao_liberar_nao_marca_reserva_liberada(db, estoque, monkeypatch):
    """
    Achado verificando o plano de ação: a reserva só pode virar LIBERADA quando
    o estoque confirma. Marcá-la assim mesmo numa falha deixa vendas e estoque
    divergentes em silêncio — reserva presa lá, "liberada" aqui.
    """
    async def liberar_falha(empresa_id, produto_id, variante_id, quantidade, documento):
        return False

    monkeypatch.setattr(VendaService, "liberar_reserva_estoque", staticmethod(liberar_falha))

    venda, (produto,) = await _venda(db, StatusVenda.PEDIDO.value, [(True, False)])
    _, itens = await _recarregar(db, venda.id)
    reserva = await ReservaEstoqueVendaRepository.criar(
        db,
        venda_id=venda.id,
        item_venda_id=itens[0].id,
        produto_id=produto,
        variante_id=None,
        quantidade_reservada=Decimal("1"),
        status=StatusReserva.RESERVADA.value,
    )
    await db.commit()

    await VendaService.cancelar_venda(db, EMPRESA, venda.id, CancelarVendaRequest(motivo=MOTIVO))

    await db.refresh(reserva)
    venda, _ = await _recarregar(db, venda.id)
    assert reserva.status == StatusReserva.RESERVADA.value, (
        "marcou a reserva como liberada mesmo o estoque tendo recusado a liberação"
    )
    assert venda.reconciliacao_estoque_pendente is True, (
        "falha ao liberar reserva no cancelamento devia acender reconciliação"
    )


@pytest.mark.asyncio
async def test_rota_responde_503_quando_o_estorno_e_indeterminado(client, db, estoque):
    _, config = estoque
    config["estorno_ok"] = False
    venda, _ = await _venda(db, StatusVenda.SEPARADA.value, [(True, True)])

    resposta = await client.post(
        f"/vendas/{venda.id}/cancelar",
        json={"motivo": MOTIVO},
        headers={"X-Empresa-Id": str(EMPRESA)},
    )

    assert resposta.status_code == 503, resposta.text
    assert "Tente novamente" in resposta.json()["detail"]
