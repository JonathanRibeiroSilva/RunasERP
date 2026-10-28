> **Substituído em 2026-10-26** por `docs/superpowers/specs/2026-10-26-esteira-ci-cd-design.md`. Mantido só como histórico.

# Redesenho de CI e Deploy — Plano de implementação

> **Para quem executa:** SUB-SKILL OBRIGATÓRIA: `superpowers:executing-plans` (execução nativa; a regra do usuário só permite subagentes quando ele pedir). Os passos usam checkbox (`- [ ]`).

**Objetivo:** CI escopada no PR, pipeline único no merge (`test` ∥ `publish` → `deploy`), `:latest` só promovido depois de tudo verde, imagens construídas uma vez.

**Arquitetura:** `ci.yml` vira reutilizável (`workflow_call`) com um job `changes` que filtra por path; `deploy.yml` chama a CI completa, constrói e empurra só `:<sha>`, e o job `deploy` promove `:<sha>` → `:latest` no registry antes de acionar a Coolify. Um teste estrutural em `tests/unit` trava o desenho.

**Tecnologias:** GitHub Actions, `dorny/paths-filter`, `docker buildx imagetools`, pytest + PyYAML (padrão de `tests/unit/test_backup_antes_da_migration.py`).

**Spec:** `docs/superpowers/specs/2026-10-23-ci-deploy-redesign-design.md`

## Restrições globais

- **Nada de commit, merge ou push** sem pedido explícito do usuário. Onde o passo diria "commit", sugerir a mensagem (Conventional Commits, em inglês, tipo `ci`) e parar.
- Worktree **só** em `.claude/worktrees/` dentro do RunasERP; nunca pasta irmã em `E:\GitHub\ERP`.
- A branch atual (`feat/reconhecer-produto-tm`) tem mudanças não commitadas do card 60: **não tocar nela**.
- Não rodar workflow nem Docker local; dizer ao fim o que **não** foi executado.
- Os passos de `Trigger Coolify deploy` e `Wait for Coolify to finish the deploy` são copiados **sem alteração** do `deploy.yml` atual (incluem `-A Mozilla…`, retry, tolerância a 530).
- `paths-ignore` do `deploy.yml` (`landing-page/**`, `docs/**`, `**.md`, `.github/**`, `scripts/**`) **não muda**.
- No `run:` do job `publish` a string `:latest` não pode aparecer (nem em comentário): o teste trava isso.
- Actions pinadas como o repo faz (tag de major: `checkout@v7`, `setup-python@v7`); confirmar o major atual do `dorny/paths-filter` com `gh api repos/dorny/paths-filter/releases/latest --jq .tag_name` antes de escrever.
- Docs em pt-BR; comentários de YAML explicam o porquê, no estilo dos arquivos atuais.

## Foco de revisão

1. Serviço novo em `services/` sem entrada no filtro → nunca testado em PR (Task 1, `test_todo_servico_e_toda_imagem_tem_filtro`).
2. Rollback pula `test`/`publish` e, sem `!failure()`, o `deploy` também é pulado em silêncio (Task 1, `test_rollback_pula_test_e_publish_mas_nao_o_deploy`).
3. `:latest` promovido antes dos testes (Task 1, `test_latest_so_e_promovido_no_job_deploy`).
4. PR que só mexe em `ci.yml` roda só o que o filtro não cobre (Task 1, `test_filtros_incluem_o_proprio_ci_e_os_compartilhados`).
5. `migration-replay` pulado no merge por `event_name` (Task 1, `test_migration_replay_continua_fora_do_pr`).

---

### Task 0: Worktree e linha de base

**Arquivos:** nenhum código.

- [ ] **Step 1:** `git fetch origin Developer` e criar o worktree: `git worktree add .claude/worktrees/ci-deploy-redesign -b ci/pipeline-redesenho origin/Developer`.
- [ ] **Step 2:** copiar `docs/superpowers/specs/2026-10-23-ci-deploy-redesign-design.md` e este plano para o mesmo caminho dentro do worktree (estão só como não rastreados no checkout principal). A partir daqui, todo comando roda dentro do worktree.
- [ ] **Step 3:** `python -m pip install -r tests/requirements.txt` e `python -m pytest -c tests/pytest.ini tests/unit -q`. Esperado: tudo passa. Anotar a contagem para comparar no fim.

---

### Task 1: Teste estrutural do pipeline (falha primeiro)

**Arquivos:**
- Criar: `tests/unit/test_pipeline_ci_deploy.py`

**Interfaces:**
- Produz: o contrato que as Tasks 2–4 precisam satisfazer. Nomes que o teste espera: jobs de `ci.yml` = `changes`, `compose`, `build`, `frontend`, `backend`, `services`, `migration-replay`; jobs de `deploy.yml` = `test`, `publish`, `deploy`; outputs de `changes` = `services`, `images`, `frontend`; entradas de `workflow_call` = `full`, `build_images` (boolean); script `scripts/ci-smoke-auth.sh`; chaves de filtro `svc-<nome>` (`api-gateway` + cada pasta de `services/`), `img-<nome>` (cada chave de `docker-compose.build.yml` sem o sufixo `-prod`) e `frontend`.

- [ ] **Step 1: Escrever o teste.** Helpers: `_wf(nome)` (`yaml.safe_load` de `.github/workflows/<nome>`), `_on(wf)` (`wf.get("on", wf.get(True))`, porque o YAML 1.1 lê `on:` como `True`), `_runs(job)` (junta os `run` dos steps), `_filtros()` (carrega `with.filters` do step `dorny/paths-filter` do job `changes` e achata listas aninhadas das âncoras). Testes e asserts:
  - `test_ci_nao_dispara_em_push`: `_on(ci)` tem `pull_request`, `workflow_dispatch`, `workflow_call` e **não** tem `push`; `workflow_call.inputs.full.type == "boolean"` e `build_images.type == "boolean"`.
  - `test_deploy_encadeia_test_publish_deploy`: chaves de jobs = `{test, publish, deploy}`; `deploy.needs` contém `test` e `publish`; `test.uses == "./.github/workflows/ci.yml"`, `test.with.full is True`, `test.with.build_images is False`.
  - `test_concurrency_no_workflow_inteiro`: `deploy.yml` tem `concurrency.group == "deploy-production"` e `cancel-in-progress is False` no topo, e nenhum job tem `concurrency`.
  - `test_rollback_pula_test_e_publish_mas_nao_o_deploy`: `test.if` e `publish.if` contêm `inputs.tag == ''`; `deploy.if` contém `!failure()` e `!cancelled()`.
  - `test_latest_so_e_promovido_no_job_deploy`: `":latest" not in _runs(publish)`; `_runs(deploy)` contém `imagetools create` e `:latest`.
  - `test_smoke_roda_antes_do_push_no_publish`: no `publish`, o índice do step cujo `run` chama `scripts/ci-smoke-auth.sh` é menor que o do step cujo `run` contém `compose $FILES push`; e o script existe no repo.
  - `test_ci_build_usa_o_mesmo_script_de_smoke`: `_runs(ci.jobs.build)` contém `scripts/ci-smoke-auth.sh`.
  - `test_jobs_do_ci_dependem_do_changes`: `services`, `build`, `frontend` têm `changes` em `needs`; `backend` e `compose` **não** têm `if`.
  - `test_todo_servico_e_toda_imagem_tem_filtro`: o conjunto de chaves `svc-*` == `{"svc-api-gateway"} ∪ {svc-<pasta> para pasta em services/}`; o conjunto `img-*` == `{img-<k sem "-prod"> para k em docker-compose.build.yml.services}`; existe a chave `frontend`.
  - `test_filtros_incluem_o_proprio_ci_e_os_compartilhados`: todo `svc-*` contém `postgres/**`, `tests/requirements.txt`, `.github/workflows/ci.yml` e o glob da própria pasta; todo `img-*` contém `docker-compose.prod.yml`, `docker-compose.build.yml`, `.env.production.example`, `.github/workflows/ci.yml` e o glob da própria pasta.
  - `test_migration_replay_continua_fora_do_pr`: `ci.jobs["migration-replay"].if == "github.event_name != 'pull_request'"`.
  - `test_deploy_mantem_paths_ignore`: `_on(deploy).push["paths-ignore"]` == as 5 entradas atuais.
- [ ] **Step 2:** `python -m pytest -c tests/pytest.ini tests/unit/test_pipeline_ci_deploy.py -q`. Esperado: **FALHA** em todos (workflows ainda no formato antigo). Se algum passar sem mudança, o teste não está medindo o que diz.

---

### Task 2: Script de smoke compartilhado

**Arquivos:**
- Criar: `scripts/ci-smoke-auth.sh`
- Modificar: `.github/workflows/ci.yml` (job `build`, só para chamar o script; o resto do arquivo muda na Task 3)

**Interfaces:**
- Produz: `scripts/ci-smoke-auth.sh <env-file> <servico-prod>...` — para cada serviço informado resolve a imagem por `docker compose --env-file <env-file> -f docker-compose.prod.yml -f docker-compose.build.yml config --format json` e roda o `passlib`/`bcrypt` de `ci.yml:62` dentro dela com `docker run --rm --entrypoint python`. Sai ≠ 0 se qualquer imagem falhar. Consumido pelas Tasks 3 e 4.

- [ ] **Step 1:** mover o corpo do step "Smoke-test auth primitives" (`ci.yml:58-75`, incluindo os comentários sobre `docker run` vs `compose run` e o porquê do smoke) para o script, trocando a lista fixa `api-gateway-prod vendas-prod` pelos argumentos e o `--env-file` fixo pelo primeiro argumento. `set -euo pipefail`.
- [ ] **Step 2:** `bash -n scripts/ci-smoke-auth.sh` (sintaxe). Se `shellcheck` existir, rodar também. Esperado: sem erro. **Não executar o script** (precisa de Docker e imagens construídas).
- [ ] **Step 3:** sugerir mensagem de commit: `ci(smoke): extract auth smoke test into a shared script`. Não commitar.

---

### Task 3: `ci.yml` escopado e reutilizável

**Arquivos:**
- Modificar: `.github/workflows/ci.yml`

**Interfaces:**
- Consome: `scripts/ci-smoke-auth.sh` (Task 2).
- Produz: `workflow_call` com `inputs.full` e `inputs.build_images` (boolean, `required: false`, `default: false` e `true`, respectivamente); outputs do job `changes`: `services` (JSON `["api-gateway","services/estoque",…]` para a matriz), `images` (string separada por espaço, ex. `estoque-prod frontend-prod`, sem JSON), `frontend` (`'true'|'false'`).

- [ ] **Step 1: Gatilhos.** `on:` fica com `pull_request` (branches `main`, `Developer`), `workflow_dispatch: {}` e `workflow_call` com as duas entradas. Remover `push` e o `paths-ignore` (o comentário sobre `c26e51e` passa a explicar que o merge é coberto pelo `deploy.yml`).
- [ ] **Step 2: Job `changes`** (`runs-on: ubuntu-latest`, `permissions: {contents: read, pull-requests: read}`, **sem secrets**). Duas etapas:
  - `dorny/paths-filter` (`id: filter`) com `filters` em YAML usando âncoras: `shared_services: &shared_services` = `postgres/**`, `tests/requirements.txt`, `.github/workflows/ci.yml`; `shared_images: &shared_images` = `docker-compose.prod.yml`, `docker-compose.build.yml`, `.env.production.example`, `.github/workflows/ci.yml`; depois `svc-api-gateway: [api-gateway/**, *shared_services]`, um `svc-<n>` por pasta de `services/` (`services/<n>/**`), um `img-<n>` por imagem (`img-api-gateway` → `api-gateway/**`, `img-<serviço>` → `services/<serviço>/**`, `img-frontend` → `frontend/**`, cada um com `*shared_images`) e `frontend: [frontend/**, .github/workflows/ci.yml]`.
  - Passo `run` com `jq` que lê `${{ steps.filter.outputs.changes }}` (array JSON dos filtros que casaram) e escreve os três outputs. Regras: se `inputs.full == true` **ou** `github.event_name == 'workflow_dispatch'`, todos os serviços/imagens/frontend entram; senão, `svc-X` vira `X` para o gateway e `services/X` para os demais; `img-X` vira `X-prod`; `frontend` vale `'true'` se a chave `frontend` casou. Passar o JSON por `env:` e não por `${{ }}` dentro do `run:` (injeção, mesmo cuidado do `ROLLBACK_TAG`).
- [ ] **Step 3: Jobs.**
  - `compose` (novo, sempre): só os dois `docker compose config` (hoje no topo do job `build`, `ci.yml:35-38`).
  - `build`: `needs: changes`; `if: inputs.build_images != false && needs.changes.outputs.images != ''` (em PR `inputs.build_images` é vazio → roda); constrói **só** `needs.changes.outputs.images` (`docker compose … build <imagens>`), depois chama `scripts/ci-smoke-auth.sh .env.production.example` com a interseção de `{api-gateway-prod, vendas-prod}` com as imagens construídas (se vazia, pula o smoke).
  - `frontend`: `needs: changes`; `if: needs.changes.outputs.frontend == 'true'`; corpo inalterado.
  - `backend`: inalterado, sem `if`.
  - `services`: `needs: changes`; `if: needs.changes.outputs.services != '[]'`; `matrix.svc: ${{ fromJSON(needs.changes.outputs.services) }}`; `fail-fast: false` e corpo inalterados.
  - `migration-replay`: `if: github.event_name != 'pull_request'` **inalterado**; reescrever só o comentário para registrar que em `workflow_call` o `event_name` é o do chamador, por isso roda no merge.
- [ ] **Step 4:** `python -m pytest -c tests/pytest.ini tests/unit/test_pipeline_ci_deploy.py -q`. Esperado: os testes de `ci.yml` passam; os de `deploy.yml` ainda falham. Conferir também `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`.
- [ ] **Step 5:** sugerir mensagem de commit: `ci: scope PR checks to changed paths and make ci.yml reusable`. Não commitar.

---

### Task 4: `deploy.yml` em três jobs com promoção de `:latest`

**Arquivos:**
- Modificar: `.github/workflows/deploy.yml`

**Interfaces:**
- Consome: `ci.yml` via `workflow_call` com `full: true` e `build_images: false`; `scripts/ci-smoke-auth.sh`.
- Produz: jobs `test`, `publish`, `deploy`.

- [ ] **Step 1: Topo.** Manter `on` (push em `main` com o `paths-ignore` atual, e `workflow_dispatch` com `tag`). Mover `concurrency: {group: deploy-production, cancel-in-progress: false}` e uma linha de comentário sobre a corrida entre deploys para o **topo do workflow** (já está no topo; conferir que nenhum job repete). Adicionar `permissions: {contents: read}` no topo. Manter `env.FILES`.
- [ ] **Step 2: `test`.** `uses: ./.github/workflows/ci.yml`; `with: {full: true, build_images: false}`; `if: inputs.tag == ''`; `permissions: {contents: read, pull-requests: read}`.
- [ ] **Step 3: `publish`.** `if: inputs.tag == ''`; `permissions: {contents: read, packages: write}`; `env.TAG: ${{ github.sha }}` no nível do job. Steps: checkout; "Write build env" (igual ao atual); login no ghcr (igual); `docker compose $FILES build --build-arg BUILDKIT_INLINE_CACHE=1` (manter o comentário `ponytail:` sobre `cache_from`); `scripts/ci-smoke-auth.sh .env api-gateway-prod vendas-prod`; `docker compose $FILES push` (empurra só `:<sha>`). Sem nenhum `:latest` no `run`.
- [ ] **Step 4: `deploy`.** `needs: [test, publish]`; `if: ${{ !failure() && !cancelled() }}`; `permissions: {contents: read, packages: write}`; `env.TAG: ${{ inputs.tag || github.sha }}`. Steps: checkout; "Write build env" (de novo, para o `compose config --images` parsear); login; "Promote to :latest" com `ROLLBACK_TAG` lido por `env:` e `docker compose $FILES config --images | grep '^ghcr\.io/' | while read -r img; do docker buildx imagetools create -t "${img%:*}:latest" "$img"; done` (só manifesto, sem pull); depois os steps "Trigger Coolify deploy" e "Wait for Coolify to finish the deploy" copiados **sem alteração**.
- [ ] **Step 5:** reescrever os comentários que descreviam o fluxo antigo (cabeçalho e o bloco de "Publish images") para o novo: `:latest` só avança no `deploy`; rollback = mesmo passo de promoção com o sha informado.
- [ ] **Step 6:** `python -m pytest -c tests/pytest.ini tests/unit/test_pipeline_ci_deploy.py -q`. Esperado: **todos passam**. Depois a suíte inteira: `python -m pytest -c tests/pytest.ini tests/unit -q`, comparando com a contagem da Task 0.
- [ ] **Step 7:** sugerir mensagem de commit: `ci(deploy): gate the deploy on tests and promote :latest only after they pass`. Não commitar.

---

### Task 5: Documentação e referências `arquivo:linha`

**Arquivos:**
- Modificar: `.github/workflows/README.md`, `docs/06-operacao/deploy.md`, `tests/README.md`, `CLAUDE.md`, `docs/superpowers/specs/2026-10-23-ci-deploy-redesign-design.md` (uma linha em 4.2 registrando a entrada `build_images`).

- [ ] **Step 1:** `git grep -nE "(ci|deploy)\.yml:[0-9]" -- '*.md'` lista toda referência a linha dos workflows (sabidos: `CLAUDE.md` cita `ci.yml:167` e `graphify-update.yml:10-18`; `deploy.md` e `workflows/README.md` citam dezenas). Para cada uma, **re-medir no arquivo novo** com `git grep -n` e reescrever; não chutar números.
- [ ] **Step 2:** `workflows/README.md` e `deploy.md` §2: descrever o novo fluxo (CI escopada no PR; `test ∥ publish → deploy` no merge; promoção do `:latest`; `concurrency` no workflow; rollback pulando `test`/`publish`) e remover a afirmação de que a CI dispara em push em `main`/`Developer`. `tests/README.md` (linhas 21, 67 e 117): CI agora tem `changes`, `compose`, `build`, `frontend`, `backend`, `services`, `migration-replay`. Atualizar "Última atualização".
- [ ] **Step 3:** `CLAUDE.md` (seção Infrastructure): "CI publishes every image twice… rollback is `TAG=<sha>`" passa a dizer que o `publish` empurra `:<sha>` e o `deploy` promove `:latest`.
- [ ] **Step 4:** sugerir mensagem de commit: `docs(ci): describe the scoped CI and the gated deploy pipeline`. Não commitar.

---

### Task 6: Verificação final e entrega

- [ ] **Step 1:** `python -m pytest -c tests/pytest.ini tests/unit -q` (tudo verde) e parse YAML dos 5 workflows. Se `actionlint` estiver instalado, rodar `actionlint`; senão registrar "actionlint não rodou".
- [ ] **Step 2:** `git status --short` no worktree: só `.github/workflows/{ci,deploy}.yml`, `.github/workflows/README.md`, `scripts/ci-smoke-auth.sh`, `tests/unit/test_pipeline_ci_deploy.py`, os `.md` da Task 5 e `docs/superpowers/**`.
- [ ] **Step 3:** entregar ao usuário: (a) lista do que **não foi executado** — nenhum workflow rodou, o script de smoke não foi executado, Docker/`docker compose config` não rodou (sem Docker local); (b) o roteiro de prova da seção 6 do spec, na ordem; (c) lembrete de que o merge deste PR **não** dispara deploy (`.github/**` e `scripts/**` estão no `paths-ignore`), então a primeira prova real é o `workflow_dispatch` com `tag` vazio, com ~80s de queda; (d) rascunho do corpo do PR, commit a commit, com a mensagem de atribuição do Claude Code no fim; (e) os cards a registrar no Trello: `VITE_*` não chegam ao bundle e teste de integração entre serviços.
