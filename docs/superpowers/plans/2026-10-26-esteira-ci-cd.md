# Esteira de CI/CD: plano de implementação

> **Para quem executa:** cada Task é um card do Trello, feito num chat próprio. Use
> `superpowers:executing-plans` (execução nativa; subagente só se o usuário pedir) e a skill `card-telemetria`,
> com a est e o teto do comentário do card. Os passos usam checkbox (`- [ ]`).

**Objetivo:** a CI do PR roda só o que o diff toca, em poucos jobs; o merge em main testa tudo antes do deploy, só
promove `:latest` depois de tudo verde, confere a saúde de produção e reverte sozinho quando é seguro.

**Arquitetura:** `ci.yml` vira reutilizável e tem um job `checks`, que filtra por path e decide o escopo. Os legs
rodam em sequência num job, pelo `scripts/ci-services.sh`. O `deploy.yml` faz `test` (chama o `ci.yml`) ∥
`publish` → `deploy`. A lógica de shell sai para `scripts/*.sh`, pequenos e testáveis. Um teste estrutural em
`tests/unit` trava o desenho.

**Tecnologias:** GitHub Actions, `dorny/paths-filter` v4.0.3, `docker/login-action` v4.7.0,
`docker buildx imagetools`, bash, pytest + PyYAML (padrão de `tests/unit/test_backup_antes_da_migration.py`).

**Spec:** `docs/superpowers/specs/2026-10-26-esteira-ci-cd-design.md`. Os números de custo vêm de
`docs/superpowers/audits/2026-10-26-ci-cd/achados.md`.

## Restrições globais

- **Nada de commit, merge ou push sem pedido explícito do usuário.** Onde o passo diz "commit", sugira a mensagem
  (Conventional Commits, em inglês) e pare.
- **Uma Task por chat.** O worktree fica em `.claude/worktrees/<nome>`, criado a partir de `origin/Developer`
  (`git worktree add .claude/worktrees/<nome> -b <branch> origin/Developer`). O PR tem base `Developer` (a CI não
  roda em PR empilhado). Nunca toque a checkout principal (branch `feat/reconhecer-produto-tm`).
- **Spec e plano no worktree:** se não estiverem em `origin/Developer`, copie-os da checkout principal, onde estão
  não versionados. O PR da Task 1 os versiona.
- **O que roda local:** `python -m pytest -c tests/pytest.ini tests/unit -q`, `bash -n scripts/<x>.sh` e
  `python -c "import yaml; yaml.safe_load(open('<arquivo>'))"`. Workflow, Docker e Postgres não rodam aqui: diga no
  fim o que não foi executado.
- **Nunca abra `.env` real.**
- **Comentários em YAML e shell:** em inglês, explicando o porquê, como nos arquivos atuais.
- **Actions:** as `actions/*` vão por major (`@v7`). As de terceiro vão por SHA de 40 hex, com a tag em comentário.
  Para resolver o SHA, rode `gh api repos/<dono>/<repo>/git/ref/tags/<tag> --jq .object`; se `type == "tag"`, siga
  com `gh api repos/<dono>/<repo>/git/tags/<sha> --jq .object.sha`.
- **Segredos:** nunca `${{ secrets.* }}` dentro de `run:`. Passe por `env:` e leia como `"$X"`.
- **`paths-ignore` do `deploy.yml`:** `landing-page/**`, `docs/**`, `**.md`, `.github/**`, `scripts/**`. Não muda.
- **`timeout-minutes` (min):** `checks` 10, `services` 20, `frontend` 15, `build` 30, `migration-replay` 20,
  `publish` 30, `deploy` 25. Job com `uses:` não aceita `timeout-minutes`.
- **Globs:** no `paths-filter` (picomatch), `*` não cruza `/`; use `**/alembic/**`. No pathspec do `git diff`, `*`
  cruza `/`, então `'*/alembic/versions/*'` pega `services/x/alembic/versions/y.py`.
- **`tests/unit/test_pipeline_ci_deploy.py` cresce a cada Task, sempre antes do workflow.** Helpers comuns (Task 1):
  - `_wf(nome)`: `yaml.safe_load` de `.github/workflows/<nome>`;
  - `_on(wf)`: `wf.get("on", wf.get(True))`;
  - `_steps(job)`;
  - `_runs(job)`: junta os `run` dos steps;
  - `_flat(lista)`: achata listas aninhadas.
- **Fechamento:** PR com descrição detalhada, commit a commit, e o card movido e comentado no Trello.

## Foco de revisão

1. Serviço novo em `services/` sem filtro ou fora da lista nunca é testado no PR (Task 1
   `test_listar_devolve_gateway_e_todas_as_pastas`; Task 2 `test_filtros_batem_com_as_pastas_e_imagens`).
2. Mais de 16 serviços estouram os bancos do Redis (0..15) (Task 1 `test_cabe_nos_16_bancos_do_redis`).
3. O Cloudflare desafia o health check sem cara de navegador, e isso dispara um rollback falso (Task 3
   `test_health_usa_user_agent_de_navegador`).
4. Um `needs` pulado pula o `deploy` em silêncio no rollback manual (Task 3
   `test_rollback_manual_pula_test_e_publish_mas_nao_o_deploy`).
5. Sem a tag `producao`, o rollback automático precisa avisar em vez de reverter para lugar nenhum (Task 4
   `test_decide_sem_producao`).

---

### Task 1 (card 79): legs num job só + smoke compartilhado

**Arquivos:**
- Criar: `scripts/ci-services.sh`, `scripts/ci-smoke-auth.sh`, `tests/unit/test_pipeline_ci_deploy.py`
- Modificar: `.github/workflows/ci.yml` (jobs `services` e `build`; o resto não muda)

**Interfaces (produz):**
- `scripts/ci-services.sh --listar`: imprime `api-gateway` e depois `services/<pasta>` para cada pasta de
  `services/`, uma por linha, em ordem alfabética.
- `scripts/ci-services.sh [<dir>...]`: sem argumentos equivale à lista do `--listar`.
  - Para o i-ésimo serviço (base 0), com `nome` = basename com `-` → `_`:
    - `createdb -h localhost -U erp erp_<nome>`;
    - `DATABASE_URL=postgresql+asyncpg://erp:erp@localhost:5432/erp_<nome>` e `REDIS_URL=redis://localhost:6379/<i>`;
    - venv em `${RUNNER_TEMP:-/tmp}/venv-<nome>` e `pip install -q -r <dir>/requirements.txt -r tests/requirements.txt`;
    - `psql -h localhost -U erp -d erp_<nome> -v ON_ERROR_STOP=1 -q -f postgres/init-schemas.sql`;
    - `(cd <dir> && alembic upgrade head && pytest tests -p no:cacheprovider)`, num subshell com `set -e`.
  - Cada serviço fica dentro de `::group::<dir>` / `::endgroup::`.
  - Anota ok ou FALHOU, segue para o próximo, imprime a tabela (e a anexa a `$GITHUB_STEP_SUMMARY` se existir) e
    sai com 1 se algum falhou. Recusa mais de 16 serviços com mensagem.
- `scripts/ci-smoke-auth.sh <env-file> <servico-prod>...`: o corpo do step "Smoke-test auth primitives" de hoje
  (`ci.yml`, job `build`), com a lista e o `--env-file` vindos dos argumentos. `set -euo pipefail`.

- [ ] **Step 1: Worktree** `.claude/worktrees/ci-legs-num-job` (branch `ci/legs-num-job`), com a cópia do spec e do
  plano. Linha de base: `python -m pytest -c tests/pytest.ini tests/unit -q`. Anote a contagem.
- [ ] **Step 2: Escrever o teste** com os helpers comuns:
  - `test_listar_devolve_gateway_e_todas_as_pastas`: `subprocess.run(["bash", "scripts/ci-services.sh",
    "--listar"])` == `["api-gateway"] + sorted(f"services/{p.name}" for p in (REPO/"services").iterdir() if
    p.is_dir())`. Use `pytest.skip` só se `shutil.which("bash")` for `None`.
  - `test_cabe_nos_16_bancos_do_redis`: a lista acima tem `<= 16` itens.
  - `test_services_e_um_job_so_que_chama_o_script`: `"strategy" not in ci["jobs"]["services"]`;
    `"scripts/ci-services.sh" in _runs(services)`; `services["timeout-minutes"] == 20`.
  - `test_build_chama_o_smoke_compartilhado`: `"scripts/ci-smoke-auth.sh" in _runs(build)`, e o comando cita
    `api-gateway-prod` e `vendas-prod`.
- [ ] **Step 3: Rodar** `python -m pytest -c tests/pytest.ini tests/unit/test_pipeline_ci_deploy.py -q`. Esperado:
  FALHA em todos.
- [ ] **Step 4: Escrever os dois scripts** conforme as Interfaces. No `ci.yml`:
  - job `services`: sai `strategy`/`matrix` e o `defaults.run.working-directory`; saem `DATABASE_URL` e `REDIS_URL`
    do `env:` (o script define); entram `PGHOST: localhost` e `PGUSER: erp`; os steps viram checkout,
    `setup-python 3.12` e `bash scripts/ci-services.sh`; `timeout-minutes: 20`;
  - job `build`: o step de smoke vira `bash scripts/ci-smoke-auth.sh .env.production.example api-gateway-prod
    vendas-prod`.
  Mantenha os comentários que explicam o porquê (imports planos, um processo do pytest por serviço) junto do job.
- [ ] **Step 5: Verificar.** O teste passa, `bash -n` passa nos dois scripts, o YAML faz parse e a suíte `tests/unit`
  inteira passa (compare com a contagem do Step 1).
- [ ] **Step 6: Commit** (só com pedido): `ci: run the eight service legs in one job through a shared script`.
  O PR versiona também o spec e o plano. Prova no PR: o job `services` roda os 8 legs, e a soma dos `passed` bate
  com a de hoje (223 nos legs, `achados.md`).

---

### Task 2 (card 102): CI do PR escopada

**Arquivos:**
- Modificar: `.github/workflows/ci.yml`, `tests/unit/test_pipeline_ci_deploy.py`

**Interfaces:**
- Consome: `scripts/ci-services.sh --listar` e `[<dir>...]`, e `scripts/ci-smoke-auth.sh` (Task 1).
- Produz:
  - `workflow_call.inputs`: `full` (boolean, padrão `false`) e `build_images` (boolean, padrão `true`);
  - saídas do job `checks`: `services` (dirs separados por espaço, ex. `api-gateway services/estoque`), `images`
    (chaves do `docker-compose.build.yml` separadas por espaço, ex. `estoque-prod frontend-prod`), `frontend` e
    `migrations` (`'true'`/`'false'`).

- [ ] **Step 1: Worktree** `.claude/worktrees/ci-escopada` (branch `ci/escopada`) a partir de `origin/Developer`,
  já com a Task 1.
- [ ] **Step 2: Escrever os testes:**
  - `test_pr_so_para_developer`: `_on(ci)["pull_request"]["branches"] == ["Developer"]`.
  - `test_workflow_call_tem_full_e_build_images`: os dois inputs existem, com `type == "boolean"`.
  - `test_jobs_dependem_do_checks`: `services`, `build`, `frontend` e `migration-replay` têm `checks` em `needs`,
    e o `if` de cada um contém `!cancelled()`. Os jobs antigos `backend` e `compose` não existem.
  - `test_filtros_batem_com_as_pastas_e_imagens`: carregue o `filters` do step `dorny/paths-filter` com
    `yaml.safe_load`. As chaves que não começam com `_` == lista do `--listar` ∪ chaves de `docker-compose.build.yml`
    ∪ `{"frontend", "migrations"}`.
  - `test_filtros_compartilhados`: com `_flat`, verifique:
    - cada serviço tem o próprio `<dir>/**` mais `postgres/**`, `tests/requirements.txt`,
      `.github/workflows/ci.yml` e `scripts/ci-services.sh`;
    - cada imagem tem a própria pasta (`api-gateway-prod` → `api-gateway/**`, `<s>-prod` → `services/<s>/**`,
      `frontend-prod` → `frontend/**`) mais `docker-compose.prod.yml`, `docker-compose.build.yml`,
      `.env.production.example`, `.github/workflows/ci.yml` e `scripts/ci-smoke-auth.sh`;
    - `frontend` contém `.github/workflows/ci.yml`;
    - `migrations` == `{"**/alembic/**", "**/database.py", "postgres/**", "docker-compose.dev.yml",
      ".github/workflows/ci.yml"}`.
  - `test_replay_em_pr_so_com_migration`: o `if` do `migration-replay` contém `github.event_name !=
    'pull_request'` e `needs.checks.outputs.migrations == 'true'`.
  - `test_concurrency_cancela_so_no_pr`: o `concurrency` do topo tem `group` com `pull_request` e `run_id`, e
    `cancel-in-progress` com `pull_request`.
  - `test_build_loga_no_ghcr_so_leitura`: `build["permissions"]["packages"] == "read"`, e um step usa
    `docker/login-action`.
  - `test_todo_job_do_ci_tem_timeout`: parametrize pelos jobs do `ci.yml`, comparando com os valores das
    Restrições globais.
  - `test_actions_de_terceiro_pinadas_ci`: todo `uses` fora de `actions/` e `./` casa `@[0-9a-f]{40}$`.
- [ ] **Step 3: Rodar** o teste. Esperado: FALHA nos testes novos.
- [ ] **Step 4: Implementar no `ci.yml`:**
  - **Gatilhos:** `pull_request.branches: [Developer]`. O `push` fica como está, porque a Task 3 o tira.
    Entram `workflow_dispatch: {}` e `workflow_call` com os dois inputs.
  - **`concurrency` no topo:** `group: ${{ github.event_name == 'pull_request' && format('ci-pr-{0}',
    github.event.pull_request.number) || github.run_id }}` e `cancel-in-progress: ${{ github.event_name ==
    'pull_request' }}`. Antes, confira na doc de reusable workflows como o `concurrency` do workflow chamado se
    comporta. Se houver dúvida, aplique o mesmo `concurrency` nos jobs, com o mesmo `group`.
  - **`checks`:**
    - checkout e `setup-python 3.12` + `pip install -r tests/requirements.txt`;
    - `dorny/paths-filter` (pinado, `id: filter`, `if: github.event_name == 'pull_request'`, sem secrets). O
      `filters` tem âncoras `_svc`/`_img`, e as chaves são os próprios valores: `api-gateway`,
      `services/<pasta>`, `<chave>-prod`, `frontend`, `migrations`;
    - step `id: scope`, com `EVENT`, `FULL` e `CHANGES` (`steps.filter.outputs.changes`) por `env:`:
      - se `EVENT != pull_request` ou `FULL == true`: `services` = `--listar` unido por espaço, `images` = chaves
        do build (via PyYAML), `frontend` e `migrations` = `true`;
      - senão, `jq` sobre `CHANGES`: `services` = itens `== "api-gateway"` ou que começam com `services/`;
        `images` = itens que terminam em `-prod`; `frontend` e `migrations` pela presença da chave;
    - os dois `docker compose config` de hoje e `pytest -c tests/pytest.ini tests/unit`.
  - **Demais jobs:**
    - `services`: `bash scripts/ci-services.sh $SERVICES`, com `SERVICES` vindo de `env:`;
    - `build`: `permissions: {contents: read, packages: read}`, login no ghcr pinado e `docker compose ... build
      $IMAGES`. O smoke recebe a interseção de `{api-gateway-prod, vendas-prod}` com `IMAGES` e é pulado se ela
      ficar vazia;
    - `frontend`: o corpo de hoje;
    - `migration-replay`: o corpo de hoje.

    Todos levam `needs: checks` e `if: ${{ !cancelled() && ... }}`. Saem os jobs `backend` e o validador de
    compose do topo do `build`.
  - **Timeouts** em todos os jobs.
  - **`permissions: {contents: read}` no topo** (achado C10). O `build` sobrescreve com `packages: read`. Teste:
    `test_ci_declara_permissao_minima_no_topo`.
- [ ] **Step 5: Verificar.** O teste passa, o YAML faz parse e a suíte `tests/unit` passa.
- [ ] **Step 6: Commit** (só com pedido): `ci: scope PR checks to the changed paths and make ci.yml reusable`.
  Prova no PR: como o `ci.yml` mudou, tudo roda uma vez, inclusive o replay. Depois do merge, rode um PR só em
  `services/estoque` (`checks` + `services` + `build` do estoque) e um PR só de docs (só `checks`).

---

### Task 3 (card 80): pipeline do merge

**Arquivos:**
- Criar: `scripts/promote-latest.sh`, `scripts/coolify-deploy.sh`, `scripts/health-ready.sh`
- Modificar: `.github/workflows/deploy.yml`, `.github/workflows/ci.yml` (sai o `push`),
  `tests/unit/test_pipeline_ci_deploy.py`

**Interfaces:**
- Consome: `ci.yml` via `workflow_call` com `full: true` e `build_images: false` (Task 2), e `scripts/ci-smoke-auth.sh`.
- Produz:
  - `scripts/promote-latest.sh <sha>`: para cada imagem `ghcr.io/` de `docker compose $FILES config --images` (com
    `TAG=<sha>`), roda `docker buildx imagetools create -t <img>:latest <img>:<sha>`. Exige o `.env` de build e
    `FILES` no ambiente;
  - `scripts/coolify-deploy.sh`: o corpo exato dos steps "Trigger Coolify deploy" + "Wait for Coolify to finish
    the deploy" de hoje (retry, `-A Mozilla…`, tolerância a 530, 90×10 s, 45 inalcançáveis, log na falha). Lê
    `COOLIFY_URL`, `COOLIFY_TOKEN` e `COOLIFY_UUID` do ambiente; o uuid do disparo vira variável local;
  - `scripts/health-ready.sh <url>`: até `${HEALTH_TENTATIVAS:-18}` tentativas, com `${HEALTH_INTERVALO:-10}` s
    entre elas, de `curl -s -o <tmp> --max-time 10 -A 'Mozilla/5.0 (compatible; RunasDeploy/1.0; +github-actions)'
    -w '%{http_code}' <url>`. Com 200, sai 0. Se nenhuma der 200, imprime a lista `down` do corpo (como o
    `uptime.yml`) e `::error::`, e sai 1;
  - os jobs `test`, `publish` e `deploy`; os steps do `deploy` têm `id: promote`, `id: coolify` e `id: health`.

- [ ] **Step 1: Worktree** `.claude/worktrees/ci-pipeline-merge` (branch `ci/pipeline-merge`), já com a Task 2.
- [ ] **Step 2: Escrever os testes:**
  - `test_ci_nao_dispara_em_push`: `"push" not in _on(ci)`.
  - `test_deploy_encadeia_test_publish_deploy`: os jobs == `{test, publish, deploy}`; `deploy.needs ⊇ {test,
    publish}`; `test.uses == "./.github/workflows/ci.yml"`; `test.with == {"full": True, "build_images": False}`.
  - `test_test_concede_o_que_o_ci_pede`: `test.permissions` contém `contents: read`, `pull-requests: read` e
    `packages: read`.
  - `test_concurrency_no_workflow_inteiro`: no topo, `group == "deploy-production"` e `cancel-in-progress is False`;
    nenhum job tem `concurrency`.
  - `test_rollback_manual_pula_test_e_publish_mas_nao_o_deploy`: o `if` de `test` e de `publish` contém
    `inputs.tag`; o de `deploy` contém `!failure()` e `!cancelled()`.
  - `test_latest_so_e_promovido_no_job_deploy`: `":latest" not in _runs(publish)`, e o `deploy` chama
    `scripts/promote-latest.sh`.
  - `test_smoke_roda_antes_do_push_no_publish`: o índice do step com `ci-smoke-auth.sh` < o do step com
    `compose $FILES push`.
  - `test_deploy_mantem_paths_ignore`: a lista das Restrições globais.
  - `test_health_vem_depois_da_coolify`: o índice do step com `coolify-deploy.sh` < o do step com
    `health-ready.sh`.
  - `test_health_usa_user_agent_de_navegador`: `"Mozilla/5.0"` aparece em `scripts/health-ready.sh`.
  - `test_health_ready_aceita_200`: sobe `http.server` numa porta livre (thread) e roda o script com
    `HEALTH_TENTATIVAS=1`. Esperado: exit 0.
  - `test_health_ready_falha_sem_200`: roda contra `http://127.0.0.1:9/` com `HEALTH_TENTATIVAS=1` e
    `HEALTH_INTERVALO=0`. Esperado: exit ≠ 0.
  - `test_nenhum_segredo_dentro_de_run`: para `ci.yml` e `deploy.yml`, nenhum `run` contém `${{ secrets.`.
  - `test_todo_job_do_deploy_tem_timeout`: `publish` 30 e `deploy` 25 (o `test` tem `uses` e fica de fora).
  - `test_actions_de_terceiro_pinadas_deploy`: a mesma regra da Task 2.
- [ ] **Step 3: Rodar.** Esperado: FALHA nos testes novos.
- [ ] **Step 4: Escrever os três scripts e o `deploy.yml`:**
  - topo com `permissions: {contents: read}`, o `concurrency` de hoje, `env.FILES` e o `on` de hoje (o `tag` do
    dispatch fica);
  - `test`: `if: ${{ !inputs.tag }}`;
  - `publish`: `if: ${{ !inputs.tag }}`, `packages: write`, `TAG=${{ github.sha }}`. Steps: checkout; `.env` via
    `env: PROD_ENV` + `printf '%s\n' "$PROD_ENV" > .env`; login pinado; build com `--build-arg
    BUILDKIT_INLINE_CACHE=1`; smoke `.env api-gateway-prod vendas-prod`; `docker compose $FILES push`;
  - `deploy`: `needs: [test, publish]`, `if: ${{ !failure() && !cancelled() }}`, `packages: write`, `TAG=${{
    inputs.tag || github.sha }}`. Steps: checkout; `.env` (de novo, para o `config --images`); login; `promote`;
    `coolify` (segredos por `env:`); `health` com `https://app.runaserp.com.br/api/health/ready`.

  No `ci.yml`, sai o `push` com o `paths-ignore` dele, e o comentário passa a dizer que o merge é coberto pelo
  `deploy.yml`.
- [ ] **Step 5: Verificar.** Teste, `bash -n` nos três scripts, parse dos YAML e a suíte `tests/unit`.
- [ ] **Step 6: Commit** (só com pedido): `ci(deploy): gate the deploy on the full CI and check health after Coolify`.
  **Atenção:** este PR traz `tests/**`, que não está no `paths-ignore`. A promoção dele para main roda o pipeline
  novo de verdade, com ~80 s de queda. Combine o horário com o usuário (card 82, prova 7).

---

### Task 4 (card 103): rollback automático

**Arquivos:**
- Criar: `scripts/rollback-decide.sh`
- Modificar: `.github/workflows/deploy.yml` (job `deploy` e o dispatch), `tests/unit/test_pipeline_ci_deploy.py`

**Interfaces:**
- Consome: `promote-latest.sh`, `coolify-deploy.sh` e `health-ready.sh` (Task 3).
- Produz: `scripts/rollback-decide.sh <live>`. Lê no stdin a lista de arquivos de `git diff --name-only <live> <sha>`
  e imprime uma palavra:
  - `sem-producao`, se `<live>` vazio;
  - `migration`, se alguma linha casar `*/alembic/versions/*`;
  - `reverter`, nos demais casos.

- [ ] **Step 1: Worktree** `.claude/worktrees/ci-rollback-auto` (branch `ci/rollback-automatico`), já com a Task 3.
- [ ] **Step 2: Escrever os testes:**
  - `test_decide_sem_producao`: `""` com stdin vazio → `sem-producao`.
  - `test_decide_migration`: `services/vendas/alembic/versions/0007_x.py` → `migration`; idem para
    `api-gateway/alembic/versions/a.py`.
  - `test_decide_reverter`: `services/vendas/main.py\nservices/vendas/alembic.ini` → `reverter`.
  - `test_ensaio_rollback_e_boolean_de_dispatch`: `_on(deploy)["workflow_dispatch"]["inputs"]["ensaio_rollback"]
    ["type"] == "boolean"`.
  - `test_deploy_busca_o_historico`: o checkout do `deploy` tem `fetch-depth: 0`.
  - `test_contents_write_so_no_deploy`: o topo tem `contents: read`; só o job `deploy` tem `contents: write`.
  - `test_health_continua_para_o_rollback_decidir`: o step `health` tem `continue-on-error: true`.
  - `test_producao_so_move_depois_do_health`: o step que contém `refs/tags/producao` vem depois do `health` e tem
    `if` com `steps.health.outcome == 'success'`.
  - `test_rollback_so_roda_quando_o_health_falha`: o step de rollback tem `if` com `steps.health.outcome ==
    'failure'`, e o `run` dele contém `git diff --name-only` e `rollback-decide.sh`.
- [ ] **Step 3: Rodar.** Esperado: FALHA nos testes novos.
- [ ] **Step 4: Implementar:**
  - **Script:** `scripts/rollback-decide.sh`.
  - **Dispatch:** entra o input `ensaio_rollback` (boolean, padrão `false`).
  - **Job `deploy`:** ganha `contents: write` e checkout com `fetch-depth: 0`.
  - **Step `id: live`, antes do `promote`:** grava `sha=$(git rev-parse -q --verify refs/tags/producao^{commit} ||
    true)` em `$GITHUB_OUTPUT`. Os steps seguintes leem `LIVE: ${{ steps.live.outputs.sha }}` por `env:`.
  - **Step `health`:** `continue-on-error: true`. Se `ensaio_rollback` for verdadeiro, a URL ganha o sufixo
    `-ensaio-inexistente`.
  - **Step "Mark production"** (`if` com `steps.health.outcome == 'success'`): `git push -f origin
    "$TAG:refs/tags/producao"`.
  - **Step "Automatic rollback"** (`if` com `steps.health.outcome == 'failure'`):
    - calcula `decisao` pelo `git diff --name-only "$LIVE" "$TAG" | bash scripts/rollback-decide.sh "$LIVE"`, ou
      com stdin vazio quando `LIVE` estiver vazio;
    - `sem-producao` → `::error::` "no producao tag: automatic rollback disabled";
    - `migration` → `::error::` "a migration landed between $LIVE and $TAG: decide the rollback by hand";
    - `reverter` → `promote-latest.sh "$LIVE"`, depois `coolify-deploy.sh`, depois `health-ready.sh` na URL real.
      Com sucesso, `::error::` "deploy reverted to $LIVE"; sem sucesso, `::error::` "rollback failed too:
      production is down".
    - Termina sempre com `exit 1`.
- [ ] **Step 5: Verificar.** Teste, `bash -n` no script novo, parse do YAML e a suíte `tests/unit`.
- [ ] **Step 6: Commit** (só com pedido): `ci(deploy): roll back automatically when health fails and no migration landed`.
  Não há passo manual: o primeiro deploy verde depois deste PR cria a tag `producao`. Esse deploy fica sem rollback
  automático; se falhar, o job avisa com `sem-producao`.

---

### Task 5 (card 81): documentação

**Arquivos:** `.github/workflows/README.md`, `docs/06-operacao/deploy.md`, `tests/README.md`,
`.claude/rules/testes-backend.md` e `CLAUDE.md`.

- [ ] **Step 1:** liste as referências com `git grep -nE "(ci|deploy)\.yml:[0-9]" -- '*.md'` e re-meça cada uma no
  arquivo novo com `git grep -n`. Não chute números.
- [ ] **Step 2:** escreva o fluxo novo:
  - CI só em PR para `Developer`, escopada;
  - `checks`/`services`/`build`/`frontend`/`replay`;
  - `test ∥ publish → deploy`, a promoção do `:latest` e o health;
  - a tag `producao`, o rollback automático e o caso da migration;
  - o rollback manual por `tag` e o ensaio por `ensaio_rollback`.

  Tire toda frase dizendo que a CI dispara em push.
- [ ] **Step 3:** em `.claude/rules/testes-backend.md`, a "matriz de 8" vira o `scripts/ci-services.sh`, com o
  comando local equivalente. No `CLAUDE.md`, na seção de infraestrutura, o `publish` empurra `:<sha>`, o `deploy`
  promove `:latest`, e o rollback é a tag `producao` ou o dispatch. Mantenha a contagem de linhas; faça `git fetch`
  antes, porque outros chats editam o arquivo.
- [ ] **Step 4: Verificar.** `git grep -nE "(ci|deploy)\.yml:[0-9]" -- '*.md'` sem referência quebrada e nenhuma
  frase de "CI em push". Commit (só com pedido): `docs(ci): describe the scoped CI, gated deploy and automatic
  rollback`.

---

### Task 6 (card 82): prova em produção (Ação manual)

Siga o roteiro do spec §9, em ordem, e comente no card o link do run de cada item. Comandos:
- runs: `gh run list --workflow ci.yml -L 5` e `gh run view <id> --json jobs --jq '.jobs[] | [.name, .conclusion]'`;
- tag criada no primeiro deploy verde depois do 103 (prova 8): `git ls-remote origin refs/tags/producao` aponta
  para o sha daquele deploy.

Combine com o usuário as provas 7 e 10, que derrubam o stack por ~80 s e ~160 s. Se uma delas falhar, não repita às
cegas: leia o log impresso pelo job e abra um card. A prova 11 é o billing do mês seguinte.
