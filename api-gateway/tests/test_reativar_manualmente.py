"""Reativação do suporte: sai de somente leitura/suspensa e não volta na régua."""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from services import preapproval_service

EMPRESA_ID = 987001


async def _assinatura(db, status: str) -> None:
    await db.execute(
        text(
            "INSERT INTO gateway.assinaturas "
            "(empresa_id, plano, valor, status, vence_em, carencia_ate, somente_leitura_desde) "
            "VALUES (:e, 'BASICO', 99, :s, '2020-01-01', '2020-01-06', '2020-01-07')"
        ),
        {"e": EMPRESA_ID, "s": status},
    )


async def _linha(db):
    return (await db.execute(
        text("SELECT status, carencia_ate, somente_leitura_desde FROM gateway.assinaturas "
             "WHERE empresa_id = :e"),
        {"e": EMPRESA_ID},
    )).one()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["INADIMPLENTE", "SUSPENSA"])
async def test_reativar_limpa_somente_leitura_e_estende_carencia(db, status):
    await _assinatura(db, status)

    await preapproval_service.reativar_manualmente(db, EMPRESA_ID)

    linha = await _linha(db)
    assert linha.status == "ATIVA"
    assert linha.somente_leitura_desde is None
    assert linha.carencia_ate == date.today() + timedelta(days=preapproval_service.DIAS_CARENCIA)


@pytest.mark.asyncio
async def test_reativar_nao_desfaz_cancelamento(db):
    await _assinatura(db, "CANCELADA")

    await preapproval_service.reativar_manualmente(db, EMPRESA_ID)

    linha = await _linha(db)
    assert linha.status == "CANCELADA"
    assert linha.somente_leitura_desde is not None
