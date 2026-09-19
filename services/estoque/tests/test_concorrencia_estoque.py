"""Duas escritas simultâneas no mesmo estoque não podem se apagar.

Toda escrita de EstoqueService calcula a quantidade nova em Python, a partir de
uma leitura da linha. Sem SELECT ... FOR UPDATE, duas requisições leem o mesmo
valor e a segunda grava por cima da primeira: dois pedidos reservam o último
item, duas entradas somam como uma, dois ajustes deixam movimentações com o
mesmo quantidade_anterior. O lock existia no repositório e só baixa/estorno de
venda o usavam.

Estes testes não torcem por uma corrida — forçam o pior intercalamento. Cada um
põe um ponto de encontro logo depois da leitura: sem lock, as duas transações
leem e chegam lá juntas; com lock, a segunda fica presa no FOR UPDATE, a
primeira desiste de esperar e segue, e a segunda só lê depois do commit dela.

Não usam a fixture `db` do conftest: ela vive numa transação que nunca commita,
e o que se testa aqui é justamente o que acontece entre duas transações.
"""
import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text

from database import AsyncSessionLocal, engine
from models.estoque import Estoque, Movimentacao
from repositories.estoque_repository import EstoqueRepository, MovimentacaoRepository
from schemas.estoque import (
    AjusteEstoqueRequest,
    EntradaEstoqueRequest,
    LiberarReservaRequest,
    ReservaEstoqueRequest,
    SaidaEstoqueRequest,
)
from services.estoque_service import EstoqueService

# Tenant exclusivo destes testes: a limpeza apaga tudo dele e de nenhum outro.
EMPRESA = 990_001


@pytest_asyncio.fixture
async def criar_estoque():
    """Linhas de estoque commitadas de verdade, apagadas no fim com o que elas geraram."""
    async def _criar(quantidade=1.0, reservada=0.0):
        async with AsyncSessionLocal() as s:
            linha = Estoque(
                empresa_id=EMPRESA,
                produto_id=uuid.uuid4(),
                quantidade=quantidade,
                quantidade_reservada=reservada,
                quantidade_disponivel=quantidade - reservada,
            )
            s.add(linha)
            await s.commit()
            await s.refresh(linha)
            return linha

    yield _criar

    async with engine.begin() as c:
        for sql in (
            "DELETE FROM estoque.movimentacoes WHERE estoque_id IN "
            "(SELECT id FROM estoque.estoque WHERE empresa_id = :e)",
            "DELETE FROM estoque.lotes WHERE estoque_id IN "
            "(SELECT id FROM estoque.estoque WHERE empresa_id = :e)",
            "DELETE FROM estoque.estoque WHERE empresa_id = :e",
            "DELETE FROM gateway.auditoria_registros WHERE empresa_id = :e",
        ):
            await c.execute(text(sql), {"e": EMPRESA})
    await engine.dispose()


def ponto_de_encontro(monkeypatch, alvo, nome, espera=0.5):
    """Troca alvo.nome por uma versão que espera a outra transação chegar ali.

    Sem lock as duas chegam em milissegundos e seguem juntas. Com lock a segunda
    nunca chega enquanto a primeira não commitar, então a primeira desiste de
    esperar em `espera` segundos — o teste não trava, só deixa de forçar a corrida.
    """
    original = getattr(alvo, nome)
    chegaram = []
    todas = asyncio.Event()

    async def com_encontro(*args, **kwargs):
        chegaram.append(True)
        if len(chegaram) == 2:
            todas.set()
        try:
            await asyncio.wait_for(todas.wait(), timeout=espera)
        except asyncio.TimeoutError:
            pass
        return await original(*args, **kwargs)

    monkeypatch.setattr(alvo, nome, staticmethod(com_encontro))


async def ao_mesmo_tempo(*operacoes):
    """Cada operação na sua própria sessão, como duas requisições de verdade."""
    async def em_sessao(operacao):
        async with AsyncSessionLocal() as s:
            return await operacao(s)

    return await asyncio.gather(*(em_sessao(op) for op in operacoes), return_exceptions=True)


async def recarregar(estoque_id):
    async with AsyncSessionLocal() as s:
        linha = await s.get(Estoque, estoque_id)
        movs = (await s.execute(
            select(Movimentacao).where(Movimentacao.estoque_id == estoque_id)
            .order_by(Movimentacao.quantidade_anterior.desc())
        )).scalars().all()
    await engine.dispose()
    return linha, movs


def falhas(resultados):
    return [r for r in resultados if isinstance(r, Exception)]


@pytest.mark.asyncio
async def test_dois_pedidos_pelo_ultimo_item_so_um_reserva(criar_estoque, monkeypatch):
    estoque = await criar_estoque(quantidade=1.0)
    ponto_de_encontro(monkeypatch, EstoqueRepository, "reservar")
    pedido = ReservaEstoqueRequest(empresa_id=EMPRESA, produto_id=estoque.produto_id, quantidade=1.0)

    resultados = await ao_mesmo_tempo(
        lambda s: EstoqueService.reservar_estoque(s, EMPRESA, pedido),
        lambda s: EstoqueService.reservar_estoque(s, EMPRESA, pedido),
    )

    linha, _ = await recarregar(estoque.id)
    assert len(falhas(resultados)) == 1, (
        f"os dois pedidos reservaram o único item — overselling: {resultados}"
    )
    assert isinstance(falhas(resultados)[0], ValueError), resultados
    assert (linha.quantidade_reservada, linha.quantidade_disponivel) == (1.0, 0.0)


@pytest.mark.asyncio
async def test_a_mesma_reserva_so_e_liberada_uma_vez(criar_estoque, monkeypatch):
    estoque = await criar_estoque(quantidade=1.0, reservada=1.0)
    ponto_de_encontro(monkeypatch, EstoqueRepository, "liberar_reserva")
    pedido = LiberarReservaRequest(empresa_id=EMPRESA, produto_id=estoque.produto_id, quantidade=1.0)

    resultados = await ao_mesmo_tempo(
        lambda s: EstoqueService.liberar_reserva(s, EMPRESA, pedido),
        lambda s: EstoqueService.liberar_reserva(s, EMPRESA, pedido),
    )

    linha, _ = await recarregar(estoque.id)
    assert len(falhas(resultados)) == 1, (
        f"uma reserva de 1 foi liberada duas vezes: {resultados}"
    )
    assert (linha.quantidade_reservada, linha.quantidade_disponivel) == (0.0, 1.0)


@pytest.mark.asyncio
async def test_duas_saidas_do_ultimo_item_so_uma_sai(criar_estoque, monkeypatch):
    estoque = await criar_estoque(quantidade=1.0)
    ponto_de_encontro(monkeypatch, MovimentacaoRepository, "criar")
    saida = SaidaEstoqueRequest(empresa_id=EMPRESA, produto_id=estoque.produto_id, quantidade=1.0)

    resultados = await ao_mesmo_tempo(
        lambda s: EstoqueService.saida_estoque(s, EMPRESA, saida),
        lambda s: EstoqueService.saida_estoque(s, EMPRESA, saida),
    )

    linha, movs = await recarregar(estoque.id)
    assert len(falhas(resultados)) == 1, (
        f"o mesmo item saiu duas vezes do estoque: {resultados}"
    )
    assert linha.quantidade == 0.0
    assert len(movs) == 1, f"{len(movs)} movimentações de saída para 1 unidade física"


@pytest.mark.asyncio
async def test_duas_entradas_somam_as_duas(criar_estoque, monkeypatch):
    estoque = await criar_estoque(quantidade=1.0)
    ponto_de_encontro(monkeypatch, MovimentacaoRepository, "criar")
    entrada = EntradaEstoqueRequest(empresa_id=EMPRESA, produto_id=estoque.produto_id, quantidade=5.0)

    resultados = await ao_mesmo_tempo(
        lambda s: EstoqueService.entrada_estoque(s, EMPRESA, entrada),
        lambda s: EstoqueService.entrada_estoque(s, EMPRESA, entrada),
    )

    linha, movs = await recarregar(estoque.id)
    assert not falhas(resultados), resultados
    assert linha.quantidade == 11.0, (
        f"1 + 5 + 5 deu {linha.quantidade}: uma entrada apagou a outra"
    )
    assert [(m.quantidade_anterior, m.quantidade_posterior) for m in movs] == [(6.0, 11.0), (1.0, 6.0)]


@pytest.mark.asyncio
async def test_dois_ajustes_deixam_a_trilha_encadeada(criar_estoque, monkeypatch):
    estoque = await criar_estoque(quantidade=10.0)
    ponto_de_encontro(monkeypatch, MovimentacaoRepository, "criar")

    resultados = await ao_mesmo_tempo(
        lambda s: EstoqueService.ajustar_estoque(
            s, EMPRESA, AjusteEstoqueRequest(estoque_id=estoque.id, quantidade_nova=7.0, motivo="inventário")
        ),
        lambda s: EstoqueService.ajustar_estoque(
            s, EMPRESA, AjusteEstoqueRequest(estoque_id=estoque.id, quantidade_nova=4.0, motivo="inventário")
        ),
    )

    _, movs = await recarregar(estoque.id)
    assert not falhas(resultados), resultados
    anteriores = sorted(m.quantidade_anterior for m in movs)
    posteriores = {m.quantidade_posterior for m in movs}
    assert 10.0 in anteriores and anteriores[0] in posteriores, (
        f"as duas movimentações partem de {anteriores}: a segunda leu o estoque "
        "antes da primeira gravar, e a trilha não fecha com o saldo"
    )
