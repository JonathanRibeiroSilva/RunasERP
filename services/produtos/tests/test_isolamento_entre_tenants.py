"""P2+P3 — o id de outro tenant não serve para nada.

`loja_online_config`, `loja_online_fotos` e `fornecedor_produto` não têm coluna
`empresa_id`: quem tem dono é o produto. Os métodos de serviço recebiam
`empresa_id` e o descartavam, buscando a linha só pelo id — então um id
adivinhado (ou vazado numa resposta) de outra loja podia ser lido, editado e
apagado. Publicar produto alheio na própria loja era um PATCH.

A guarda é um JOIN em `Produto.empresa_id`, e mora no `obter_por_id` de cada
repositório, não nos chamadores: `atualizar` e `deletar` saem de lá, então
fechar o getter fecha os três.

Os testes atacam pelo service, que é onde `empresa_id` entra vindo da rota.
"""
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio

from schemas.produtos import (
    FornecedorProdutoCreate,
    FornecedorProdutoUpdate,
    LojaOnlineConfigCreate,
    LojaOnlineConfigUpdate,
    LojaOnlineFotoCreate,
    LojaOnlineFotoUpdate,
)
from services.produtos import FornecedorProdutoService, LojaOnlineService
from repositories.produtos import CategoriaRepository, FornecedorRepository, ProdutoRepository

DONO = 990_701
INTRUSO = 990_702


async def _produto(db, empresa_id: int):
    categoria = await CategoriaRepository(db).criar(empresa_id=empresa_id, nome="Categoria")
    return await ProdutoRepository(db).criar(
        empresa_id=empresa_id,
        categoria_id=categoria.id,
        nome="Produto",
        preco=Decimal("10.00"),
        custo=Decimal("5.00"),
    )


@pytest_asyncio.fixture
async def config_do_dono(db):
    """Config de loja online de um produto do DONO."""
    produto = await _produto(db, DONO)
    config = await LojaOnlineService(db).criar_config(
        DONO, LojaOnlineConfigCreate(produto_id=produto.id, visivel=False)
    )
    await db.commit()
    return config


@pytest_asyncio.fixture
async def foto_do_dono(db):
    produto = await _produto(db, DONO)
    foto = await LojaOnlineService(db).adicionar_foto(
        DONO, LojaOnlineFotoCreate(produto_id=produto.id, url="https://exemplo/original.jpg")
    )
    await db.commit()
    return foto


@pytest_asyncio.fixture
async def vinculo_do_dono(db):
    produto = await _produto(db, DONO)
    fornecedor = await FornecedorRepository(db).criar(empresa_id=DONO, nome="Fornecedor")
    vinculo = await FornecedorProdutoService(db).vincular_fornecedor(
        DONO,
        FornecedorProdutoCreate(
            fornecedor_id=fornecedor.id,
            produto_id=produto.id,
            preco_fornecedor=Decimal("7.00"),
            codigo_fornecedor="ORIGINAL",
        ),
    )
    await db.commit()
    return vinculo


# ----------------------------- P2: loja online -----------------------------

@pytest.mark.asyncio
async def test_intruso_nao_publica_produto_alheio(db, config_do_dono):
    with pytest.raises(ValueError):
        await LojaOnlineService(db).atualizar_config(
            INTRUSO, config_do_dono.id, LojaOnlineConfigUpdate(visivel=True, destaque=True)
        )

    await db.refresh(config_do_dono)
    assert config_do_dono.visivel is False, "produto de outra loja foi publicado por um PATCH"
    assert config_do_dono.destaque is False


@pytest.mark.asyncio
async def test_dono_continua_publicando_o_proprio(db, config_do_dono):
    """A guarda não pode ter fechado a porta de quem é de casa."""
    await LojaOnlineService(db).atualizar_config(
        DONO, config_do_dono.id, LojaOnlineConfigUpdate(visivel=True)
    )

    await db.refresh(config_do_dono)
    assert config_do_dono.visivel is True


@pytest.mark.asyncio
async def test_intruso_nao_troca_a_foto_alheia(db, foto_do_dono):
    with pytest.raises(ValueError):
        await LojaOnlineService(db).atualizar_foto(
            INTRUSO, foto_do_dono.id, LojaOnlineFotoUpdate(url="https://intruso/trocada.jpg")
        )

    await db.refresh(foto_do_dono)
    assert foto_do_dono.url == "https://exemplo/original.jpg"


@pytest.mark.asyncio
async def test_intruso_nao_apaga_a_foto_alheia(db, foto_do_dono):
    apagou = await LojaOnlineService(db).deletar_foto(INTRUSO, foto_do_dono.id)

    assert apagou is False, "foto de outra loja apagada"
    await db.refresh(foto_do_dono)
    assert foto_do_dono.url == "https://exemplo/original.jpg"


# -------------------------- P3: fornecedor-produto --------------------------

@pytest.mark.asyncio
async def test_intruso_nao_le_o_custo_do_concorrente(db, vinculo_do_dono):
    """O preço de compra é o dado mais sensível do cadastro de fornecedor."""
    with pytest.raises(ValueError):
        await FornecedorProdutoService(db).obter_vinculo(INTRUSO, vinculo_do_dono.id)


@pytest.mark.asyncio
async def test_intruso_nao_edita_o_vinculo_alheio(db, vinculo_do_dono):
    with pytest.raises(ValueError):
        await FornecedorProdutoService(db).atualizar_vinculo(
            INTRUSO,
            vinculo_do_dono.id,
            FornecedorProdutoUpdate(preco_fornecedor=Decimal("1.00"), codigo_fornecedor="INTRUSO"),
        )

    await db.refresh(vinculo_do_dono)
    assert vinculo_do_dono.preco_fornecedor == Decimal("7.00")
    assert vinculo_do_dono.codigo_fornecedor == "ORIGINAL"


@pytest.mark.asyncio
async def test_intruso_nao_apaga_o_vinculo_alheio(db, vinculo_do_dono):
    with pytest.raises(ValueError):
        await FornecedorProdutoService(db).deletar_vinculo(INTRUSO, vinculo_do_dono.id)

    await db.refresh(vinculo_do_dono)
    assert vinculo_do_dono.codigo_fornecedor == "ORIGINAL"


@pytest.mark.asyncio
async def test_dono_continua_editando_o_proprio_vinculo(db, vinculo_do_dono):
    await FornecedorProdutoService(db).atualizar_vinculo(
        DONO, vinculo_do_dono.id, FornecedorProdutoUpdate(preco_fornecedor=Decimal("8.00"))
    )

    await db.refresh(vinculo_do_dono)
    assert vinculo_do_dono.preco_fornecedor == Decimal("8.00")


@pytest.mark.asyncio
async def test_id_inexistente_nao_vira_erro_diferente(db):
    """Mesma resposta para 'não é seu' e 'não existe' — senão o erro vira oráculo."""
    with pytest.raises(ValueError):
        await FornecedorProdutoService(db).obter_vinculo(DONO, uuid.uuid4())
