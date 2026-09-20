"""Limpar um campo opcional chega ao banco.

`ProdutoRepository.atualizar` ignorava todo valor `None`, e o PATCH chega com
`None` tanto quando o campo não veio quanto quando veio vazio. As duas coisas
eram a mesma para o repositório, então apagar era impossível: o lojista limpava
a descrição ou o preço promocional, salvava, e o valor antigo continuava lá —
sem erro, sem aviso, e a tela mostrando o que ele acabou de apagar.

Doeu primeiro na promoção, que é dinheiro: sem poder apagar o preço
promocional, o único jeito de desligar uma promoção era mexer na data.

O conserto é o `exclude_unset` do pydantic, que separa as duas. Estes testes
prendem a separação nos dois sentidos — o que veio vazio apaga, o que não veio
não encosta — porque perder qualquer um dos lados traz o bug de volta.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
import pytest_asyncio

from models.produto import hoje_na_loja
from schemas.produtos import ProdutoCreate, ProdutoUpdate
from services.produtos import ProdutoService
from repositories.produtos import CategoriaRepository

EMPRESA = 991_002


@pytest_asyncio.fixture
async def produto(db):
    categoria = await CategoriaRepository(db).criar(empresa_id=EMPRESA, nome="Categoria")
    produto = await ProdutoService(db).criar_produto(
        EMPRESA,
        ProdutoCreate(
            empresa_id=EMPRESA,
            categoria_id=categoria.id,
            nome="Produto",
            descricao="Descrição original",
            preco=Decimal("10.00"),
            custo=Decimal("4.00"),
            preco_promocional=Decimal("8.00"),
            promocao_fim=hoje_na_loja() + timedelta(days=30),
        ),
    )
    await db.commit()
    return produto


@pytest.mark.asyncio
async def test_apagar_o_preco_promocional_desliga_a_promocao(db, produto):
    await ProdutoService(db).atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(preco_promocional=None)
    )

    await db.refresh(produto)
    assert produto.preco_promocional is None, "a promoção apagada continuou gravada"
    assert produto.preco_efetivo == Decimal("10.00")


@pytest.mark.asyncio
async def test_apagar_a_descricao_chega_ao_banco(db, produto):
    await ProdutoService(db).atualizar_produto(EMPRESA, produto.id, ProdutoUpdate(descricao=""))

    await db.refresh(produto)
    assert produto.descricao == ""


@pytest.mark.asyncio
async def test_campo_que_nao_veio_no_patch_nao_e_tocado(db, produto):
    """O outro lado da moeda: omitir não pode virar apagar."""
    await ProdutoService(db).atualizar_produto(EMPRESA, produto.id, ProdutoUpdate(nome="Nome novo"))

    await db.refresh(produto)
    assert produto.nome == "Nome novo"
    assert produto.descricao == "Descrição original"
    assert produto.preco_promocional == Decimal("8.00")
    assert produto.preco == Decimal("10.00")


@pytest.mark.asyncio
async def test_vazio_em_campo_obrigatorio_nao_apaga_o_valor(db, produto):
    """O schema aceita None em tudo para poder omitir; o banco não aceita em tudo.

    Ignorar é melhor que um IntegrityError sem explicação vindo do flush.
    """
    await ProdutoService(db).atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(nome=None, preco=None)
    )

    await db.refresh(produto)
    assert produto.nome == "Produto"
    assert produto.preco == Decimal("10.00")
