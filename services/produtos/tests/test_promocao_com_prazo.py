"""Promoção tem último dia, e o preço que vale é calculado num lugar só.

Duas coisas que andavam juntas e agora estão prendidas aqui.

A promoção não tinha prazo: preenchida uma vez, valia para sempre. Quem
esquecesse de tirar seguia dando desconto sem nada avisar — e o único jeito de
notar era conferir o cadastro produto a produto. A data de fim faz o
esquecimento acabar sozinho, sem job e sem ninguém lembrar.

E `preco_efetivo` é o que fecha a divergência entre o que a loja anuncia e o
que o carrinho cobra: a regra "promoção ou preço normal" morava no card em
TypeScript e no carrinho em Python ao mesmo tempo, e as duas se desencontraram.
Agora existe uma resposta só, e é esta.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
import pytest_asyncio

from models.produto import hoje_na_loja
from schemas.produtos import ProdutoCreate, ProdutoUpdate
from services.produtos import ProdutoService
from repositories.produtos import CategoriaRepository, ProdutoRepository

EMPRESA = 991_001
HOJE = hoje_na_loja()


@pytest_asyncio.fixture
async def categoria(db):
    categoria = await CategoriaRepository(db).criar(empresa_id=EMPRESA, nome="Categoria")
    await db.commit()
    return categoria


def _produto(categoria, **extras):
    return ProdutoCreate(
        empresa_id=EMPRESA,
        categoria_id=categoria.id,
        nome="Produto",
        preco=Decimal("10.00"),
        custo=Decimal("4.00"),
        **extras,
    )


# ------------------------------ o prazo ------------------------------

@pytest.mark.asyncio
async def test_promocao_sem_prazo_e_recusada(db, categoria):
    with pytest.raises(ValueError, match="data de término"):
        await ProdutoService(db).criar_produto(
            EMPRESA, _produto(categoria, preco_promocional=Decimal("8.00"))
        )


@pytest.mark.asyncio
async def test_produto_sem_promocao_nao_precisa_de_prazo(db, categoria):
    produto = await ProdutoService(db).criar_produto(EMPRESA, _produto(categoria))

    assert produto.promocao_fim is None
    assert produto.preco_efetivo == Decimal("10.00")


@pytest.mark.asyncio
async def test_pos_promocao_num_produto_existente_tambem_exige_prazo(db, categoria):
    servico = ProdutoService(db)
    produto = await servico.criar_produto(EMPRESA, _produto(categoria))
    await db.commit()

    with pytest.raises(ValueError, match="data de término"):
        await servico.atualizar_produto(
            EMPRESA, produto.id, ProdutoUpdate(preco_promocional=Decimal("8.00"))
        )


@pytest.mark.asyncio
async def test_prazo_ja_gravado_serve_para_um_preco_promocional_novo(db, categoria):
    """O PATCH só enxerga o que veio; o prazo que já está no banco continua valendo."""
    servico = ProdutoService(db)
    produto = await servico.criar_produto(
        EMPRESA,
        _produto(categoria, preco_promocional=Decimal("9.00"), promocao_fim=HOJE + timedelta(days=5)),
    )
    await db.commit()

    await servico.atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(preco_promocional=Decimal("7.00"))
    )

    await db.refresh(produto)
    assert produto.preco_efetivo == Decimal("7.00")


# --------------------------- o preço que vale ---------------------------

@pytest.mark.asyncio
async def test_promocao_vigente_e_o_preco_que_vale(db, categoria):
    produto = await ProdutoService(db).criar_produto(
        EMPRESA,
        _produto(categoria, preco_promocional=Decimal("8.00"), promocao_fim=HOJE + timedelta(days=1)),
    )

    assert produto.preco_efetivo == Decimal("8.00")
    assert produto.promocao_ativa is True


@pytest.mark.asyncio
async def test_o_ultimo_dia_ainda_e_dia_de_promocao(db, categoria):
    """"Vale até dia 30" tem que valer o dia 30 inteiro, no fuso do lojista."""
    produto = await ProdutoService(db).criar_produto(
        EMPRESA, _produto(categoria, preco_promocional=Decimal("8.00"), promocao_fim=HOJE)
    )

    assert produto.preco_efetivo == Decimal("8.00")


@pytest.mark.asyncio
async def test_promocao_vencida_volta_ao_preco_normal_sozinha(db, categoria):
    """O ponto do prazo: ninguém precisa lembrar de desligar."""
    produto = await ProdutoService(db).criar_produto(
        EMPRESA,
        _produto(categoria, preco_promocional=Decimal("8.00"), promocao_fim=HOJE - timedelta(days=1)),
    )

    assert produto.preco_efetivo == Decimal("10.00")
    assert produto.promocao_ativa is False
    assert produto.preco_promocional == Decimal("8.00"), (
        "o preço promocional foi apagado; ele fica gravado para o lojista reativar"
    )


@pytest.mark.asyncio
async def test_encerrar_a_promocao_e_por_a_data_no_passado(db, categoria):
    servico = ProdutoService(db)
    produto = await servico.criar_produto(
        EMPRESA,
        _produto(categoria, preco_promocional=Decimal("8.00"), promocao_fim=HOJE + timedelta(days=30)),
    )
    await db.commit()

    await servico.atualizar_produto(
        EMPRESA, produto.id, ProdutoUpdate(promocao_fim=HOJE - timedelta(days=1))
    )

    await db.refresh(produto)
    assert produto.preco_efetivo == Decimal("10.00")


@pytest.mark.asyncio
async def test_linha_anterior_a_esta_regra_nao_cobra_promocao(db, categoria):
    """A migration não faz backfill — é este comportamento que a torna segura.

    Linha gravada antes da coluna existir tem promoção e nenhum prazo. Sem data
    a promoção não vale, então o produto é cobrado pelo preço normal: a vitrine
    e o carrinho continuam concordando, que é a garantia que importa.
    """
    produto = await ProdutoRepository(db).criar(  # direto no repo: pula o service
        empresa_id=EMPRESA,
        categoria_id=categoria.id,
        nome="Legado",
        preco=Decimal("10.00"),
        custo=Decimal("4.00"),
        preco_promocional=Decimal("8.00"),
    )

    assert produto.promocao_fim is None
    assert produto.preco_efetivo == Decimal("10.00")
