"""Trocar o limite e debitar o fiado ao mesmo tempo não pode apagar nenhum dos dois.

`atualizar_credito` (trocar o limite) e `registrar_movimento_credito` (débito do
ledger) calculam o `credito_disponivel` novo em Python, a partir de uma leitura da
linha. Sem lock, o lojista que edita o limite no instante de uma venda fiada lê o
saldo antigo e grava por cima do débito que commitou no meio: o cliente fica com
crédito a mais. `test_trocar_limite_preserva_o_saldo_devedor` não vê isso, porque é
sequencial.

O teste força o pior intercalamento. Os dois caminhos passam pelo service, que lê o
cliente (`buscar_cliente`) antes de chegar ao repository — e é aí que a barreira
fica: as duas operações só seguem depois que as duas já leram o cliente, então as
duas chegam ao lock com o saldo antigo no identity map. Só a leitura travada que
também refresca a instância (`populate_existing`) enxerga o que a outra gravou; um
`FOR UPDATE` sozinho espera a outra commitar e devolve a instância velha.

Qualquer ordem de serialização termina em 110: limite 150 menos os 40 de fiado.

Não usa a fixture `db` do conftest: ela vive numa transação que nunca commita, e o
que se testa aqui é justamente o que acontece entre duas transações.
"""
import asyncio
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import text
from validate_docbr import CPF

from database import AsyncSessionLocal, engine
from models.cliente import Cliente
from repositories.cliente_repository import ClienteRepository
from schemas.cliente import ClienteCreate, CreditoUpdate
from services.cliente_service import ClienteService

# Tenant exclusivo deste teste: a limpeza apaga tudo dele e de nenhum outro.
EMPRESA = 990_302


@pytest_asyncio.fixture
async def cliente_com_limite():
    """Cliente commitado de verdade com limite 100, apagado no fim com o que gerou."""
    async with AsyncSessionLocal() as s:
        repo = ClienteRepository(s)
        cliente = await repo.criar(ClienteCreate(
            empresa_id=EMPRESA, nome="Cliente Fiado", cpf=CPF().generate(), telefone="11999999999",
        ))
        await repo.atualizar_credito(cliente.id, EMPRESA, Decimal("100.00"), None)
        await s.commit()
        cliente_id = cliente.id

    yield cliente_id

    async with engine.begin() as c:
        for sql in (
            "DELETE FROM clientes.movimentos_credito WHERE empresa_id = :e",
            "DELETE FROM clientes.clientes WHERE empresa_id = :e",
            "DELETE FROM gateway.auditoria_registros WHERE empresa_id = :e",
        ):
            await c.execute(text(sql), {"e": EMPRESA})
    await engine.dispose()


@pytest.mark.asyncio
async def test_trocar_limite_e_debitar_ao_mesmo_tempo_nao_se_apagam(cliente_com_limite, monkeypatch):
    cliente_id = cliente_com_limite
    barreira = asyncio.Barrier(2)
    ler_cliente = ClienteService.buscar_cliente

    async def ler_e_esperar_a_outra(self, *args, **kwargs):
        cliente = await ler_cliente(self, *args, **kwargs)
        # Timeout só para o teste não travar se uma das duas falhar antes de chegar.
        await asyncio.wait_for(barreira.wait(), timeout=5)
        return cliente

    monkeypatch.setattr(ClienteService, "buscar_cliente", ler_e_esperar_a_outra)

    async def em_sessao(operacao):
        async with AsyncSessionLocal() as s:
            return await operacao(ClienteService(s))

    resultados = await asyncio.gather(
        em_sessao(lambda svc: svc.definir_credito(
            cliente_id, EMPRESA, CreditoUpdate(limite_credito=Decimal("150.00"), dia_vencimento=None)
        )),
        em_sessao(lambda svc: svc.ajustar_credito(cliente_id, EMPRESA, Decimal("-40.00"), "V-CONC-1")),
        return_exceptions=True,
    )

    async with AsyncSessionLocal() as s:
        final = await s.get(Cliente, cliente_id)
    assert not [r for r in resultados if isinstance(r, Exception)], resultados
    assert (final.limite_credito, final.credito_disponivel) == (Decimal("150.00"), Decimal("110.00")), (
        f"limite {final.limite_credito}, disponível {final.credito_disponivel}: "
        "uma das duas escritas apagou a outra (esperado 150 / 110)"
    )
