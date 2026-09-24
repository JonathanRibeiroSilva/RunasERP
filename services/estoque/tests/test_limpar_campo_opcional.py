"""Limpar um campo opcional do estoque chega ao banco.

`EstoqueRepository.atualizar` ignorava todo valor `None`, e o PATCH chega com
`None` tanto quando o campo não veio quanto quando veio vazio. As duas coisas
eram a mesma para o repositório, então apagar era impossível: o operador
limpava a localização de uma peça que mudou de prateleira, salvava, e o banco
continuava apontando para a prateleira antiga — sem erro e sem aviso.

Mesma armadilha do #96 em produtos, e antes dela do #69 e do #81. O conserto é
o mesmo: `exclude_unset` separa "não mandou" de "mandou vazio", e
`campos_gravaveis` segura só o null que a coluna recusa.

Os testes prendem os dois sentidos — o que veio vazio apaga, o que não veio não
encosta — porque perder qualquer um dos lados traz o bug de volta.
"""
import uuid

import pytest
import pytest_asyncio

from models.estoque import Estoque
from schemas.estoque import EstoqueUpdate
from services.estoque_service import EstoqueService

EMPRESA = 990_005


@pytest_asyncio.fixture
async def estoque(db):
    linha = Estoque(
        empresa_id=EMPRESA,
        produto_id=uuid.uuid4(),
        quantidade=10.0,
        quantidade_reservada=0.0,
        quantidade_disponivel=10.0,
        estoque_minimo=2.0,
        estoque_maximo=50.0,
        localizacao="Prateleira A1",
    )
    db.add(linha)
    await db.commit()
    return linha


@pytest.mark.asyncio
async def test_apagar_a_localizacao_chega_ao_banco(db, estoque):
    await EstoqueService.atualizar_estoque(
        db, EMPRESA, estoque.id, EstoqueUpdate(localizacao=None)
    )

    await db.refresh(estoque)
    assert estoque.localizacao is None, (
        f"a localização apagada continuou gravada como {estoque.localizacao!r}"
    )


@pytest.mark.asyncio
async def test_apagar_o_estoque_maximo_chega_ao_banco(db, estoque):
    """Tirar o teto é uma decisão: o alerta de excesso some junto."""
    await EstoqueService.atualizar_estoque(
        db, EMPRESA, estoque.id, EstoqueUpdate(estoque_maximo=None)
    )

    await db.refresh(estoque)
    assert estoque.estoque_maximo is None


@pytest.mark.asyncio
async def test_campo_que_nao_veio_no_patch_nao_e_tocado(db, estoque):
    """O outro lado da moeda: omitir não pode virar apagar."""
    await EstoqueService.atualizar_estoque(
        db, EMPRESA, estoque.id, EstoqueUpdate(estoque_minimo=3.0)
    )

    await db.refresh(estoque)
    assert estoque.estoque_minimo == 3.0
    assert estoque.localizacao == "Prateleira A1"
    assert estoque.estoque_maximo == 50.0


@pytest.mark.asyncio
async def test_vazio_em_campo_obrigatorio_nao_apaga_o_valor(db, estoque):
    """`estoque_minimo` é NOT NULL: o null é descartado antes do flush.

    Sem o descarte isto seria um IntegrityError que o serviço re-lança — 500 no
    PATCH, sem dizer qual campo. A chamada precisa devolver resposta.
    """
    resposta = await EstoqueService.atualizar_estoque(
        db, EMPRESA, estoque.id, EstoqueUpdate(estoque_minimo=None, localizacao="Prateleira B2")
    )

    assert resposta is not None
    await db.refresh(estoque)
    assert estoque.estoque_minimo == 2.0
    assert estoque.localizacao == "Prateleira B2", "o campo válido do mesmo PATCH não gravou"
