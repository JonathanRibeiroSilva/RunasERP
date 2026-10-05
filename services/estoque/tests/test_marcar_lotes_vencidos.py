"""
E4 (Onda 6): `marcar_vencidos` existia desde antes deste plano sem nenhum
chamador — um lote com `data_validade` passada ficava ATIVO para sempre. O job
(`jobs/marcar_lotes_vencidos.py`) usa seu próprio engine fora do request, por
isso não dá para testar o job em si com a fixture `db` — só a lógica que ele
chama, igual o resto dos jobs deste repo.
"""
import uuid
from datetime import date, timedelta

import pytest

from models.estoque import Estoque, Lote, StatusLote
from repositories.estoque_repository import LoteRepository

EMPRESA = 990_501
OUTRA_EMPRESA = 990_502


async def _lote(db, empresa_id, status, data_validade):
    estoque = Estoque(
        empresa_id=empresa_id, produto_id=uuid.uuid4(),
        quantidade=10.0, quantidade_reservada=0.0, quantidade_disponivel=10.0,
    )
    db.add(estoque)
    await db.flush()
    lote = Lote(
        empresa_id=empresa_id, estoque_id=estoque.id, codigo=f"L-{uuid.uuid4().hex[:8]}",
        quantidade=10.0, quantidade_inicial=10.0, status=status,
        data_validade=data_validade,
    )
    db.add(lote)
    await db.commit()
    return lote


@pytest.mark.asyncio
async def test_marca_vencido_so_o_lote_ativo_com_validade_passada(db):
    ontem = date.today() - timedelta(days=1)
    amanha = date.today() + timedelta(days=1)

    vencido = await _lote(db, EMPRESA, StatusLote.ATIVO.value, ontem)
    dentro_do_prazo = await _lote(db, EMPRESA, StatusLote.ATIVO.value, amanha)
    ja_bloqueado = await _lote(db, EMPRESA, StatusLote.BLOQUEADO.value, ontem)

    count = await LoteRepository.marcar_vencidos(db, EMPRESA)
    await db.commit()

    assert count == 1
    await db.refresh(vencido)
    await db.refresh(dentro_do_prazo)
    await db.refresh(ja_bloqueado)
    assert vencido.status == StatusLote.VENCIDO.value
    assert dentro_do_prazo.status == StatusLote.ATIVO.value, "ainda não venceu"
    assert ja_bloqueado.status == StatusLote.BLOQUEADO.value, (
        "quarentena não muda sozinha — marcar vencido não pode desfazer bloqueio"
    )


@pytest.mark.asyncio
async def test_marcar_vencidos_e_isolado_por_empresa(db):
    ontem = date.today() - timedelta(days=1)
    lote_outra_empresa = await _lote(db, OUTRA_EMPRESA, StatusLote.ATIVO.value, ontem)

    count = await LoteRepository.marcar_vencidos(db, EMPRESA)
    await db.commit()

    assert count == 0
    await db.refresh(lote_outra_empresa)
    assert lote_outra_empresa.status == StatusLote.ATIVO.value


@pytest.mark.asyncio
async def test_empresas_com_lote_vencido_encontra_so_quem_tem(db):
    ontem = date.today() - timedelta(days=1)
    amanha = date.today() + timedelta(days=1)

    await _lote(db, EMPRESA, StatusLote.ATIVO.value, ontem)
    await _lote(db, OUTRA_EMPRESA, StatusLote.ATIVO.value, amanha)  # não vencido

    empresas = await LoteRepository.empresas_com_lote_vencido(db)

    assert EMPRESA in empresas
    assert OUTRA_EMPRESA not in empresas
