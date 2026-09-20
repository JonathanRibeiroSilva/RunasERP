"""O preço do item é o do catálogo, nunca o do pedido.

criar_venda buscava o produto no serviço de produtos e jogava o preço fora assim
que o payload mandasse um: `item.preco_unitario if item.preco_unitario else ...`.
Quem alcançasse POST /vendas escolhia quanto a venda custava — e por fora de
desconto_tipo/desconto_valor, então o relatório lia "vendido a R$ 3" como preço
normal, sem dizer que houve desconto nem de quanto.

Os testes entram pela rota, não pelo service: o campo saiu do schema, e só um
payload cru consegue mandá-lo. HTTP para produtos e estoque é substituído; o
banco é o Postgres de verdade.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from models.venda import ItemVenda, Venda
from services.estoque_resultado import ResultadoBaixaEstoque
from services.venda_service import VendaService

EMPRESA = 990_102

# Produto e variante devolvem o preço em chaves diferentes — é a mesma leitura
# que o carrinho faz, e os dois caminhos têm que continuar achando o preço.
CATALOGO_PRODUTO = {"preco": "10.00", "nome": "Produto", "sku": "SKU"}
CATALOGO_VARIANTE = {"preco_venda": "10.00", "nome": "Variante", "sku": "SKU-V"}


@pytest.fixture
def catalogo(monkeypatch):
    """Substitui o serviço de produtos; o teste escolhe o que ele responde."""
    resposta = {"produto": dict(CATALOGO_PRODUTO)}

    async def produto(produto_id, variante_id, empresa_id):
        return resposta["produto"]

    async def reservar(empresa_id, produto_id, variante_id, quantidade, documento):
        return ResultadoBaixaEstoque.SUCESSO

    monkeypatch.setattr(VendaService, "verificar_produto_existe", staticmethod(produto))
    monkeypatch.setattr(VendaService, "reservar_estoque", staticmethod(reservar))
    return resposta


def _payload(**extras_do_item):
    return {
        "empresa_id": EMPRESA,
        "itens": [{"produto_id": str(uuid.uuid4()), "quantidade": 2, **extras_do_item}],
    }


async def _post(client, payload):
    return await client.post("/vendas", json=payload, headers={"X-Empresa-Id": str(EMPRESA)})


async def _vendas_gravadas(db):
    return await db.scalar(
        select(func.count()).select_from(Venda).where(Venda.empresa_id == EMPRESA)
    )


@pytest.mark.asyncio
async def test_preco_no_pedido_e_recusado_em_vez_de_virar_o_preco_da_venda(db, client, catalogo):
    resposta = await _post(client, _payload(preco_unitario="0.01"))

    assert resposta.status_code == 422, (
        f"o pedido escolheu o preço e foi aceito: {resposta.status_code} {resposta.text[:200]}"
    )
    assert "preco_unitario" in resposta.text
    assert await _vendas_gravadas(db) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "catalogo_responde", [CATALOGO_PRODUTO, CATALOGO_VARIANTE], ids=["produto", "variante"]
)
async def test_preco_gravado_e_o_do_catalogo(db, client, catalogo, catalogo_responde):
    catalogo["produto"] = dict(catalogo_responde)

    resposta = await _post(client, _payload())

    assert resposta.status_code == 201, resposta.text
    item = (await db.execute(
        select(ItemVenda).where(ItemVenda.venda_id == uuid.UUID(resposta.json()["id"]))
    )).scalar_one()
    assert item.preco_unitario == Decimal("10.00")
    assert item.subtotal == Decimal("20.00")
    assert Decimal(resposta.json()["valor_total"]) == Decimal("20.00")


@pytest.mark.asyncio
async def test_catalogo_sem_preco_nao_vira_venda_de_graca(db, client, catalogo):
    """Sem o preço do pedido como rede, preço zero no catálogo tem que barrar.

    Antes, um catálogo sem preço era compensado pelo preço que o pedido mandava;
    agora ninguém compensa, e gravar a venda mesmo assim seria dar a mercadoria.
    """
    catalogo["produto"] = {"preco": "0", "nome": "Produto sem preço"}

    resposta = await _post(client, _payload())

    assert resposta.status_code == 400, resposta.text
    assert "sem preço de venda" in resposta.json()["detail"]
    assert await _vendas_gravadas(db) == 0
