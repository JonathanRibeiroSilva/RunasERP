"""
Wiring do G1b — o que some calado se alguém desfizer.

A lógica de `exigir_plataforma` tem teste de verdade em
`services/empresas/tests/test_plataforma_com_prova.py`. O que não cabe lá é o
outro lado: o gateway carimbando, o proxy limpando, e o segredo chegando em
exatamente DOIS containers.

O escopo é o ponto do fix. Espalhar `PLATAFORMA_INTERNO_TOKEN` para os 8 o
tornaria idêntico ao `SERVICO_INTERNO_TOKEN` e reabriria o achado sem que
nenhum teste de lógica percebesse.
"""
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


def test_gateway_carimba_o_token():
    """Sem o carimbo, fechar a guarda do empresas derruba o super admin."""
    fonte = (RAIZ / "api-gateway" / "routers" / "plataforma.py").read_text(
        encoding="utf-8")
    # Linha comentada não carimba nada.
    ativas = [l.strip() for l in fonte.splitlines()
              if not l.strip().startswith("#")]
    assert any('headers["X-Plataforma-Token"]' in l for l in ativas), (
        "o router /plataforma parou de carimbar PLATAFORMA_INTERNO_TOKEN"
    )


def test_cliente_nao_forja_o_header():
    """
    O gateway remove x-plataforma-token do que chega de fora, junto dos outros
    headers de contexto — senão o cliente traz a própria prova e o fix é nulo.
    """
    fonte = (RAIZ / "api-gateway" / "proxy" / "service_proxy.py").read_text(
        encoding="utf-8")
    bloco = fonte[fonte.index("for interno in ("):]
    bloco = bloco[:bloco.index("headers.pop")]
    assert '"x-plataforma-token"' in bloco, (
        "service_proxy não remove x-plataforma-token do request do cliente"
    )


@pytest.mark.parametrize("compose",
                         ["docker-compose.prod.yml", "docker-compose.dev.yml"])
def test_segredo_so_nos_dois_containers(compose):
    yaml = pytest.importorskip("yaml")
    servicos = yaml.safe_load(
        (RAIZ / compose).read_text(encoding="utf-8"))["services"]
    com_token = {
        nome for nome, spec in servicos.items()
        if isinstance(spec, dict)
        and "PLATAFORMA_INTERNO_TOKEN" in (spec.get("environment") or {})
    }
    assert len(com_token) == 2, (
        f"{compose}: {sorted(com_token)} — esperado exatamente 2 "
        f"(gateway e empresas). Espalhar para os 8 reabre o G1b."
    )


def test_empresas_le_o_segredo():
    cfg = (RAIZ / "services" / "empresas" / "config.py").read_text(encoding="utf-8")
    assert "PLATAFORMA_INTERNO_TOKEN" in cfg
