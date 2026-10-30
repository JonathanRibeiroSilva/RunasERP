"""A esteira de CI/CD tem o desenho que o spec de 26/10 manda.

Workflow não roda local, então estes testes leem o YAML e rodam o que dá para rodar
(`scripts/ci-services.sh --listar`). O custo da CI vem do arredondamento por job: oito
jobs de 0,8 min faturam 8 min por run, e um job só com os mesmos oito serviços fatura
menos. Estes testes guardam o formato que mantém essa conta.

Cada card da esteira acrescenta os seus testes aqui, sempre antes do workflow.
"""
import os
import re
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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


def test_services_guarda_o_cache_do_pip_entre_runs():
    """Card 112: o cache do pip morria com o run, e o job levava ~3 min só instalando.

    A chave do cache é o hash dos requirements: se um serviço (ou o de teste) ficar de
    fora do `cache-dependency-path`, mexer nos pins dele não invalida o cache.
    """
    passos = [s for s in _steps(_ci()["jobs"]["services"])
              if str(s.get("uses", "")).startswith("actions/setup-python@")]
    assert len(passos) == 1
    com = passos[0]["with"]
    assert com["cache"] == "pip"
    cobertos = {
        p.relative_to(REPO).as_posix()
        for linha in com["cache-dependency-path"].split()
        for p in REPO.glob(linha)
    }
    esperados = {f"{d}/requirements.txt" for d in _pastas_testadas()} | {"tests/requirements.txt"}
    assert cobertos == esperados


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


# --- Card 80: pipeline do merge ----------------------------------------------------

PATHS_IGNORE_DEPLOY = ["landing-page/**", "docs/**", "**.md", ".github/**", "scripts/**"]


def _deploy() -> dict:
    return _wf("deploy.yml")


def _indice(job: dict, trecho: str) -> int:
    """Posição do primeiro step cujo `run` contém o trecho."""
    return next(i for i, s in enumerate(_steps(job)) if trecho in s.get("run", ""))


def test_ci_nao_dispara_em_push():
    """O merge em main é coberto pelo deploy.yml; rodar a CI de novo pagaria duas vezes."""
    assert "push" not in _on(_ci())


def test_deploy_encadeia_test_publish_deploy():
    jobs = _deploy()["jobs"]
    assert set(jobs) == {"test", "publish", "deploy"}
    assert set(jobs["deploy"]["needs"]) >= {"test", "publish"}
    assert jobs["test"]["uses"] == "./.github/workflows/ci.yml"
    assert jobs["test"]["with"] == {"full": True, "build_images": False}


def test_test_concede_o_que_o_ci_pede():
    """O GitHub valida as permissões do workflow chamado ao abrir o run, até as do job pulado."""
    perms = _deploy()["jobs"]["test"]["permissions"]
    assert perms["contents"] == "read"
    assert perms["pull-requests"] == "read"
    assert perms["packages"] == "read"


def test_concurrency_no_workflow_inteiro():
    wf = _deploy()
    assert wf["concurrency"]["group"] == "deploy-production"
    assert wf["concurrency"]["cancel-in-progress"] is False
    assert not any("concurrency" in job for job in wf["jobs"].values())


def test_rollback_manual_pula_test_e_publish_mas_nao_o_deploy():
    """`needs` pulado pula o dependente em silêncio, a não ser que o `if` use status."""
    jobs = _deploy()["jobs"]
    assert "inputs.tag" in jobs["test"]["if"]
    assert "inputs.tag" in jobs["publish"]["if"]
    assert "!failure()" in jobs["deploy"]["if"] and "!cancelled()" in jobs["deploy"]["if"]


def test_latest_so_e_promovido_no_job_deploy():
    jobs = _deploy()["jobs"]
    assert ":latest" not in _runs(jobs["publish"])
    assert "scripts/promote-latest.sh" in _runs(jobs["deploy"])


def test_smoke_roda_antes_do_push_no_publish():
    publish = _deploy()["jobs"]["publish"]
    assert _indice(publish, "ci-smoke-auth.sh") < _indice(publish, "compose $FILES push")


def test_deploy_mantem_paths_ignore():
    push = _on(_deploy())["push"]
    assert push["branches"] == ["main"]
    assert push["paths-ignore"] == PATHS_IGNORE_DEPLOY


def test_health_vem_depois_da_coolify():
    deploy = _deploy()["jobs"]["deploy"]
    assert _indice(deploy, "scripts/coolify-deploy.sh") < _indice(deploy, "scripts/health-ready.sh")


def test_health_usa_user_agent_de_navegador():
    """Sem cara de navegador o Cloudflare desafia o curl e o health vira falso negativo."""
    assert "Mozilla/5.0" in (REPO / "scripts" / "health-ready.sh").read_text(encoding="utf-8")


def _rodar_health(url: str) -> subprocess.CompletedProcess:
    bash, curl = shutil.which("bash"), shutil.which("curl")
    if bash is None or curl is None:
        pytest.skip("sem bash ou curl neste ambiente")
    env = {**os.environ, "HEALTH_TENTATIVAS": "1", "HEALTH_INTERVALO": "0"}
    return subprocess.run(
        [bash, "scripts/health-ready.sh", url],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=60,
    )


def test_health_ready_aceita_200():
    class Ok(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        def log_message(self, *args):
            pass

    servidor = HTTPServer(("127.0.0.1", 0), Ok)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        r = _rodar_health(f"http://127.0.0.1:{servidor.server_port}/")
    finally:
        servidor.shutdown()
    assert r.returncode == 0, r.stdout + r.stderr


def test_health_ready_falha_sem_200():
    """Porta 9 (discard) fechada: o curl não conecta e o script tem de sair com erro."""
    assert _rodar_health("http://127.0.0.1:9/").returncode != 0


def test_nenhum_segredo_dentro_de_run():
    """`${{ secrets.* }}` num run é substituição textual: vira código no shell do runner."""
    for nome in ("ci.yml", "deploy.yml"):
        for job in _wf(nome)["jobs"].values():
            assert "${{ secrets." not in _runs(job), nome


@pytest.mark.parametrize("job,minutos", {"publish": 30, "deploy": 25}.items())
def test_todo_job_do_deploy_tem_timeout(job, minutos):
    # O `test` tem `uses` e não aceita timeout: herda os do ci.yml.
    assert _deploy()["jobs"][job]["timeout-minutes"] == minutos


def test_actions_de_terceiro_pinadas_deploy():
    usos = [s["uses"] for job in _deploy()["jobs"].values() for s in _steps(job) if "uses" in s]
    terceiros = [u for u in usos if not u.startswith(("actions/", "./"))]
    assert terceiros, "esperava ao menos docker/login-action"
    for uso in terceiros:
        assert re.search(r"@[0-9a-f]{40}$", uso), f"{uso} não está pinada por SHA"


# --- Card 103: rollback automático --------------------------------------------------


def _decidir(live: str, arquivos: str) -> str:
    """O que `rollback-decide.sh <live>` responde para a lista de `git diff --name-only`."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("sem bash neste ambiente")
    return subprocess.run(
        [bash, "scripts/rollback-decide.sh", live],
        cwd=REPO, input=arquivos, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _step(job: dict, **campos) -> dict:
    """O step cujo id, ou o `run` que contém o trecho, bate com o pedido."""
    def bate(s):
        return all(
            (s.get(k) == v) if k == "id" else (v in s.get(k, ""))
            for k, v in campos.items()
        )
    return next(s for s in _steps(job) if bate(s))


def _posicao(job: dict, step: dict) -> int:
    return next(i for i, s in enumerate(_steps(job)) if s is step)


def test_decide_sem_producao():
    """Sem sha no ar registrado não há para onde voltar: o script avisa em vez de reverter."""
    assert _decidir("", "") == "sem-producao"


def test_decide_migration():
    assert _decidir("abc", "services/vendas/alembic/versions/0007_x.py\n") == "migration"
    assert _decidir("abc", "README.md\napi-gateway/alembic/versions/a.py\n") == "migration"


def test_decide_reverter():
    """alembic.ini e env.py não são migration: só `versions/` muda o schema."""
    assert _decidir("abc", "services/vendas/main.py\nservices/vendas/alembic.ini\n") == "reverter"


def test_ensaio_rollback_e_boolean_de_dispatch():
    campo = _on(_deploy())["workflow_dispatch"]["inputs"]["ensaio_rollback"]
    assert campo["type"] == "boolean"


def test_deploy_busca_o_historico():
    """Sem o histórico completo o `git diff <live> <sha>` não acha o sha antigo."""
    checkout = next(s for s in _steps(_deploy()["jobs"]["deploy"]) if "actions/checkout" in s.get("uses", ""))
    assert checkout["with"]["fetch-depth"] == 0


def test_so_o_deploy_grava_o_sha_no_ar():
    """`deployments: write` é só para registrar o sha no ar; nenhum job escreve no repositório."""
    wf = _deploy()
    assert wf["permissions"] == {"contents": "read"}
    for nome, job in wf["jobs"].items():
        perms = job.get("permissions", {})
        assert perms.get("contents") != "write", nome
        assert (perms.get("deployments") == "write") == (nome == "deploy"), nome


def test_health_continua_para_o_rollback_decidir():
    assert _step(_deploy()["jobs"]["deploy"], id="health")["continue-on-error"] is True


def test_producao_so_e_gravada_depois_do_health():
    deploy = _deploy()["jobs"]["deploy"]
    marca = _step(deploy, run="production-sha.sh set")
    assert _posicao(deploy, marca) > _posicao(deploy, _step(deploy, id="health"))
    assert "steps.health.outcome == 'success'" in marca["if"]


def test_sha_no_ar_nao_anda_por_tag_git():
    """Card 114: mover a tag para tras, por `git push` ou pela API, é recusado ao
    GITHUB_TOKEN quando o .github/workflows dos dois shas difere; o rollback manual
    ficava vermelho. Um deployment é só um registro, aceita qualquer sha."""
    deploy = _deploy()["jobs"]["deploy"]
    assert "GH_TOKEN" in _step(deploy, run="production-sha.sh set")["run"]
    assert "git push" not in _runs(deploy) and "refs/tags" not in _runs(deploy)
    script = (REPO / "scripts" / "production-sha.sh").read_text(encoding="utf-8")
    assert "/git/refs" not in script and "environment: \"production\"" in script


def test_live_e_lido_antes_de_promover():
    """O sha lido depois da promoção já seria o novo."""
    deploy = _deploy()["jobs"]["deploy"]
    live = _step(deploy, id="live")
    assert _posicao(deploy, live) < _posicao(deploy, _step(deploy, id="promote"))
    assert "production-sha.sh get" in live["run"]


def test_sha_no_ar_pula_deployment_sem_success(tmp_path):
    """Um `set` que morreu no meio deixa um deployment sem status: não é o que está no ar."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("sem bash neste ambiente")
    gh = tmp_path / "gh"
    gh.write_text(
        r"""#!/usr/bin/env bash
case "$*" in
  *deployments?environment=production*) printf '30 sha-novo\n20 sha-bom\n10 sha-velho\n' ;;
  */deployments/30/statuses*) echo in_progress ;;
  */deployments/20/statuses*) echo success ;;
  *) exit 1 ;;
esac
""",
        encoding="utf-8", newline="\n",
    )
    gh.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}", "GITHUB_REPOSITORY": "o/r"}
    saida = subprocess.run(
        [bash, "scripts/production-sha.sh", "get"], cwd=REPO, env=env, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert saida == "sha-bom"


def test_rollback_so_roda_quando_o_health_falha():
    deploy = _deploy()["jobs"]["deploy"]
    rollback = _step(deploy, run="rollback-decide.sh")
    assert "steps.health.outcome == 'failure'" in rollback["if"]
    assert "git diff --name-only" in rollback["run"]
    # Reaproveita os scripts do card 80 e termina sempre vermelho.
    for script in ("promote-latest.sh", "coolify-deploy.sh", "health-ready.sh"):
        assert script in rollback["run"], script
    assert rollback["run"].rstrip().endswith("exit 1")


def test_dispatch_recusa_tag_que_nao_e_sha_completo():
    """Card 115: as imagens levam `github.sha` inteiro. O sha curto (`8d4f77c`) passava por
    checkout, login e leitura do sha no ar e só morria no promote, com `not found`."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("sem bash neste ambiente")
    deploy = _deploy()["jobs"]["deploy"]
    passo = _steps(deploy)[0]
    assert passo["if"] == "${{ inputs.tag }}"  # push usa github.sha, que já é completo
    assert "FULL sha (40" in _on(_deploy())["workflow_dispatch"]["inputs"]["tag"]["description"]

    def rodar(tag: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [bash, "-c", passo["run"]], env={**os.environ, **passo["env"], "INPUT_TAG": tag},
            capture_output=True, text=True,
        )

    assert rodar("a" * 40).returncode == 0
    for ruim in ("8d4f77c", "A" * 40, "a" * 39, "a" * 41, "a" * 40 + "\nfoo", "../" + "a" * 37):
        r = rodar(ruim)
        assert r.returncode != 0, ruim
        assert "40" in r.stdout, ruim  # a mensagem diz o que se espera


def test_ensaio_aponta_o_primeiro_health_para_um_caminho_inexistente():
    health = _step(_deploy()["jobs"]["deploy"], id="health")
    assert "ensaio_rollback" in str(health["env"]) + health["run"]
    assert "-ensaio-inexistente" in str(health["env"]) + health["run"]
