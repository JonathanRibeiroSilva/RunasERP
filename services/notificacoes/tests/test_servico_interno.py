"""Fail-closed do validador de origem interna (INFRA-C), neste serviço.

Os outros cinco serviços fecharam no #124 com tráfego real medido. Aqui não
havia o que medir — só existe /health, que é isento —, então o que prova o
fechamento é este teste, não o log de produção.
"""
import pytest

from config import settings

SEGREDO = "segredo-de-teste"


@pytest.fixture
def segredo(monkeypatch):
    monkeypatch.setattr(settings, "SERVICO_INTERNO_TOKEN", SEGREDO)


@pytest.mark.asyncio
async def test_health_passa_sem_segredo(client, segredo):
    """O healthcheck do Docker bate em localhost sem passar pelo gateway."""
    assert (await client.get("/health")).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [{}, {"X-Servico-Interno-Token": "errado"}])
async def test_recusa_sem_prova_de_origem(client, segredo, headers):
    resposta = await client.get("/qualquer-rota", headers=headers)

    assert resposta.status_code == 403, resposta.text


@pytest.mark.asyncio
async def test_recusa_quando_o_segredo_nao_esta_configurado(client, monkeypatch):
    """O ponto do fail-closed: env vazia não vira porta aberta."""
    monkeypatch.setattr(settings, "SERVICO_INTERNO_TOKEN", "")

    resposta = await client.get("/qualquer-rota", headers={"X-Servico-Interno-Token": ""})

    assert resposta.status_code == 403, resposta.text


@pytest.mark.asyncio
async def test_segredo_certo_passa_pelo_validador(client, segredo):
    """Passou da guarda: o 404 é da rota que não existe, não do validador."""
    resposta = await client.get(
        "/qualquer-rota", headers={"X-Servico-Interno-Token": SEGREDO}
    )

    assert resposta.status_code == 404, resposta.text
