"""
C1+C2+C3 (Onda 6): o ledger substitui o campo `credito_disponivel` mutado direto.

C1 — trocar o limite não pode apagar o saldo devedor.
C2 — débito/crédito é idempotente por (empresa_id, documento, tipo); corrida
     concorrente não duplica o efeito.
C3 — débito que deixaria o disponível negativo é recusado (teto de crédito).
"""
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from validate_docbr import CPF

from main import app
from models.cliente import TipoMovimentoCredito
from repositories.cliente_repository import ClienteRepository
from schemas.cliente import ClienteCreate

EMPRESA = 990_301


async def _cliente(db, limite=Decimal("0.00")):
    repo = ClienteRepository(db)
    cliente = await repo.criar(ClienteCreate(
        empresa_id=EMPRESA,
        nome="Cliente Fiado",
        cpf=CPF().generate(),
        telefone="11999999999",
    ))
    if limite:
        await repo.atualizar_credito(cliente.id, EMPRESA, limite, None)
    await db.commit()
    return cliente


@pytest.mark.asyncio
async def test_trocar_limite_preserva_o_saldo_devedor(db):
    """C1: cliente deve 40 de 100; lojista sobe o limite para 150 — a dívida continua 40."""
    repo = ClienteRepository(db)
    cliente = await _cliente(db, Decimal("100.00"))

    await repo.registrar_movimento_credito(
        cliente.id, EMPRESA, TipoMovimentoCredito.DEBITO, Decimal("-40.00"), "V-1"
    )
    await db.commit()

    atualizado = await repo.atualizar_credito(cliente.id, EMPRESA, Decimal("150.00"), None)
    await db.commit()

    assert atualizado.credito_disponivel == Decimal("110.00"), (
        "limite subiu 50 (100→150); disponível devia subir junto (60→110), "
        "não ser reposto para o limite cheio e apagar a dívida de 40"
    )


@pytest.mark.asyncio
async def test_debito_alem_do_disponivel_e_recusado(db):
    """C3: o teto de crédito que vendas nunca checava antes de fechar a venda fiada."""
    repo = ClienteRepository(db)
    cliente = await _cliente(db, Decimal("50.00"))

    with pytest.raises(ValueError, match="insuficiente"):
        await repo.registrar_movimento_credito(
            cliente.id, EMPRESA, TipoMovimentoCredito.DEBITO, Decimal("-60.00"), "V-2"
        )


@pytest.mark.asyncio
async def test_mesmo_documento_nao_debita_duas_vezes(db):
    """C2: repetir a chamada (retry, webhook duplicado) é idempotente, não debita de novo."""
    repo = ClienteRepository(db)
    cliente = await _cliente(db, Decimal("100.00"))

    primeira = await repo.registrar_movimento_credito(
        cliente.id, EMPRESA, TipoMovimentoCredito.DEBITO, Decimal("-30.00"), "V-3"
    )
    await db.commit()
    segunda = await repo.registrar_movimento_credito(
        cliente.id, EMPRESA, TipoMovimentoCredito.DEBITO, Decimal("-30.00"), "V-3"
    )

    assert primeira.credito_disponivel == Decimal("70.00")
    assert segunda.credito_disponivel == Decimal("70.00"), (
        "o mesmo documento debitou duas vezes — retry/webhook duplicado não é seguro"
    )


@pytest.mark.asyncio
async def test_credito_de_estorno_devolve_o_disponivel(db):
    """Cancelamento de venda fiada credita de volta — mesmo documento, tipo diferente."""
    repo = ClienteRepository(db)
    cliente = await _cliente(db, Decimal("100.00"))

    await repo.registrar_movimento_credito(
        cliente.id, EMPRESA, TipoMovimentoCredito.DEBITO, Decimal("-40.00"), "V-4"
    )
    await db.commit()
    devolvido = await repo.registrar_movimento_credito(
        cliente.id, EMPRESA, TipoMovimentoCredito.CREDITO, Decimal("40.00"), "V-4"
    )

    assert devolvido.credito_disponivel == Decimal("100.00")


@pytest.mark.asyncio
async def test_rota_de_credito_exige_prova_de_origem_interna():
    """
    C4: a rota some sozinha junto com o middleware global do INFRA-C (#107/#124) —
    este teste prova que ela está mesmo coberta, não só que devia estar. O
    middleware rejeita antes de tocar o banco, então nem precisa de um cliente
    de verdade. Usa um AsyncClient próprio, sem o carimbo que o `client` fixture
    adiciona por padrão, simulando um request que não passou pelo gateway nem
    por uma chamada interna real.
    """
    cliente_id = "00000000-0000-0000-0000-000000000000"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as sem_carimbo:
        resposta = await sem_carimbo.post(
            f"/clientes/{cliente_id}/credito/ajustar",
            json={"delta": "-10.00", "documento": "V-5"},
            headers={"X-Empresa-Id": str(EMPRESA)},
        )

    assert resposta.status_code == 403, resposta.text
