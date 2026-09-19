"""Saída manual por lote: BLOQUEADO não sai; VENCIDO sai.

As duas metades importam. BLOQUEADO é quarentena — o lote está retido e mexer
nele desfaz a retenção. VENCIDO precisa sair: é por esta saída que se registra o
descarte, e a venda não passa por lote nenhum (a baixa de venda não lê a tabela
de lotes). Bloquear o vencido, que parece o conserto óbvio, deixaria o estoque
contando mercadoria que foi para o lixo.
"""
import uuid

import pytest

from models.estoque import Estoque, Lote, StatusLote
from schemas.estoque import SaidaEstoqueRequest
from services.estoque_service import EstoqueService

EMPRESA = 990_002


async def _estoque_com_lote(db, status):
    estoque = Estoque(
        empresa_id=EMPRESA, produto_id=uuid.uuid4(),
        quantidade=10.0, quantidade_reservada=0.0, quantidade_disponivel=10.0,
    )
    db.add(estoque)
    await db.flush()
    lote = Lote(
        empresa_id=EMPRESA, estoque_id=estoque.id, codigo=f"L-{status}",
        quantidade=10.0, quantidade_inicial=10.0, status=status,
    )
    db.add(lote)
    # commit: o serviço dá rollback no erro, e sem isto o rollback levaria junto
    # o que o teste montou. A fixture `db` desfaz tudo no fim de qualquer jeito.
    await db.commit()
    return estoque, lote


def _saida(estoque, lote):
    return SaidaEstoqueRequest(
        empresa_id=EMPRESA, produto_id=estoque.produto_id, quantidade=3.0,
        lote_id=lote.id, motivo="descarte",
    )


@pytest.mark.asyncio
async def test_lote_bloqueado_nao_sai(db):
    estoque, lote = await _estoque_com_lote(db, StatusLote.BLOQUEADO.value)

    with pytest.raises(ValueError, match="bloqueado"):
        await EstoqueService.saida_estoque(db, EMPRESA, _saida(estoque, lote))

    await db.refresh(estoque)
    await db.refresh(lote)
    assert (estoque.quantidade, lote.quantidade) == (10.0, 10.0), "o lote em quarentena foi mexido"


@pytest.mark.asyncio
async def test_lote_vencido_sai_porque_e_o_descarte(db):
    estoque, lote = await _estoque_com_lote(db, StatusLote.VENCIDO.value)

    resposta = await EstoqueService.saida_estoque(db, EMPRESA, _saida(estoque, lote))

    await db.refresh(lote)
    assert resposta.quantidade == 7.0, "sem esta saída o descarte do vencido não tem como ser registrado"
    assert lote.quantidade == 7.0


@pytest.mark.asyncio
async def test_lote_ativo_sai(db):
    estoque, lote = await _estoque_com_lote(db, StatusLote.ATIVO.value)

    resposta = await EstoqueService.saida_estoque(db, EMPRESA, _saida(estoque, lote))

    assert resposta.quantidade == 7.0
