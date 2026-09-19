"""Criar venda: a recusa do estoque bloqueia; o silêncio do estoque sinaliza.

Até aqui o vendas reservava item a item, logava a falha e marcava o item como
reservado de qualquer jeito. Dois problemas em um: a venda saía prometendo
mercadoria que o estoque tinha recusado, e o item afirmava uma reserva que não
existia.

O conserto separa o que um bool juntava. Se o estoque RESPONDE que não reservou
(4xx), a venda não é criada, e as reservas que ele confirmou para os itens
anteriores são desfeitas — o rollback do banco do vendas não alcança o serviço de
estoque. Se o estoque NÃO responde (timeout, 5xx), nada é desfeito: a reserva é
um contador por produto, e soltar às cegas pode soltar a de outro pedido. A venda
segue, o item diz a verdade (estoque_reservado=False) e a venda vai para a fila
de reconciliação.

HTTP para produtos e estoque é substituído; o banco é o Postgres de verdade.
"""
import uuid
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select

from models.venda import ItemVenda, Venda
from schemas.venda import ItemVendaCreate, VendaCreate
from services import venda_service
from services.estoque_resultado import ResultadoBaixaEstoque
from services.venda_service import VendaService

EMPRESA = 990_101

SUCESSO = ResultadoBaixaEstoque.SUCESSO
SEM_ESTOQUE = ResultadoBaixaEstoque.SEM_ESTOQUE
INDETERMINADO = ResultadoBaixaEstoque.INDETERMINADO


class Registro:
    """Substitui o `log` do módulo e guarda cada evento emitido."""

    def __init__(self):
        self.eventos = []

    def __getattr__(self, nivel):
        return lambda evento, **campos: self.eventos.append((nivel, evento, campos))


@pytest.fixture
def estoque_responde(monkeypatch):
    """Configura, por produto, o que o serviço de estoque responde à reserva."""
    respostas, liberados = {}, []
    config = {"liberacao_funciona": True}

    async def produto(produto_id, variante_id, empresa_id):
        return {"preco": "10.00", "nome": f"Produto {str(produto_id)[:4]}", "sku": "SKU"}

    async def reservar(empresa_id, produto_id, variante_id, quantidade, documento):
        return respostas[produto_id]

    async def liberar(empresa_id, produto_id, variante_id, quantidade, documento):
        liberados.append(produto_id)
        return config["liberacao_funciona"]

    monkeypatch.setattr(VendaService, "verificar_produto_existe", staticmethod(produto))
    monkeypatch.setattr(VendaService, "reservar_estoque", staticmethod(reservar))
    monkeypatch.setattr(VendaService, "liberar_reserva_estoque", staticmethod(liberar))
    return respostas, liberados, config


def _venda(*produtos):
    return VendaCreate(
        empresa_id=EMPRESA,
        itens=[ItemVendaCreate(produto_id=p, quantidade=Decimal("1")) for p in produtos],
    )


async def _vendas_gravadas(db):
    return await db.scalar(select(func.count()).select_from(Venda).where(Venda.empresa_id == EMPRESA))


@pytest.mark.asyncio
async def test_recusa_bloqueia_a_venda_e_desfaz_so_as_reservas_confirmadas(db, estoque_responde):
    respostas, liberados, _ = estoque_responde
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    respostas.update({a: SUCESSO, b: SEM_ESTOQUE, c: SUCESSO})

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        await VendaService.criar_venda(db, EMPRESA, _venda(a, b, c))

    assert await _vendas_gravadas(db) == 0, "a venda foi criada mesmo com o estoque recusando"
    assert liberados == [a], (
        f"deveria desfazer só a reserva de A, a única confirmada antes da recusa: {liberados}"
    )


@pytest.mark.asyncio
async def test_timeout_nao_bloqueia_nao_desfaz_e_manda_para_reconciliacao(db, estoque_responde):
    respostas, liberados, _ = estoque_responde
    a, b = uuid.uuid4(), uuid.uuid4()
    respostas.update({a: SUCESSO, b: INDETERMINADO})

    resposta = await VendaService.criar_venda(db, EMPRESA, _venda(a, b))

    venda = await db.get(Venda, resposta.id)
    await db.refresh(venda)
    itens = {
        i.produto_id: i.estoque_reservado
        for i in (await db.execute(select(ItemVenda).where(ItemVenda.venda_id == venda.id))).scalars()
    }
    assert liberados == [], "reserva indeterminada foi desfeita — pode ter soltado a de outro pedido"
    assert itens == {a: True, b: False}, f"o item diz uma reserva que não se sabe se existe: {itens}"
    assert venda.reconciliacao_estoque_pendente is True
    assert "indeterminada" in venda.reconciliacao_motivo


@pytest.mark.asyncio
async def test_tudo_reservado_cria_a_venda_sem_pendencia(db, estoque_responde):
    respostas, liberados, _ = estoque_responde
    a, b = uuid.uuid4(), uuid.uuid4()
    respostas.update({a: SUCESSO, b: SUCESSO})

    resposta = await VendaService.criar_venda(db, EMPRESA, _venda(a, b))

    venda = await db.get(Venda, resposta.id)
    await db.refresh(venda)
    assert venda.reconciliacao_estoque_pendente is False
    assert liberados == []


@pytest.mark.asyncio
async def test_liberacao_que_falha_vira_alerta_e_a_venda_continua_recusada(db, estoque_responde, monkeypatch):
    respostas, _, config = estoque_responde
    config["liberacao_funciona"] = False
    registro = Registro()
    monkeypatch.setattr(venda_service, "log", registro)
    a, b = uuid.uuid4(), uuid.uuid4()
    respostas.update({a: SUCESSO, b: SEM_ESTOQUE})

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        await VendaService.criar_venda(db, EMPRESA, _venda(a, b))

    criticos = [(e, c) for nivel, e, c in registro.eventos if nivel == "critical"]
    assert [e for e, _ in criticos] == ["reserva_orfa_liberar_manual"], registro.eventos
    assert criticos[0][1]["produto_id"] == str(a)


class EstoqueHttp:
    """Dublê de httpx.AsyncClient: devolve um status fixo ou levanta um erro."""

    def __init__(self, status=None, erro=None):
        self.status, self.erro = status, erro

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, *args, **kwargs):
        if self.erro:
            raise self.erro
        return httpx.Response(self.status, text="detalhe do estoque")


@pytest.mark.asyncio
@pytest.mark.parametrize("dubl, esperado", [
    (EstoqueHttp(status=201), SUCESSO),
    (EstoqueHttp(status=400), SEM_ESTOQUE),   # o que /reservar devolve quando falta
    (EstoqueHttp(status=403), SEM_ESTOQUE),
    (EstoqueHttp(status=500), INDETERMINADO),
    (EstoqueHttp(status=503), INDETERMINADO),
    (EstoqueHttp(erro=httpx.ReadTimeout("lento")), INDETERMINADO),
    (EstoqueHttp(erro=httpx.ConnectError("fora")), INDETERMINADO),
], ids=["201", "400", "403", "500", "503", "timeout", "sem-conexao"])
async def test_reservar_distingue_recusa_de_silencio(dubl, esperado, monkeypatch):
    monkeypatch.setattr(venda_service.httpx, "AsyncClient", dubl)

    resultado = await VendaService.reservar_estoque(EMPRESA, uuid.uuid4(), None, Decimal("1"), "V-1")

    assert resultado == esperado
