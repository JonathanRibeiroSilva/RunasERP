"""A esteira de CI/CD tem o desenho que o spec de 26/10 manda.

Workflow não roda local, então estes testes leem o YAML e rodam o que dá para rodar
(`scripts/ci-services.sh --listar`). O custo da CI vem do arredondamento por job: oito
jobs de 0,8 min faturam 8 min por run, e um job só com os mesmos oito serviços fatura
menos. Estes testes guardam o formato que mantém essa conta.

Cada card da esteira acrescenta os seus testes aqui, sempre antes do workflow.
"""
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]


def _wf(nome: str) -> dict:
    return yaml.safe_load((REPO / ".github" / "workflows" / nome).read_text(encoding="utf-8"))


def _on(wf: dict) -> dict:
    # PyYAML lê a chave `on:` como o booleano True (YAML 1.1).
    return wf.get("on", wf.get(True))


def _steps(job: dict) -> list:
    return job.get("steps", [])


def _runs(job: dict) -> str:
    return "\n".join(s["run"] for s in _steps(job) if "run" in s)


def _flat(lista) -> list:
    saida = []
    for item in lista:
        saida.extend(_flat(item) if isinstance(item, list) else [item])
    return saida


def _pastas_testadas() -> list:
    """O gateway e todo diretório de services/: o que o script tem de listar."""
    return ["api-gateway"] + sorted(
        f"services/{p.name}" for p in (REPO / "services").iterdir() if p.is_dir()
    )


def test_listar_devolve_gateway_e_todas_as_pastas():
    """Serviço novo em services/ entra na CI sem ninguém lembrar de editar uma lista."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("sem bash neste ambiente")
    # O caminho de which, não o nome: no Windows, "bash" sozinho vira o do WSL.
    saida = subprocess.run(
        [bash, "scripts/ci-services.sh", "--listar"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert saida == _pastas_testadas()


def test_cabe_nos_16_bancos_do_redis():
    """Cada serviço usa um Redis DB próprio (0..15); o 17º serviço não teria onde ficar."""
    assert len(_pastas_testadas()) <= 16


def test_services_e_um_job_so_que_chama_o_script():
    services = _wf("ci.yml")["jobs"]["services"]
    assert "strategy" not in services
    assert "scripts/ci-services.sh" in _runs(services)
    assert services["timeout-minutes"] == 20


def test_build_chama_o_smoke_compartilhado():
    runs = _runs(_wf("ci.yml")["jobs"]["build"])
    assert "scripts/ci-smoke-auth.sh" in runs
    assert "api-gateway-prod" in runs and "vendas-prod" in runs
