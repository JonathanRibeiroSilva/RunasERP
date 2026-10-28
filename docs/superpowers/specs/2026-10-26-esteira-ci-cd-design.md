# Esteira de CI/CD: spec revisado

Data: 2026-10-26. Status: aguardando revisão do usuário. Sem commit (regra do usuário).
Substitui `2026-10-23-ci-deploy-redesign-design.md` e o plano de mesma data.
Base: a auditoria de 26/10 em `docs/superpowers/audits/2026-10-26-ci-cd/achados.md` (não versionado; os JSON
estão na mesma pasta). Os números abaixo vêm de lá: não refaça a medição.

## 1. Problema

O repo volta a ser privado no plano Free, que tem 2.000 min de Actions por mês e bloqueia ao esgotar. Outubro
estourou: 2.240 min até o dia 26. O GitHub **arredonda cada job para cima ao minuto**, e esse modelo explica 95% do
billing real (3.004 min estimados contra 3.162 reais em 36 dias). A alavanca, portanto, é **jobs × runs**, não a
velocidade de cada job: um leg de 0,8 min custa 1 min, e o teste em si leva ~3 s.

Para onde vão ~2.631 min por 30 dias:

| Origem | min/30d |
|---|---:|
| CI no push em Developer (o PR já testou o mesmo código) | 615 |
| CI de PR de feature | 603 |
| Promoção: CI no PR (277) + CI no push em main (293) | 570 |
| Dependabot (mira main; cada bump vira deploy) | ~400 |
| Uptime (cron) | 211 |
| Deploy | ~115 |

Defeitos confirmados pelo verificador da auditoria:
- **C3:** deploy subiu com CI vermelha (sha 90d26cb, 19/09). O `deploy.yml` não espera a CI.
- **C1:** o build da CI dá 401 no cache do ghcr (não há login), então nada vem do cache.
- **C6:** nenhum job tem `timeout-minutes`; um job travado consome 360 min.
- **C5:** o PR não tem `concurrency`; run obsoleto continua faturando.
- **C4:** o deploy só confere o status da Coolify, nunca o `/api/health/ready`.
- **C8:** `${{ secrets.* }}` é expandido dentro dos scripts.

Além disso, o `:latest` é empurrado antes de qualquer teste, e a Coolify e o cache leem `:latest`.

## 2. Objetivo e critério de sucesso

- Deploy só sobe o que passou em teste, e `:latest` só avança depois de tudo verde.
- A esteira cabe na cota com folga. A estimativa é de ~725 min/30d, contando os cards 88 (Dependabot) e 89
  (uptime), que ficam fora deste spec. **É estimativa sobre o custo medido por run; a prova é o billing do mês
  seguinte, com o repo privado.**
- Produção nunca fica pior que hoje durante a transição: cada PR da entrega pode ser mergeado sozinho.

## 3. Decisões do usuário (26/10)

1. Spec só da esteira (`ci.yml`, `deploy.yml`, scripts e o teste deles). Dependabot, uptime e testes viraram cards
   próprios (88–101).
2. **PR para `main` não roda CI automática** (promoção, Dependabot de segurança, PR direto). O pipeline do merge é o
   portão. Quem quiser pré-checar dispara a CI completa por `workflow_dispatch` na Developer.
3. **Poucos jobs:** os legs rodam em sequência num job só, por script, em vez da matriz de 8 jobs.
4. O `migration-replay` também roda no PR que mexe em migration.
5. **Rollback automático** quando o health check falha, exceto quando o salto cruza uma migration.

## 4. Fora de escopo

- Dependabot (card 88), uptime (card 89), testes de regressão e lacunas (cards 87, 90–101) e contrato entre
  serviços (card 83, Decisão).
- `graphify-update.yml` e `landing.yml` (card 105), retenção do ghcr (card 104) e Dockerfiles como root com gcc
  (card 106).
- Reduzir os ~80 s de queda da Coolify por deploy.
- Branch protection e Environments: só valem enquanto o repo for público.
- `ARG VITE_*` no `frontend/Dockerfile` (fora de escopo desde 23/10).

## 5. Desenho

### 5.1 CI do PR (`ci.yml`)

```
PR ─► Developer
checks  (sempre)  filtro por path + docker compose config (prod e dev) + tests/unit
  ├─► services   legs afetados, em sequência, 1 job       se a lista não for vazia
  ├─► build      imagens afetadas, cache do ghcr, smoke   se a lista não for vazia e build_images
  ├─► frontend   npm ci, lint, build, vitest              se o filtro marcar
  └─► replay     stack inteiro, 1 Postgres, do zero       fora de PR, ou PR com o filtro de migration
```

**Gatilhos:**
- `pull_request` com `branches: [Developer]`;
- `workflow_dispatch`, que roda tudo;
- `workflow_call`, com as entradas `full` (boolean, padrão false) e `build_images` (boolean, padrão true).

Sai o `push`.

**`concurrency`:** o grupo é `ci-pr-<número>` com `cancel-in-progress` no PR. Fora do PR, o grupo é o `run_id`
(único), para não interferir no `deploy-production` do chamador.

**`checks`:** roda o `dorny/paths-filter`, pinado por SHA e sem secrets, só em `pull_request`. Com `full` ou
`workflow_dispatch`, marca tudo. Saídas: `services` (lista de pastas), `images` (lista), `frontend` (bool) e
`migrations` (bool). No modo completo, a lista de serviços vem das pastas (`api-gateway` + `services/*`), para um
serviço novo entrar sem edição.

**Filtros:**

| Saída | Só o item | Tudo |
|---|---|---|
| `services` | `services/<x>/**` ou `api-gateway/**` | `postgres/**`, `tests/requirements.txt`, `.github/workflows/ci.yml`, `scripts/ci-services.sh` |
| `images` | a pasta da imagem (as 9 chaves de `docker-compose.build.yml`, sem `-prod`) | `docker-compose.prod.yml`, `docker-compose.build.yml`, `.env.production.example`, `.github/workflows/ci.yml`, `scripts/ci-smoke-auth.sh` |
| `frontend` | `frontend/**` | `.github/workflows/ci.yml` |
| `migrations` | `*/alembic/**`, `*/database.py`, `postgres/**`, `docker-compose.dev.yml`, `.github/workflows/ci.yml` | — |

**`build`:** faz login no ghcr com `packages: read`, o que conserta o 401 do cache. Constrói só as imagens
afetadas. Roda o `scripts/ci-smoke-auth.sh` quando `api-gateway-prod` ou `vendas-prod` estiver na lista.

**Timeouts (min):** `checks` 10, `services` 20, `frontend` 15, `build` 30, `replay` 20.

### 5.2 Merge em main (`deploy.yml`)

```
push em main (paths-ignore igual a hoje)  |  workflow_dispatch(tag, ensaio_rollback)
 ├─ test     uses ci.yml {full: true, build_images: false}     if: tag vazio
 ├─ publish  build 9 imagens com PROD_ENV + cache do :latest   if: tag vazio
 │           ci-smoke-auth.sh ANTES do push; push só do :<sha>
 └─ deploy   needs [test, publish]; if: !failure() && !cancelled()
             0. live = tag git `producao`
             1. promove :<sha> → :latest (docker buildx imagetools create, só manifesto)
             2. dispara a Coolify e espera (passos idênticos aos de hoje)
             3. health: até 18×10 s esperando 200 em https://app.runaserp.com.br/api/health/ready (-A Mozilla)
                ├─ 200 → git push -f origin <sha>:refs/tags/producao
                └─ falhou → rollback automático (abaixo)
```

- **`concurrency: deploy-production`** com `cancel-in-progress: false` no workflow inteiro, para os merges saírem
  em ordem. O `paths-ignore` fica igual: `landing-page/**`, `docs/**`, `**.md`, `.github/**`, `scripts/**`.
- **`<sha>`:** é `inputs.tag || github.sha`. O dispatch com `tag` faz o rollback manual: `test` e `publish` são
  pulados e o `deploy` roda o mesmo caminho.
- **Rollback automático:** se o health falhar, o job checa se `git diff --quiet "$live" "$sha" --
  '*/alembic/versions/*'` acusa diferença.
  - Se houver migration no meio, **não reverte**: o código antigo rodaria contra o schema novo. O job fica
    vermelho com a mensagem "migration aplicada; decida o rollback à mão".
  - Se não houver, promove `:<live>` → `:latest`, dispara a Coolify, espera e roda o health de novo. Com 200, o job
    fica vermelho com `deploy revertido para <live>`. Sem 200, fica vermelho com "rollback também falhou: produção
    fora".
  - Sem a tag `producao`, o rollback automático fica desligado e o job avisa. A tag não é criada à mão: o primeiro
    health verde a cria, com o mesmo `git push -f` que a move depois.
- **`ensaio_rollback`** (boolean de dispatch, para usar com `tag` = sha da `producao`): o primeiro health consulta um
  caminho inexistente, o que força o rollback sem quebrar nada.
- **Permissões:** o job `test` concede `contents: read`, `pull-requests: read` e `packages: read`. O GitHub valida
  as permissões dos jobs chamados pelo `workflow_call` ao abrir o run, inclusive as do `build`, que vai ser pulado. O `publish` tem `packages: write`. O `deploy` tem `packages: write` e `contents: write` (só para
  a tag), com checkout `fetch-depth: 0`. Push de tag feito com o `GITHUB_TOKEN` não dispara workflow.
- **Segredos:** todos passam por `env:` e são lidos como `"$X"`. O `.env` é escrito com `printf '%s\n'
  "$PROD_ENV" > .env`. O `deploy` reescreve o `.env` de build, porque `docker compose config --images` exige as
  entradas `${VAR:?}`.
- **Actions de terceiro:** pinadas por SHA (`docker/login-action`, `dorny/paths-filter`). As `actions/*` continuam
  por major.
- **Timeouts (min):** `publish` 30, `deploy` 25. Os jobs do `test` herdam os do `ci.yml`.

### 5.3 Scripts

- **`scripts/ci-services.sh <svc>...`:** Postgres e Redis vêm dos `services:` do job. Para cada serviço, em
  sequência:
  - cria o banco `erp_<svc>` e usa o Redis DB 8..15;
  - cria um venv próprio e instala `requirements.txt` + `tests/requirements.txt`, com cache de pip compartilhado;
  - roda `postgres/init-schemas.sql`, depois `alembic upgrade head`, depois `pytest tests -p no:cacheprovider`;
  - tudo dentro de `::group::`, num subshell com `set -e`.

  O script anota ok ou FALHOU, segue para o próximo, escreve uma tabela em `$GITHUB_STEP_SUMMARY` e sai com 1 se
  algum leg falhou. As variáveis de ambiente são as da matriz de hoje. Os 8 conftests e `alembic/env.py` leem
  `DATABASE_URL` do ambiente e usam schema próprio, então o isolamento é o de hoje.
- **`scripts/ci-smoke-auth.sh <env-file> <servico-prod>...`:** o smoke de passlib/bcrypt que hoje está no `ci.yml`,
  usado pelo `build` do PR e pelo `publish`.

### 5.4 Teste da esteira (`tests/unit/test_pipeline_ci_deploy.py`)

Segue o padrão de `tests/unit/test_backup_antes_da_migration.py` (`yaml.safe_load`; a chave `on:` do YAML 1.1 vira
`True`, então use `wf.get("on", wf.get(True))`). Roda local, sem Postgres. O teste falha se:

- **`ci.yml`:**
  - houver gatilho `push`, ou o PR mirar algo além de `Developer`;
  - uma pasta de serviço ou uma imagem do `docker-compose.build.yml` não tiver filtro;
  - o `ci.yml` ou um script sair dos conjuntos compartilhados;
  - o replay rodar em PR sem o filtro de migration;
  - o `build` não usar o `ci-smoke-auth.sh`;
  - o cancelamento valer fora do PR.
- **`deploy.yml`:**
  - o `test` não chamar o `ci.yml` com `full: true`;
  - o `deploy` não depender de `[test, publish]` com `!failure() && !cancelled()`;
  - o `concurrency` não estiver no workflow inteiro;
  - o `run` do `publish` contiver `:latest`, mesmo em comentário;
  - o smoke vier depois do push;
  - o `paths-ignore` mudar;
  - o health não vier depois da espera da Coolify;
  - a tag `producao` se mover antes do health;
  - o rollback não checar `alembic/versions`;
  - houver `contents: write` fora do `deploy`.
- **Os dois:** job sem `timeout-minutes`; `${{ secrets.` dentro de `run:`; action fora de `actions/*` sem SHA de
  40 hex.

## 6. Falhas

| Falha | Efeito | Ação |
|---|---|---|
| `test` ou `publish` vermelho | deploy não roda; produção intacta; `:<sha>` órfãs no ghcr | fix por Developer → main |
| Coolify falha depois da promoção | igual a hoje, com o log impresso | rollback automático, se não cruzar migration |
| Health falha sem migration no salto | reverte para a `producao`; job vermelho | investigar com a lista `down` impressa |
| Health falha com migration no salto | não reverte; job vermelho | decidir o rollback à mão |
| Rollback também falha | job vermelho "produção fora"; a sonda do card 89 avisa | intervenção manual |
| Falso positivo (Cloudflare ou túnel fora > 3 min) | deploy bom revertido | refazer por dispatch |
| Dois merges seguidos | em fila; o pendente mais novo vence | nada |

## 7. Custo estimado (min faturados)

| Situação | Jobs | Hoje | Novo |
|---|---|---:|---:|
| PR só de docs | `checks` | ~12,8 | ~1 |
| PR em um serviço | `checks` + `services` + `build` | ~12,8 | ~4 |
| PR com migration | o de cima + `replay` | ~12,8 | ~7 |
| PR do Dependabot de pip (mensal) | `checks` + `services`(8) + `build`(9) | ~13 | ~8 |
| Push em Developer | — | ~14,6 | 0 |
| PR para main | — | ~13 | 0 |
| Merge em main | `test` + `publish` + `deploy` | ~19,6 | ~15–16 |
| Rollback (só em falha) | Coolify + health de novo | — | +~4 |

Do merge até a produção no ar: ~9 min, contra ~4 hoje, porque hoje o deploy não espera a CI. Total de 30 dias,
somando os cards 88 e 89: ~725 min.

## 8. Entrega (cards, nesta ordem)

Cada PR pode ser mergeado sozinho sem deixar a esteira pior que hoje.

1. **79:** a matriz vira 1 job `services` chamando o `ci-services.sh`; o smoke vira `ci-smoke-auth.sh`. Mantém o
   push e todo o resto. Economiza ~7 min por run assim que entra.
2. **102:** `checks`, os filtros, o replay com filtro de migration, `concurrency`, `timeouts`, o login no ghcr e as
   entradas do `workflow_call`. Mantém o push.
3. **80:** o `deploy.yml` desta seção sem o rollback automático (health vermelho deixa o job vermelho), e o push sai
   do `ci.yml`. Depende do 102.
4. **103:** o rollback automático, a tag `producao` e o `ensaio_rollback`. Depende do 80.
5. **81:** os docs. **82:** a prova (Ação manual).

**Atenção:** `tests/**` não está no `paths-ignore`. O PR que traz o `test_pipeline_ci_deploy.py` dispara deploy
quando chega em main, e um push usa o workflow do próprio commit. **A promoção do card 80 para main é a primeira
execução real do pipeline novo**, com deploy e ~80 s de queda: faça de propósito, em horário calmo. Não há passo manual de
configuração: a tag `producao` nasce sozinha no primeiro deploy verde depois do card 103. Esse primeiro deploy fica
sem rollback automático; se falhar, o job só avisa. O mesmo vale para a promoção dos cards 79 e 102: elas deployam com o `deploy.yml` antigo, como
qualquer merge de código de hoje.

## 9. Prova (card 82)

Nada de workflow roda local, e não há Docker nem Postgres aqui. Local: `pytest -c tests/pytest.ini tests/unit`
verde (inclui o teste da esteira), `bash -n` nos dois scripts e parse dos YAML. No GitHub, em ordem:

1. PR do 79: o job `services` roda os 8 legs, e o total bate com o de hoje (223 testes nos legs).
2. PR do 102: mexe no `ci.yml`, então tudo roda uma vez, inclusive o replay.
3. PR só em `services/estoque`: só `checks` + `services`(estoque) + `build`(estoque).
4. PR só de docs: só `checks`.
5. Dois pushes seguidos num PR: o primeiro run é cancelado.
6. Merge na Developer e PR de promoção: nenhuma CI roda.
7. Promoção do 80 (horário calmo): `:latest` só muda depois de `test` e `publish` verdes; a Coolify sobe; o health
   dá 200.
8. Promoção do 103: o health verde cria a tag `producao`. Confira com `git ls-remote origin refs/tags/producao`.
9. Dispatch com `tag` = sha anterior: `test` e `publish` pulados, `deploy` não pulado.
10. Dispatch com `tag` = sha da `producao` e `ensaio_rollback` (horário calmo, ~160 s de queda): o rollback roda,
    o health volta a 200 e o job fica vermelho com "revertido".
11. Billing do mês seguinte, com o repo privado.

## 10. Docs a atualizar (card 81)

- `.github/workflows/README.md`
- `docs/06-operacao/deploy.md`: tag `producao`, rollback automático e manual, ensaio.
- `tests/README.md`
- `.claude/rules/testes-backend.md`: a matriz de 8 vira o script.
- `CLAUDE.md`: seção de infraestrutura.

Esses arquivos citam `arquivo:linha` de `ci.yml` e `deploy.yml`. Liste com
`git grep -nE "(ci|deploy)\.yml:[0-9]" -- '*.md'` e re-meça cada um no arquivo novo.

## 11. Riscos

- **Um `if`/`needs` errado pode pular o deploy em silêncio** (`workflow_call` com `full`). Mitigação: o teste da
  esteira e a prova 8.
- **Filtro incompleto deixa um serviço sem teste no PR.** Mitigação: o teste trava "toda pasta tem filtro", e o
  merge roda tudo de qualquer forma.
- **Rollback automático com falso positivo**, ou cruzando migration: o segundo caso é bloqueado pelo diff.
- **O `deploy` ganha `contents: write`** no mesmo job que tem os segredos de produção. Aceito: é só para a tag, e as
  actions de terceiro estão pinadas.
- **Mais espera:** ~5 min a mais por merge, e o job `services` em sequência leva ~4 min no run completo (a matriz
  levava ~0,8 em paralelo).
- **`concurrency` no topo do `ci.yml` chamado por `workflow_call`:** não conferi na doc como ele se comporta dentro
  do `deploy-production` do chamador. O grupo por `run_id` foi escolhido para não colidir, mas confira na doc ao
  implementar o card 102. Se houver dúvida, mova o `concurrency` para os jobs com `if` de PR. A prova 8 confirma.
- **`dorny/paths-filter` é terceiro.** Roda sem secrets e pinado por SHA, e o Dependabot mantém a versão.
- **Retenção futura do ghcr (card 104)** não pode apagar o `:<sha>` da `producao`, ou o rollback perde o alvo.
