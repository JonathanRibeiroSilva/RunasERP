"""A venda cobra o preço anunciado, promoção incluída.

`preco_promocional` não aparecia uma única vez no serviço de vendas: o carrinho
e o criar_venda liam `produto['preco']` cru, enquanto o card da loja exibia a
promoção. A vitrine anunciava R$ 8 e o pedido era gravado por R$ 10 — cobrar
diferente do anunciado, não bug de tela.

Agora quem resolve promoção é o catálogo, num campo só (`preco_efetivo`), e
vendas lê esse campo pelo `preco_do_catalogo`. O que estes testes prendem é que
a venda não volte a ler o preço na mão: é assim que as duas pontas se
desencontram de novo.

HTTP para produtos e estoque é substituído; o banco é o Postgres de verdade.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from models.venda import ItemVenda, Venda
from services.estoque_resultado import ResultadoBaixaEstoque
from services.venda_service import VendaService

EMPRESA = 990_103

# Como o serviço de produtos responde: `preco` é o de tabela, `preco_efetivo` é
# o que vale hoje. Iguais quando não há promoção vigente.
EM_PROMOCAO = {"preco": "10.00", "preco_efetivo": "8.00", "nome": "Produto", "sku": "SKU"}
SEM_PROMOCAO = {"preco": "10.00", "preco_efetivo": "10.00", "nome": "Produto", "sku": "SKU"}
CATALOGO_ANTIGO = {"preco": "10.00", "nome": "Produto", "sku": "SKU"}


@pytest.fixture
def catalogo(monkeypatch):
    """Substitui o serviço de produtos; o teste escolhe o que ele responde."""
    resposta = {"produto": dict(SEM_PROMOCAO)}

    async def produto(produto_id, variante_id, empresa_id):
        return resposta["produto"]

    async def reservar(empresa_id, produto_id, variante_id, quantidade, documento):
        return ResultadoBaixaEstoque.SUCESSO

    monkeypatch.setattr(VendaService, "verificar_produto_existe", staticmethod(produto))
    monkeypatch.setattr(VendaService, "reservar_estoque", staticmethod(reservar))
    return resposta


async def _comprar(client, db, quantidade=2):
    resposta = await client.post(
        "/vendas",
        json={
            "empresa_id": EMPRESA,
            "itens": [{"produto_id": str(uuid.uuid4()), "quantidade": quantidade}],
        },
        headers={"X-Empresa-Id": str(EMPRESA)},
    )
    assert resposta.status_code == 201, resposta.text
    item = (await db.execute(
        select(ItemVenda).where(ItemVenda.venda_id == uuid.UUID(resposta.json()["id"]))
    )).scalar_one()
    return item, resposta.json()


@pytest.mark.asyncio
async def test_produto_em_promocao_e_cobrado_pelo_preco_anunciado(db, client, catalogo):
    catalogo["produto"] = dict(EM_PROMOCAO)

    item, venda = await _comprar(client, db)

    assert item.preco_unitario == Decimal("8.00"), (
        f"a vitrine anuncia 8,00 e a venda cobrou {item.preco_unitario}"
    )
    assert Decimal(venda["valor_total"]) == Decimal("16.00")


@pytest.mark.asyncio
async def test_sem_promocao_cobra_o_preco_de_tabela(db, client, catalogo):
    catalogo["produto"] = dict(SEM_PROMOCAO)

    item, _ = await _comprar(client, db)

    assert item.preco_unitario == Decimal("10.00")


@pytest.mark.asyncio
async def test_catalogo_antigo_cobra_o_preco_cheio_em_vez_de_quebrar(db, client, catalogo):
    """Deploy em andamento: a imagem antiga de produtos não manda preco_efetivo.

    Cobrar o preço de tabela é o lado seguro — perde-se um desconto, não se
    grava uma venda sem preço.
    """
    catalogo["produto"] = dict(CATALOGO_ANTIGO)

    item, _ = await _comprar(client, db)

    assert item.preco_unitario == Decimal("10.00")
