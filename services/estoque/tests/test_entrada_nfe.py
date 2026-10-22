"""Uma NF-e entra no estoque uma vez só, e inteira ou nada.

Antes, o frontend fazia um POST /estoque/entrada por item: subir o mesmo XML de
novo dobrava o saldo, e se o item 3 de 10 falhasse os outros 9 já tinham entrado.
Agora a nota é uma transação só, e a chave de acesso é o gate de idempotência
(unique empresa_id+chave em entradas_nfe_processadas).

Os três primeiros testes usam a fixture `db` (transação que nunca commita). O
último não: o que ele guarda é a corrida entre duas transações de verdade.
"""
import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text

from database import AsyncSessionLocal, engine
from models.estoque import Estoque, Movimentacao
from schemas.estoque import EntradaNfeItem, EntradaNfeRequest
from services.estoque_service import EstoqueService, NfeJaImportadaError

EMPRESA = 990_040
EMPRESA_CONCORRENTE = 990_041
CHAVE = "35261012345678000199550010000012341000012345"
HEADERS = {"X-Empresa-Id": str(EMPRESA)}


async def _estoque(db, quantidade, empresa=EMPRESA):
    linha = Estoque(
        empresa_id=empresa, produto_id=uuid.uuid4(),
        quantidade=quantidade, quantidade_disponivel=quantidade,
    )
    db.add(linha)
    # commit: o serviço dá rollback no erro, e sem isto o rollback levaria junto
    # o que o teste montou. A fixture `db` desfaz tudo no fim de qualquer jeito.
    await db.commit()
    return linha


def _corpo(*itens, chave=CHAVE):
    return {
        "empresa_id": EMPRESA,
        "chave": chave,
        "numero": "1234",
        "emitente": "Fornecedor LTDA",
        "itens": [
            {"produto_id": str(estoque.produto_id), "quantidade": qtd, "custo_unitario": 2.5}
            for estoque, qtd in itens
        ],
    }


@pytest.mark.asyncio
async def test_a_nota_entra_em_todos_os_itens_e_registra_a_origem(db, client):
    a, b = await _estoque(db, 5.0), await _estoque(db, 0.0)

    r = await client.post("/estoque/entrada-nfe", json=_corpo((a, 2.0), (b, 3.0)), headers=HEADERS)

    assert r.status_code == 201, r.text
    assert sorted(i["quantidade"] for i in r.json()) == [3.0, 7.0]
    movs = (await db.execute(
        select(Movimentacao).where(Movimentacao.estoque_id.in_([a.id, b.id]))
    )).scalars().all()
    assert {m.documento for m in movs} == {"NF-e 1234"}
    assert all(CHAVE in m.observacao and "Fornecedor LTDA" in m.observacao for m in movs)


@pytest.mark.asyncio
async def test_mesma_chave_de_novo_e_409_e_nao_soma(db, client):
    a = await _estoque(db, 5.0)
    corpo = _corpo((a, 2.0))

    assert (await client.post("/estoque/entrada-nfe", json=corpo, headers=HEADERS)).status_code == 201
    segunda = await client.post("/estoque/entrada-nfe", json=corpo, headers=HEADERS)

    assert segunda.status_code == 409
    await db.refresh(a)
    assert a.quantidade == 7.0, "a segunda importação somou de novo"


@pytest.mark.asyncio
async def test_item_que_falha_desfaz_a_nota_inteira_e_nao_gasta_a_chave(db, client, monkeypatch):
    a = await _estoque(db, 5.0)
    # O serviço ordena os itens por produto_id: este ordena por último, então o
    # item bom já entrou quando o erro acontece — é isso que o rollback desfaz.
    sem_cadastro = Estoque(produto_id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))

    async def produto_inexistente(*args, **kwargs):
        return False

    monkeypatch.setattr(EstoqueService, "verificar_produto_existe", staticmethod(produto_inexistente))

    r = await client.post(
        "/estoque/entrada-nfe", json=_corpo((a, 2.0), (sem_cadastro, 1.0)), headers=HEADERS
    )

    assert r.status_code == 400
    assert str(sem_cadastro.produto_id) in r.json()["detail"], "o erro não diz qual item falhou"
    await db.refresh(a)
    assert a.quantidade == 5.0, "o item bom ficou gravado com a nota falha"

    # A chave não foi gasta: corrigida a nota, o reenvio entra.
    reenvio = await client.post("/estoque/entrada-nfe", json=_corpo((a, 2.0)), headers=HEADERS)
    assert reenvio.status_code == 201, reenvio.text


@pytest.mark.asyncio
async def test_chave_precisa_ter_44_digitos(db, client):
    a = await _estoque(db, 5.0)

    r = await client.post("/estoque/entrada-nfe", json=_corpo((a, 1.0), chave="123"), headers=HEADERS)

    assert r.status_code == 422


@pytest_asyncio.fixture
async def estoque_commitado():
    """Linha de estoque commitada de verdade, apagada no fim com o que a nota gerou."""
    async with AsyncSessionLocal() as s:
        linha = Estoque(
            empresa_id=EMPRESA_CONCORRENTE, produto_id=uuid.uuid4(),
            quantidade=5.0, quantidade_disponivel=5.0,
        )
        s.add(linha)
        await s.commit()
        await s.refresh(linha)

    yield linha

    async with engine.begin() as c:
        for sql in (
            "DELETE FROM estoque.movimentacoes WHERE estoque_id IN "
            "(SELECT id FROM estoque.estoque WHERE empresa_id = :e)",
            "DELETE FROM estoque.estoque WHERE empresa_id = :e",
            "DELETE FROM estoque.entradas_nfe_processadas WHERE empresa_id = :e",
            "DELETE FROM gateway.auditoria_registros WHERE empresa_id = :e",
        ):
            await c.execute(text(sql), {"e": EMPRESA_CONCORRENTE})
    await engine.dispose()


@pytest.mark.asyncio
async def test_duas_requisicoes_da_mesma_nota_entram_uma_vez(estoque_commitado):
    """Duplo clique, retry de rede, duas abas: o índice único decide, não a sorte."""
    pedido = EntradaNfeRequest(
        empresa_id=EMPRESA_CONCORRENTE, chave=CHAVE, numero="1234", emitente="Fornecedor LTDA",
        itens=[EntradaNfeItem(produto_id=estoque_commitado.produto_id, quantidade=2.0)],
    )

    async def importar():
        async with AsyncSessionLocal() as s:
            return await EstoqueService.entrada_nfe(s, EMPRESA_CONCORRENTE, pedido)

    resultados = await asyncio.gather(importar(), importar(), return_exceptions=True)

    assert sum(isinstance(r, NfeJaImportadaError) for r in resultados) == 1, resultados
    async with AsyncSessionLocal() as s:
        assert (await s.get(Estoque, estoque_commitado.id)).quantidade == 7.0
    await engine.dispose()
