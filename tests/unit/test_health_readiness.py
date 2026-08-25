"""O readiness precisa reprovar em 503 e dizer quem caiu.

/health devolvia {"status": "healthy"} com o Postgres morto, o Redis morto e os
sete serviços mortos — a sonda de produção perguntava só "o processo do FastAPI
subiu?". Este teste guarda a decisão nova: 200 apenas quando tudo responde, 503
nomeando o culpado quando não.

Importa health.py direto, sem passar por main.py: o gate do CI instala apenas
tests/requirements.txt (sem fastapi, sem sqlalchemy), então importar o app aqui
derrubaria a suíte inteira na coleta.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "api-gateway"))

from health import SERVICE_NAMES, summarize  # noqa: E402


def _up(nome):
    return {"name": nome, "status": "up"}


def test_tudo_no_ar_devolve_200():
    codigo, corpo = summarize([_up("postgres"), _up("redis"), _up("vendas")])
    assert codigo == 200
    assert corpo["status"] == "healthy"
    assert corpo["down"] == []


def test_uma_dependencia_fora_devolve_503_nomeando_o_culpado():
    checks = [
        _up("postgres"),
        {"name": "financeiro", "status": "down", "error": "TimeoutError"},
    ]
    codigo, corpo = summarize(checks)
    assert codigo == 503, "200 degradado não dispara alarme na sonda externa"
    assert corpo["down"] == ["financeiro"]
    assert corpo["status"] == "degraded"


def test_todo_servico_interno_e_sondado():
    """Serviço novo no config.py sem sonda no readiness é ponto cego novo."""
    config = (REPO / "api-gateway" / "config.py").read_text(encoding="utf-8")
    obrigatorios = {n.lower() for n in re.findall(r"^    (\w+)_URL: str$", config, re.M)}
    # database e redis têm sonda própria em main.py; não entram em SERVICE_NAMES.
    esperado = obrigatorios - {"database", "redis"}
    assert esperado == set(SERVICE_NAMES), (
        f"config.py e SERVICE_NAMES divergem: {esperado ^ set(SERVICE_NAMES)}"
    )
