"""Limpar um campo opcional de um pedido chega ao banco.

`VendaRepository.atualizar` ignorava todo valor `None`. Apagar a observação de
um pedido — "entregar à tarde" que deixou de valer — não chegava ao banco, e a
observação velha seguia impressa para quem separa e para quem entrega.

O desconto tinha o mesmo problema e foi contornado no serviço, escrevendo
direto na instância em vez de passar pelo repositório (ver o comentário que saiu
de `atualizar_venda`). O contorno tratava um caso; a causa era do repositório e
valia para todos os campos.

Mesma armadilha do #96 em produtos. `exclude_unset` separa "não mandou" de
"mandou vazio"; `campos_gravaveis` segura só o null que a coluna recusa.
"""
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio

from models.venda import StatusVenda, TipoEntrega, Venda
from repositories.venda_repository import VendaRepository
from schemas.venda import VendaUpdate
from services.venda_service import VendaService

EMPRESA = 990_402


@pytest_asyncio.fixture
async def venda(db):
    linha = await VendaRepository.criar(
        db,
        empresa_id=EMPRESA,
        numero_venda=f"L-{uuid.uuid4().hex[:8]}",
        subtotal=Decimal("20"),
        valor_total=Decimal("20"),
        status=StatusVenda.PEDIDO.value,
        tipo_entrega=TipoEntrega.RETIRADA.value,
        observacao="entregar à tarde",
        cliente_id=uuid.uuid4(),
        desconto_valor=Decimal("0"),
    )
    await db.commit()
    return linha


async def _recarregar(db, venda_id):
    linha = await db.get(Venda, venda_id)
    await db.refresh(linha)
    return linha


@pytest.mark.asyncio
async def test_apagar_a_observacao_chega_ao_banco(db, venda):
    await VendaService.atualizar_venda(db, EMPRESA, venda.id, VendaUpdate(observacao=None))

    assert (await _recarregar(db, venda.id)).observacao is None, (
        "a observação apagada continuou impressa no pedido"
    )


@pytest.mark.asyncio
async def test_campo_que_nao_veio_no_patch_nao_e_tocado(db, venda):
    """O outro lado da moeda: omitir não pode virar apagar."""
    cliente_original = venda.cliente_id

    await VendaService.atualizar_venda(
        db, EMPRESA, venda.id, VendaUpdate(tipo_entrega=TipoEntrega.DELIVERY)
    )

    atual = await _recarregar(db, venda.id)
    assert atual.tipo_entrega == TipoEntrega.DELIVERY.value
    assert atual.observacao == "entregar à tarde"
    assert atual.cliente_id == cliente_original


@pytest.mark.asyncio
async def test_vazio_em_campo_obrigatorio_nao_apaga_o_valor(db, venda):
    """`tipo_entrega` é NOT NULL: o null é descartado antes do flush.

    Sem o descarte seria um IntegrityError sem dizer qual campo. O outro campo
    do mesmo PATCH precisa gravar.
    """
    await VendaService.atualizar_venda(
        db, EMPRESA, venda.id, VendaUpdate(tipo_entrega=None, observacao="retirar 9h")
    )

    atual = await _recarregar(db, venda.id)
    assert atual.tipo_entrega == TipoEntrega.RETIRADA.value
    assert atual.observacao == "retirar 9h", "o campo válido do mesmo PATCH não gravou"
