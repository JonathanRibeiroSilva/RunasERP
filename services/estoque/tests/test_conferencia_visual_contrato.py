"""Contrato da conferência visual: o que o servidor aceita e o que recusa.

Sem banco: o endpoint não toca o Postgres, então a rota é chamada por um client
próprio, sem a fixture `db` do conftest (que abre transação no Postgres). Roda
em qualquer máquina que tenha as dependências do serviço.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from interno import auth_interno
from main import app

from schemas.conferencia_visual import (
    COCO_ROTULOS,
    MAX_DETECCOES,
    CaixaDelimitadora,
    ConferenciaVisualRequest,
)



@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", headers=auth_interno()
    ) as c:
        yield c


CAIXA = {"x": 0.1, "y": 0.2, "largura": 0.3, "altura": 0.4}


def _req(**campos):
    base = {"modelo": "coco-ssd", "versao_modelo": "2.2.3", "detecoes": []}
    return {**base, **campos}


def _det(rotulo="bottle", confianca=0.9, caixa=CAIXA):
    return {"rotulo": rotulo, "confianca": confianca, "caixa": caixa}


def test_tem_as_80_classes_do_coco():
    assert len(COCO_ROTULOS) == 80


def test_payload_valido_passa():
    r = ConferenciaVisualRequest(**_req(detecoes=[_det()]))
    assert r.detecoes[0].caixa.largura == 0.3


@pytest.mark.parametrize(
    "caixa",
    [
        {"x": 0.8, "y": 0.0, "largura": 0.5, "altura": 0.5},   # passa da borda direita
        {"x": 0.0, "y": 0.9, "largura": 0.5, "altura": 0.2},   # passa da borda de baixo
        {"x": -0.1, "y": 0.0, "largura": 0.5, "altura": 0.5},  # fora à esquerda
        {"x": 0.0, "y": 0.0, "largura": 0.0, "altura": 0.5},   # sem área
        {**CAIXA, "extra": 1},                                  # campo desconhecido
    ],
)
def test_caixa_invalida_e_recusada(caixa):
    with pytest.raises(ValidationError):
        CaixaDelimitadora(**caixa)


def test_caixa_encostada_na_borda_passa():
    CaixaDelimitadora(x=0.5, y=0.5, largura=0.5, altura=0.5)


@pytest.mark.parametrize("confianca", [-0.01, 1.01])
def test_confianca_fora_de_0_a_1_e_recusada(confianca):
    with pytest.raises(ValidationError):
        ConferenciaVisualRequest(**_req(detecoes=[_det(confianca=confianca)]))


def test_rotulo_fora_do_coco_e_recusado():
    with pytest.raises(ValidationError):
        ConferenciaVisualRequest(**_req(detecoes=[_det(rotulo="caixa de leite")]))


def test_modelo_desconhecido_e_recusado():
    with pytest.raises(ValidationError):
        ConferenciaVisualRequest(**_req(modelo="yolo"))


def test_lista_acima_do_limite_e_recusada():
    with pytest.raises(ValidationError):
        ConferenciaVisualRequest(**_req(detecoes=[_det()] * (MAX_DETECCOES + 1)))


@pytest.mark.asyncio
async def test_rota_resume_so_o_que_passa_do_limiar(client):
    corpo = _req(detecoes=[_det("bottle", 0.9), _det("bottle", 0.6), _det("cup", 0.4)])
    r = await client.post("/estoque/conferencia-visual", json=corpo, headers={"X-Empresa-Id": "1"})
    assert r.status_code == 200
    assert r.json() == {
        "total_detectado": 3,
        "total_aceito": 2,
        "limiar_confianca": 0.5,
        "contagem_por_rotulo": {"bottle": 2},
    }


@pytest.mark.asyncio
async def test_rota_devolve_422_para_payload_fora_do_contrato(client):
    corpo = _req(detecoes=[_det(rotulo="inventado")])
    r = await client.post("/estoque/conferencia-visual", json=corpo, headers={"X-Empresa-Id": "1"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rota_exige_empresa(client):
    r = await client.post("/estoque/conferencia-visual", json=_req())
    assert r.status_code == 422
