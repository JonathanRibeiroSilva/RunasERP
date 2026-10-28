"""A esteira de CI/CD tem o desenho que o spec de 26/10 manda.

Workflow não roda local, então estes testes leem o YAML e rodam o que dá para rodar
(`scripts/ci-services.sh --listar`). O custo da CI vem do arredondamento por job: oito
jobs de 0,8 min faturam 8 min por run, e um job só com os mesmos oito serviços fatura
menos. Estes testes guardam o formato que mantém essa conta.

Cada card da esteira acrescenta os seus testes aqui, sempre antes do workflow.
"""
import re
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


# --- Card 102: CI do PR escopada ---------------------------------------------------

JOBS_QUE_ESPERAM_O_CHECKS = ["services", "build", "frontend", "migration-replay"]

# Minutos, por job: a conta que o card 102 fecha contra o job travado de 360 min.
TIMEOUTS_CI = {
    "checks": 10, "services": 20, "frontend": 15, "build": 30, "migration-replay": 20,
}


def _ci() -> dict:
    return _wf("ci.yml")


def _filtros() -> dict:
    """O `filters` do step dorny/paths-filter, já como dict."""
    step = next(
        s for s in _steps(_ci()["jobs"]["checks"])
        if str(s.get("uses", "")).startswith("dorny/paths-filter@")
    )
    return yaml.safe_load(step["with"]["filters"])


def _chaves_do_build() -> list:
    compose = yaml.safe_load((REPO / "docker-compose.build.yml").read_text(encoding="utf-8"))
    return list(compose["services"])


def _chaves_publicas(filtros: dict) -> set:
    # As chaves com `_` são só âncoras do YAML, não saídas do filtro.
    return {k for k in filtros if not k.startswith("_")}


def _globs(filtros: dict, chave: str) -> set:
    return set(_flat(filtros[chave]))


def test_pr_so_para_developer():
    assert _on(_ci())["pull_request"]["branches"] == ["Developer"]


def test_workflow_call_tem_full_e_build_images():
    inputs = _on(_ci())["workflow_call"]["inputs"]
    assert inputs["full"]["type"] == "boolean" and inputs["full"]["default"] is False
    assert inputs["build_images"]["type"] == "boolean" and inputs["build_images"]["default"] is True
    assert "workflow_dispatch" in _on(_ci())


def test_jobs_dependem_do_checks():
    jobs = _ci()["jobs"]
    assert "backend" not in jobs and "compose" not in jobs
    for nome in JOBS_QUE_ESPERAM_O_CHECKS:
        needs = jobs[nome]["needs"]
        assert "checks" in ([needs] if isinstance(needs, str) else needs), nome
        # Sem isso, um `checks` pulado/cancelado deixaria o job dependente rodar à toa.
        assert "!cancelled()" in jobs[nome]["if"], nome


def test_filtros_batem_com_as_pastas_e_imagens():
    """Serviço novo sem filtro nunca seria testado no PR: este teste quebra antes."""
    esperado = set(_pastas_testadas()) | set(_chaves_do_build()) | {"frontend", "migrations"}
    assert _chaves_publicas(_filtros()) == esperado


def test_filtros_compartilhados():
    f = _filtros()
    compartilhado_servico = {
        "postgres/**", "tests/requirements.txt",
        ".github/workflows/ci.yml", "scripts/ci-services.sh",
    }
    for pasta in _pastas_testadas():
        assert _globs(f, pasta) >= {f"{pasta}/**"} | compartilhado_servico, pasta

    compartilhado_imagem = {
        "docker-compose.prod.yml", "docker-compose.build.yml", ".env.production.example",
        ".github/workflows/ci.yml", "scripts/ci-smoke-auth.sh",
    }
    for chave in _chaves_do_build():
        nome = chave.removesuffix("-prod")
        pasta = nome if nome in ("api-gateway", "frontend") else f"services/{nome}"
        assert _globs(f, chave) >= {f"{pasta}/**"} | compartilhado_imagem, chave

    assert ".github/workflows/ci.yml" in _globs(f, "frontend")
    # `*` não cruza `/` no picomatch: `*/alembic/**` não pegaria services/x/alembic.
    assert _globs(f, "migrations") == {
        "**/alembic/**", "**/database.py", "postgres/**",
        "docker-compose.dev.yml", ".github/workflows/ci.yml",
    }


def test_replay_em_pr_so_com_migration():
    cond = _ci()["jobs"]["migration-replay"]["if"]
    assert "github.event_name != 'pull_request'" in cond
    assert "needs.checks.outputs.migrations == 'true'" in cond


def test_concurrency_cancela_so_no_pr():
    conc = _ci()["concurrency"]
    assert "pull_request" in conc["group"] and "run_id" in conc["group"]
    assert "pull_request" in str(conc["cancel-in-progress"])


def test_build_loga_no_ghcr_so_leitura():
    build = _ci()["jobs"]["build"]
    assert build["permissions"]["packages"] == "read"
    assert any(str(s.get("uses", "")).startswith("docker/login-action@") for s in _steps(build))


def test_ci_declara_permissao_minima_no_topo():
    assert _ci()["permissions"] == {"contents": "read"}


@pytest.mark.parametrize("job,minutos", TIMEOUTS_CI.items())
def test_todo_job_do_ci_tem_timeout(job, minutos):
    assert _ci()["jobs"][job]["timeout-minutes"] == minutos
    assert set(_ci()["jobs"]) == set(TIMEOUTS_CI)


def test_actions_de_terceiro_pinadas_ci():
    usos = [
        s["uses"] for job in _ci()["jobs"].values() for s in _steps(job) if "uses" in s
    ]
    terceiros = [u for u in usos if not u.startswith(("actions/", "./"))]
    assert terceiros, "esperava ao menos dorny/paths-filter e docker/login-action"
    for uso in terceiros:
        assert re.search(r"@[0-9a-f]{40}$", uso), f"{uso} não está pinada por SHA"
