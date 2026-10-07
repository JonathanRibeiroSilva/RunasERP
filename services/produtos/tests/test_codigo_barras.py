"""O código de barras entra pela API e sai pela busca.

`codigo_barras` existia no model, mas nenhum schema de escrita o aceitava e o
filtro `busca` só casava nome: o único gravador era o seed, e colar um EAN na
busca devolvia zero. A leitura de código de barras na entrada de estoque
depende dos dois lados, então os dois ficam presos aqui.
"""
from decimal import Decimal

import pytest
import pytest_asyncio

from schemas.produtos import ProdutoCreate, ProdutoUpdate
from services.produtos import ProdutoService
from repositories.produtos import CategoriaRepository

EMPRESA = 991_003
OUTRA_EMPRESA = 991_004
EAN = "7894900011517"


@pytest_asyncio.fixture
async def produto(db):
    categoria = await CategoriaRepository(db).criar(empresa_id=EMPRESA, nome="Categoria")
    produto = await ProdutoService(db).criar_produto(
        EMPRESA,
        ProdutoCreate(
            empresa_id=EMPRESA,
            categoria_id=categoria.id,
            nome="Refrigerante",
            preco=Decimal("10.00"),
            custo=Decimal("4.00"),
            codigo_barras=EAN,
            sku="REF-001",
        ),
    )
    await db.commit()
    return produto


async def _buscar(db, termo, empresa=EMPRESA):
    itens, _ = await ProdutoService(db).listar_produtos(empresa, busca=termo)
    return itens


@pytest.mark.asyncio
async def test_criar_grava_codigo_de_barras_e_sku(produto):
    assert produto.codigo_barras == EAN
    assert produto.sku == "REF-001"


@pytest.mark.asyncio
async def test_patch_troca_e_apaga_o_codigo_de_barras(db, produto):
    service = ProdutoService(db)
    await service.atualizar_produto(EMPRESA, produto.id, ProdutoUpdate(codigo_barras="7891000100103"))
    await db.refresh(produto)
    assert produto.codigo_barras == "7891000100103"

    await service.atualizar_produto(EMPRESA, produto.id, ProdutoUpdate(codigo_barras=None))
    await db.refresh(produto)
    assert produto.codigo_barras is None


@pytest.mark.asyncio
async def test_busca_por_ean_exato_acha_o_produto(db, produto):
    assert [p.id for p in await _buscar(db, EAN)] == [produto.id]
    assert [p.id for p in await _buscar(db, "REF-001")] == [produto.id]


@pytest.mark.asyncio
async def test_busca_por_ean_parcial_nao_acha(db, produto):
    """EAN casa exato: um pedaço do número não pode listar produto."""
    assert await _buscar(db, EAN[:6]) == []


@pytest.mark.asyncio
async def test_busca_por_nome_continua_funcionando(db, produto):
    assert [p.id for p in await _buscar(db, "refri")] == [produto.id]


@pytest.mark.asyncio
async def test_ean_de_outra_empresa_nao_vaza(db, produto):
    assert await _buscar(db, EAN, empresa=OUTRA_EMPRESA) == []
