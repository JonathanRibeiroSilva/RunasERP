"""P4 — não dá para vender por menos do que se paga ao fornecedor.

O vínculo fornecedor-produto só checava `preco_fornecedor > 0`. Nada olhava
para o preço de venda, então cadastrar um fornecedor mais caro que o produto
era prejuízo garantido em cada unidade vendida — e o cadastro do produto não
pegava isso, porque a guarda de lá compara com `Produto.custo`, que é digitado
à mão e nada sincroniza com o fornecedor.

A regra vale nas duas direções, e os testes cobrem as duas: subir o preço do
fornecedor acima da venda, e baixar a venda abaixo de um fornecedor já
cadastrado. Fechar só o primeiro lado deixaria a porta dos fundos aberta —
cadastra barato, baixa o preço depois.
"""
from decimal import Decimal

import pytest
import pytest_asyncio

from schemas.produtos import FornecedorProdutoCreate, FornecedorProdutoUpdate, ProdutoUpdate
from services.produtos import FornecedorProdutoService, ProdutoService
from repositories.produtos import (
    CategoriaRepository,
    FornecedorProdutoRepository,
    FornecedorRepository,
    ProdutoRepository,
)

EMPRESA = 990_801
VENDA = Decimal("10.00")


@pytest_asyncio.fixture
async def cenario(db):
    """Produto vendido a R$ 10 e um fornecedor, ainda sem vínculo."""
    categoria = await CategoriaRepository(db).criar(empresa_id=EMPRESA, nome="Categoria")
    produto = await ProdutoRepository(db).criar(
        empresa_id=EMPRESA,
        categoria_id=categoria.id,
        nome="Produto",
        preco=VENDA,
        custo=Decimal("4.00"),
    )
    fornecedor = await FornecedorRepository(db).criar(empresa_id=EMPRESA, nome="Fornecedor")
    await db.commit()
    return produto, fornecedor


def _vinculo(produto, fornecedor, preco):
    return FornecedorProdutoCreate(
        fornecedor_id=fornecedor.id, produto_id=produto.id, preco_fornecedor=preco
    )


# ---------------------- lado 1: o preço do fornecedor ----------------------

@pytest.mark.asyncio
async def test_fornecedor_mais_caro_que_a_venda_e_recusado(db, cenario):
    produto, fornecedor = cenario

    with pytest.raises(ValueError, match="preço de venda"):
        await FornecedorProdutoService(db).vincular_fornecedor(
            EMPRESA, _vinculo(produto, fornecedor, Decimal("12.00"))
        )


@pytest.mark.asyncio
async def test_fornecedor_no_mesmo_preco_da_venda_e_aceito(db, cenario):
    """Margem zero é decisão do lojista; prejuízo é que não."""
    produto, fornecedor = cenario

    vinculo = await FornecedorProdutoService(db).vincular_fornecedor(
        EMPRESA, _vinculo(produto, fornecedor, VENDA)
    )

    assert vinculo.preco_fornecedor == VENDA


@pytest.mark.asyncio
async def test_reajuste_do_fornecedor_acima_da_venda_e_recusado(db, cenario):
    produto, fornecedor = cenario
    servico = FornecedorProdutoService(db)
    vinculo = await servico.vincular_fornecedor(EMPRESA, _vinculo(produto, fornecedor, Decimal("6.00")))
    await db.commit()

    with pytest.raises(ValueError, match="preço de venda"):
        await servico.atualizar_vinculo(
            EMPRESA, vinculo.id, FornecedorProdutoUpdate(preco_fornecedor=Decimal("11.00"))
        )

    await db.refresh(vinculo)
    assert vinculo.preco_fornecedor == Decimal("6.00"), "recusou depois de já ter gravado"


# ------------------- lado 2: a baixa do preço de venda -------------------

@pytest.mark.asyncio
async def test_baixar_a_venda_abaixo_do_fornecedor_e_recusado(db, cenario):
    """A porta dos fundos: cadastra barato, baixa o preço depois."""
    produto, fornecedor = cenario
    await FornecedorProdutoService(db).vincular_fornecedor(
        EMPRESA, _vinculo(produto, fornecedor, Decimal("8.00"))
    )
    await db.commit()

    with pytest.raises(ValueError, match="preço de venda"):
        await ProdutoService(db).atualizar_produto(
            EMPRESA, produto.id, ProdutoUpdate(preco=Decimal("5.00"))
        )

    await db.refresh(produto)
    assert produto.preco == VENDA


@pytest.mark.asyncio
async def test_baixar_ate_o_preco_do_fornecedor_e_aceito(db, cenario):
    produto, fornecedor = cenario
    await FornecedorProdutoService(db).vincular_fornecedor(
        EMPRESA, _vinculo(produto, fornecedor, Decimal("8.00"))
    )
    await db.commit()

    await ProdutoService(db).atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(preco=Decimal("8.00"))
    )

    await db.refresh(produto)
    assert produto.preco == Decimal("8.00")


@pytest.mark.asyncio
async def test_vinculo_inativo_nao_trava_a_baixa(db, cenario):
    """Fornecedor desativado não é de quem se compra; não pode segurar preço."""
    produto, fornecedor = cenario
    servico = FornecedorProdutoService(db)
    vinculo = await servico.vincular_fornecedor(EMPRESA, _vinculo(produto, fornecedor, Decimal("8.00")))
    await servico.atualizar_vinculo(EMPRESA, vinculo.id, FornecedorProdutoUpdate(ativo=False))
    await db.commit()

    await ProdutoService(db).atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(preco=Decimal("5.00"))
    )

    await db.refresh(produto)
    assert produto.preco == Decimal("5.00")


@pytest.mark.asyncio
async def test_editar_outro_campo_nao_esbarra_em_vinculo_legado(db, cenario):
    """
    Linha antiga já viola a regra (gravada antes desta guarda existir).
    Renomear o produto não pode ficar impossível por causa dela — a consulta
    só acontece quando o preço está mudando.
    """
    produto, fornecedor = cenario
    await FornecedorProdutoRepository(db).criar(  # direto no repo: pula o service
        fornecedor_id=fornecedor.id, produto_id=produto.id, preco_fornecedor=Decimal("99.00")
    )
    await db.commit()

    await ProdutoService(db).atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(nome="Nome novo")
    )

    await db.refresh(produto)
    assert produto.nome == "Nome novo"
