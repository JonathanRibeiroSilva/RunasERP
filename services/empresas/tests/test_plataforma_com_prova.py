"""
G1b: o X-Plataforma passa a carregar prova de que saiu do gateway.

`exigir_plataforma` guarda TODAS as rotas de plataforma deste serviço — inclusive
as que apagam tenant. Antes ela acreditava em `X-Plataforma: 1` e nada mais:
bastava alcançar a porta 8007 para virar plataforma.

O `SERVICO_INTERNO_TOKEN` do INFRA-C (#107) não fecha isso. Ele é o MESMO nos 8
containers, então prova apenas que a chamada veio de algum deles — e um
`notificacoes` comprometido apagando tenant é exatamente o que este achado
descreve. Daí um segundo segredo, de escopo menor: gateway e empresas, só.

Ao contrário das guardas estáticas do #107, aqui a lógica roda de verdade:
`exigir_plataforma` é uma corrotina de dois headers, sem banco e sem app.
"""
import pytest
from fastapi import HTTPException

from config import settings
from routers.empresas import exigir_plataforma

SEGREDO = "a" * 64


@pytest.fixture
def com_segredo(monkeypatch):
    monkeypatch.setattr(settings, "PLATAFORMA_INTERNO_TOKEN", SEGREDO)


@pytest.fixture
def sem_segredo(monkeypatch):
    monkeypatch.setattr(settings, "PLATAFORMA_INTERNO_TOKEN", "")


@pytest.mark.asyncio
async def test_sem_x_plataforma_continua_403(com_segredo):
    """A guarda antiga não pode ter afrouxado."""
    with pytest.raises(HTTPException) as e:
        await exigir_plataforma(x_plataforma=None, x_plataforma_token=SEGREDO)
    assert e.value.status_code == 403


@pytest.mark.asyncio
async def test_token_certo_passa(com_segredo):
    assert await exigir_plataforma(
        x_plataforma="1", x_plataforma_token=SEGREDO) is None


@pytest.mark.asyncio
async def test_token_errado_e_403(com_segredo):
    """O caso que o achado descreve: dentro da malha, mas não é o gateway."""
    with pytest.raises(HTTPException) as e:
        await exigir_plataforma(x_plataforma="1", x_plataforma_token="b" * 64)
    assert e.value.status_code == 403


@pytest.mark.asyncio
async def test_token_nao_ascii_nao_vira_500(com_segredo):
    """compare_digest levanta TypeError em str não-ASCII, e o header vem de fora."""
    with pytest.raises(HTTPException) as e:
        await exigir_plataforma(x_plataforma="1", x_plataforma_token="çãé" * 20)
    assert e.value.status_code == 403


@pytest.mark.asyncio
async def test_fail_open_sem_segredo_configurado(sem_segredo):
    """Fechar junto com o deploy tiraria o super admin do ar."""
    assert await exigir_plataforma(
        x_plataforma="1", x_plataforma_token=None) is None
    assert await exigir_plataforma(
        x_plataforma="1", x_plataforma_token="qualquer") is None


@pytest.mark.asyncio
async def test_fail_open_com_segredo_so_de_um_lado(com_segredo):
    """A janela real do deploy: empresas já tem a env, o gateway ainda não."""
    assert await exigir_plataforma(
        x_plataforma="1", x_plataforma_token=None) is None
