"""Editar o desconto de uma venda muda o valor cobrado.

O desconto era gravado e só: subtotal e valor_total continuavam os da criação.
A confirmação valida o pagamento contra valor_total, então a venda aparecia com
desconto na tela e cobrava o valor cheio.

Dois detalhes que os testes prendem, porque some fácil num refactor:
- remover o desconto precisa chegar ao banco. VendaRepository.atualizar pula
  valores None, então `desconto_tipo=None` passado por **dados seria ignorado e a
  venda ficaria "PERCENTUAL de 0";
- a validação do desconto mora no service, não no VendaUpdate: no schema só se vê
  o que veio no PATCH, e um valor sem tipo pode ser um valor novo sobre um tipo
  que já estava gravado.
"""
import uuid
from decimal import Decimal

import pytest

from models.venda import StatusVenda, TipoDesconto, Venda
from repositories.venda_repository import ItemVendaRepository, VendaRepository
from schemas.venda import VendaUpdate
from services.venda_service import VendaService

EMPRESA = 990_401


async def _venda(db, desconto_tipo=None, desconto_valor=Decimal("0")):
    """Venda PEDIDO com dois itens de R$ 10 — subtotal 20."""
    venda = await VendaRepository.criar(
        db,
        empresa_id=EMPRESA,
        numero_venda=f"T-{uuid.uuid4().hex[:8]}",
        subtotal=Decimal("20"),
        valor_total=Decimal("20") - desconto_valor if desconto_tipo == TipoDesconto.VALOR_FIXO.value else Decimal("20"),
        status=StatusVenda.PEDIDO.value,
        desconto_tipo=desconto_tipo,
        desconto_valor=desconto_valor,
    )
    for _ in range(2):
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
    return venda


async def _recarregar(db, venda_id):
    venda = await db.get(Venda, venda_id)
    await db.refresh(venda)
    return venda


@pytest.mark.asyncio
async def test_desconto_percentual_recalcula_o_valor_cobrado(db):
    venda = await _venda(db)

    await VendaService.atualizar_venda(
        db, EMPRESA, venda.id,
        VendaUpdate(desconto_tipo=TipoDesconto.PERCENTUAL, desconto_valor=Decimal("10")),
    )

    venda = await _recarregar(db, venda.id)
    assert venda.valor_total == Decimal("18"), (
        f"20 com 10% de desconto deveria cobrar 18, cobra {venda.valor_total}"
    )
    assert venda.subtotal == Decimal("20")


@pytest.mark.asyncio
async def test_desconto_em_valor_fixo_recalcula_o_valor_cobrado(db):
    venda = await _venda(db)

    await VendaService.atualizar_venda(
        db, EMPRESA, venda.id,
        VendaUpdate(desconto_tipo=TipoDesconto.VALOR_FIXO, desconto_valor=Decimal("5")),
    )

    assert (await _recarregar(db, venda.id)).valor_total == Decimal("15")


@pytest.mark.asyncio
async def test_remover_o_desconto_volta_ao_valor_cheio(db):
    venda = await _venda(db, desconto_tipo=TipoDesconto.VALOR_FIXO.value, desconto_valor=Decimal("5"))

    await VendaService.atualizar_venda(
        db, EMPRESA, venda.id,
        VendaUpdate(desconto_tipo=None, desconto_valor=Decimal("0")),
    )

    venda = await _recarregar(db, venda.id)
    assert venda.valor_total == Decimal("20")
    assert venda.desconto_tipo is None, (
        f"o tipo do desconto removido ficou gravado como {venda.desconto_tipo!r} com valor 0"
    )


@pytest.mark.asyncio
async def test_editar_outro_campo_nao_mexe_no_total(db):
    venda = await _venda(db, desconto_tipo=TipoDesconto.VALOR_FIXO.value, desconto_valor=Decimal("5"))
    total_antes = venda.valor_total

    await VendaService.atualizar_venda(db, EMPRESA, venda.id, VendaUpdate(observacao="entregar à tarde"))

    venda = await _recarregar(db, venda.id)
    assert venda.valor_total == total_antes
    assert venda.observacao == "entregar à tarde"


@pytest.mark.asyncio
async def test_percentual_acima_de_cem_e_recusado(db):
    venda = await _venda(db)

    with pytest.raises(ValueError, match="100%"):
        await VendaService.atualizar_venda(
            db, EMPRESA, venda.id,
            VendaUpdate(desconto_tipo=TipoDesconto.PERCENTUAL, desconto_valor=Decimal("120")),
        )


@pytest.mark.asyncio
async def test_valor_sem_tipo_nenhum_e_recusado(db):
    venda = await _venda(db)
    venda_id = venda.id  # o rollback do serviço expira as instâncias

    with pytest.raises(ValueError, match="desconto_tipo"):
        await VendaService.atualizar_venda(db, EMPRESA, venda_id, VendaUpdate(desconto_valor=Decimal("5")))


@pytest.mark.asyncio
async def test_valor_novo_sobre_tipo_ja_gravado_e_aceito(db):
    """O schema recusaria: só enxerga o PATCH. O service mescla com o que está no banco."""
    venda = await _venda(db, desconto_tipo=TipoDesconto.VALOR_FIXO.value, desconto_valor=Decimal("5"))

    await VendaService.atualizar_venda(db, EMPRESA, venda.id, VendaUpdate(desconto_valor=Decimal("8")))

    assert (await _recarregar(db, venda.id)).valor_total == Decimal("12")
