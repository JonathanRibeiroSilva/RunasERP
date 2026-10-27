"""Fail-closed do validador de origem interna (INFRA-C), neste serviço.

Fechou em 6b9c2a9 (#124), mas só um guard por texto conferia que o middleware
está ligado (tests/unit/test_auth_servico_a_servico.py): voltar ao fail-open
passava na CI. Mesmo molde de services/financeiro/tests/test_servico_interno.py,
com uma diferença: aqui o client do conftest já vem carimbado, e `headers={}`
não tira o carimbo (o httpx funde com os headers do client). Sem o pop, o caso
"sem header" cairia no ramo do header errado e passaria com o fail-open de volta.
"""
import pytest

from config import settings
from interno import HEADER

SEGREDO = "segredo-de-teste"


@pytest.fixture
def segredo(monkeypatch):
    monkeypatch.setattr(settings, "SERVICO_INTERNO_TOKEN", SEGREDO)


@pytest.mark.asyncio
async def test_health_passa_sem_segredo(client, segredo):
    """O healthcheck do Docker bate em localhost sem passar pelo gateway."""
    client.headers.pop(HEADER, None)

    assert (await client.get("/health")).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [{}, {HEADER: "errado"}])
async def test_recusa_sem_prova_de_origem(client, segredo, headers):
    client.headers.pop(HEADER, None)

    resposta = await client.get("/qualquer-rota", headers=headers)

    assert resposta.status_code == 403, resposta.text


@pytest.mark.asyncio
async def test_recusa_quando_o_segredo_nao_esta_configurado(client, monkeypatch):
    """O ponto do fail-closed: env vazia não vira porta aberta."""
    monkeypatch.setattr(settings, "SERVICO_INTERNO_TOKEN", "")

    resposta = await client.get("/qualquer-rota", headers={HEADER: ""})

    assert resposta.status_code == 403, resposta.text


@pytest.mark.asyncio
async def test_segredo_certo_passa_pelo_validador(client, segredo):
    """Passou da guarda: o 404 é da rota que não existe, não do validador."""
    resposta = await client.get("/qualquer-rota", headers={HEADER: SEGREDO})

    assert resposta.status_code == 404, resposta.text
