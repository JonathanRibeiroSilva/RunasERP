"""P5 — o markup da variante deixa de ser decorativo.

`Variante.calcular_preco_venda()` existia no model e ninguém chamava. Os três
números — `preco_custo`, `markup_pct`, `preco_venda` — chegavam digitados pelo
cliente, e a única checagem era `preco_venda >= preco_custo`. Uma variante podia
dizer "markup de 50%" e cobrar um preço que não correspondia a markup nenhum: a
tela mostra 50% na coluna do markup e o caixa cobra outro número, e nada no
sistema aponta a divergência.

`preco_venda` passa a ser derivado na escrita. Os testes prendem as duas metades
disso: que o valor enviado não manda mais (nem no POST nem no PATCH) e que o
recálculo acontece quando qualquer uma das duas entradas muda — inclusive num
PATCH que traz só o markup, caso em que o custo vem da linha gravada.
"""
from decimal import Decimal

import pytest
import pytest_asyncio

from schemas.produtos import VarianteCreate, VarianteUpdate
from services.produtos import VarianteService
from repositories.produtos import CategoriaRepository, ProdutoRepository

EMPRESA = 990_902
CUSTO = Decimal("10.00")


@pytest_asyncio.fixture
async def produto(db):
    categoria = await CategoriaRepository(db).criar(empresa_id=EMPRESA, nome="Categoria")
    produto = await ProdutoRepository(db).criar(
        empresa_id=EMPRESA,
        categoria_id=categoria.id,
        nome="Produto",
        preco=Decimal("15.00"),
        custo=CUSTO,
    )
    await db.commit()
    return produto


def _nova(produto, sku, markup, **extra):
    return VarianteCreate(
        empresa_id=EMPRESA,
        produto_id=produto.id,
        sku=sku,
        preco_custo=CUSTO,
        markup_pct=markup,
        **extra,
    )


@pytest_asyncio.fixture
async def variante(db, produto):
    """Custo R$ 10, markup 50% — preço de venda R$ 15."""
    variante = await VarianteService(db).criar_variante(
        EMPRESA, _nova(produto, "SKU-BASE", Decimal("50.00"))
    )
    await db.commit()
    return variante


# ------------------- o valor enviado não manda mais -------------------

@pytest.mark.asyncio
async def test_preco_venda_enviado_no_cadastro_e_ignorado(db, produto):
    """Antes isto gravava R$ 999 com markup de 50% escrito ao lado."""
    variante = await VarianteService(db).criar_variante(
        EMPRESA, _nova(produto, "SKU-1", Decimal("50.00"), preco_venda=Decimal("999.00"))
    )

    assert variante.preco_venda == Decimal("15.00")


@pytest.mark.asyncio
async def test_preco_venda_enviado_no_patch_e_ignorado(db, variante):
    await VarianteService(db).atualizar_variante(
        EMPRESA, variante.id, VarianteUpdate(preco_venda=Decimal("999.00"))
    )

    await db.refresh(variante)
    assert variante.preco_venda == Decimal("15.00")


# --------------------------- o recálculo ---------------------------

@pytest.mark.asyncio
async def test_patch_so_do_markup_recalcula_com_o_custo_gravado(db, variante):
    """O PATCH traz só o markup; o custo sai da linha, sem código de merge."""
    await VarianteService(db).atualizar_variante(
        EMPRESA, variante.id, VarianteUpdate(markup_pct=Decimal("100.00"))
    )

    await db.refresh(variante)
    assert variante.preco_custo == CUSTO
    assert variante.preco_venda == Decimal("20.00")


@pytest.mark.asyncio
async def test_patch_so_do_custo_recalcula_com_o_markup_gravado(db, variante):
    await VarianteService(db).atualizar_variante(
        EMPRESA, variante.id, VarianteUpdate(preco_custo=Decimal("20.00"))
    )

    await db.refresh(variante)
    assert variante.markup_pct == Decimal("50.00")
    assert variante.preco_venda == Decimal("30.00")


@pytest.mark.asyncio
async def test_patch_de_ativo_nao_mexe_no_preco(db, variante):
    """Desativar variante não é motivo para o preço dela mudar."""
    await VarianteService(db).atualizar_variante(
        EMPRESA, variante.id, VarianteUpdate(ativo=False)
    )

    await db.refresh(variante)
    assert variante.preco_venda == Decimal("15.00")


# -------------------------- o arredondamento --------------------------

@pytest.mark.asyncio
async def test_meio_centavo_sobe_e_memoria_bate_com_o_disco(db, produto):
    """
    R$ 1,00 com 12,5% dá R$ 1,125 — metade exata do centavo. A coluna é
    `Numeric(10, 2)`: ROUND_HALF_UP dá 1,13, o padrão do Python
    (ROUND_HALF_EVEN) daria 1,12, e o Postgres gravaria 1,13 de qualquer jeito.
    O `refresh` é o teste de verdade: prova que o número que a rota devolve
    depois do POST é o mesmo que ficou no disco.
    """
    variante = await VarianteService(db).criar_variante(
        EMPRESA,
        VarianteCreate(
            empresa_id=EMPRESA,
            produto_id=produto.id,
            sku="SKU-CENTAVO",
            preco_custo=Decimal("1.00"),
            markup_pct=Decimal("12.50"),
        ),
    )
    assert variante.preco_venda == Decimal("1.13")

    await db.refresh(variante)
    assert variante.preco_venda == Decimal("1.13")


# --------------------------- porta da frente ---------------------------

@pytest.mark.asyncio
async def test_cadastro_sem_enviar_preco_venda(db, produto):
    """O corpo que o schema agora promete: só custo e markup."""
    variante = await VarianteService(db).criar_variante(
        EMPRESA, _nova(produto, "SKU-MINIMO", Decimal("25.00"))
    )

    assert variante.preco_venda == Decimal("12.50")


@pytest.mark.asyncio
async def test_markup_zero_vende_pelo_custo(db, produto):
    """
    O limite que a checagem removida (`preco_venda < preco_custo`) guardava.
    Markup 0 é `ge=0` no schema, então é pedido legítimo: margem zero é decisão
    do lojista. Derivado, o preço nunca cai abaixo do custo — a garantia virou
    estrutural em vez de conferida.
    """
    variante = await VarianteService(db).criar_variante(
        EMPRESA, _nova(produto, "SKU-ZERO", Decimal("0"))
    )

    assert variante.preco_venda == CUSTO
