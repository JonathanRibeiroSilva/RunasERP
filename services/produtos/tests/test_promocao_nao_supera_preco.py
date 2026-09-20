"""P6 — promoção não pode cobrar mais caro que o preço normal.

`preco_promocional` só validava `gt=0`. Nada o amarrava ao `preco`, então
gravar promoção acima do preço de venda era um POST — e a vitrine acredita:
`ProdutoCard` exibe o promocional no lugar do preço sempre que ele existe, e só
risca o "preço antigo" quando a promoção é menor. Promoção de R$ 20 num produto
de R$ 10 vira um aumento anunciado como desconto.

A regra vale nas duas direções e os testes cobrem as duas: subir a promoção
acima do preço, e baixar o preço abaixo de uma promoção já gravada. Fechar só o
primeiro lado deixaria a porta dos fundos aberta — cadastra a promoção certa,
baixa o preço depois.

Promoção igual ao preço passa de propósito: é o lojista decidindo não dar
desconto, e nenhuma tela mente por isso.
"""
from decimal import Decimal

import pytest
import pytest_asyncio

from schemas.produtos import ProdutoCreate, ProdutoUpdate
from services.produtos import ProdutoService
from repositories.produtos import CategoriaRepository, ProdutoRepository

EMPRESA = 990_901
PRECO = Decimal("10.00")


@pytest_asyncio.fixture
async def categoria(db):
    categoria = await CategoriaRepository(db).criar(empresa_id=EMPRESA, nome="Categoria")
    await db.commit()
    return categoria


def _novo(categoria, promocional):
    return ProdutoCreate(
        empresa_id=EMPRESA,
        categoria_id=categoria.id,
        nome="Produto",
        preco=PRECO,
        custo=Decimal("4.00"),
        preco_promocional=promocional,
    )


@pytest_asyncio.fixture
async def produto_em_promocao(db, categoria):
    """Produto de R$ 10 com promoção de R$ 8 — o caso saudável."""
    produto = await ProdutoService(db).criar_produto(
        EMPRESA, _novo(categoria, Decimal("8.00"))
    )
    await db.commit()
    return produto


# ----------------------------- no cadastro -----------------------------

@pytest.mark.asyncio
async def test_promocao_acima_do_preco_no_cadastro_e_recusada(db, categoria):
    with pytest.raises(ValueError, match="preço de venda"):
        await ProdutoService(db).criar_produto(EMPRESA, _novo(categoria, Decimal("12.00")))


@pytest.mark.asyncio
async def test_promocao_igual_ao_preco_e_aceita(db, categoria):
    """Desconto zero é decisão do lojista; promoção mais cara é que não."""
    produto = await ProdutoService(db).criar_produto(EMPRESA, _novo(categoria, PRECO))

    assert produto.preco_promocional == PRECO


# ------------------------- lado 1: subir a promoção -------------------------

@pytest.mark.asyncio
async def test_subir_a_promocao_acima_do_preco_e_recusado(db, produto_em_promocao):
    with pytest.raises(ValueError, match="preço de venda"):
        await ProdutoService(db).atualizar_produto(
            EMPRESA, produto_em_promocao.id,
            ProdutoUpdate(preco_promocional=Decimal("11.00")),
        )

    await db.refresh(produto_em_promocao)
    assert produto_em_promocao.preco_promocional == Decimal("8.00"), "recusou depois de gravar"


# ------------------------ lado 2: baixar o preço ------------------------

@pytest.mark.asyncio
async def test_baixar_o_preco_abaixo_da_promocao_e_recusado(db, produto_em_promocao):
    """A porta dos fundos: promoção válida no cadastro, preço derrubado depois."""
    with pytest.raises(ValueError, match="preço de venda"):
        await ProdutoService(db).atualizar_produto(
            EMPRESA, produto_em_promocao.id, ProdutoUpdate(preco=Decimal("6.00"))
        )

    await db.refresh(produto_em_promocao)
    assert produto_em_promocao.preco == PRECO


# --------------------------- porta da frente ---------------------------

@pytest.mark.asyncio
async def test_aprofundar_o_desconto_continua_passando(db, produto_em_promocao):
    await ProdutoService(db).atualizar_produto(
        EMPRESA, produto_em_promocao.id, ProdutoUpdate(preco_promocional=Decimal("7.00"))
    )

    await db.refresh(produto_em_promocao)
    assert produto_em_promocao.preco_promocional == Decimal("7.00")


@pytest.mark.asyncio
async def test_linha_legada_ainda_pode_ser_consertada(db, categoria):
    """
    A guarda é mesclada, então uma linha gravada antes dela existir (promoção
    acima do preço) reprova em qualquer PATCH. Tem que sobrar saída: arrumar a
    promoção para baixo, ou subir o preço até cobri-la. Sem isso a linha ficaria
    presa e o lojista sem como desfazer o estrago.
    """
    produto = await ProdutoRepository(db).criar(  # direto no repo: pula o service
        empresa_id=EMPRESA,
        categoria_id=categoria.id,
        nome="Legado",
        preco=PRECO,
        custo=Decimal("4.00"),
        preco_promocional=Decimal("20.00"),
    )
    await db.commit()

    await ProdutoService(db).atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(preco_promocional=Decimal("9.00"))
    )

    await db.refresh(produto)
    assert produto.preco_promocional == Decimal("9.00")
