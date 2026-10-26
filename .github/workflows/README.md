# GitHub Actions Workflows

Este diretório contém os workflows do RunasERP. São **5**, e cada arquivo carrega
nos próprios comentários o motivo de cada decisão (quais paths ignora, por que o
`-A` do curl existe, qual run de produção provou o quê). Este README é o índice;
o arquivo é a fonte da verdade.

| Workflow | Dispara em | Faz |
|---|---|---|
| `ci.yml` | PR e push em `main` e `Developer` | Portão de qualidade: 4 jobs |
| `deploy.yml` | push em `main` + execução manual | Publica as 9 imagens no ghcr e manda a Coolify subir |
| `landing.yml` | push em `main` tocando `landing-page/**` + manual | Publica a landing no Cloudflare Pages |
| `uptime.yml` | cron + manual | Sonda produção e alerta no Telegram |
| `graphify-update.yml` | push em `main` tocando código + manual | Regenera e commita o `graphify-out/` |

---

## `ci.yml` — CI

Dispara em `pull_request` para `main` e `Developer` e também em `push` nessas
duas branches. No push existe `paths-ignore` (`landing-page/**`, `docs/**`,
`**.md`); num PR o portão roda inteiro, independente do diff. O filtro é pela
BASE do PR: um PR aberto contra outra branch (empilhado) não dispara o CI, por
decisão. Abra sempre contra `Developer`.

Quatro jobs:

1. **`build`** — valida `docker-compose.prod.yml` e `docker-compose.dev.yml` com
   `docker compose config` (cada um com seu próprio `.env*.example`), constrói
   todas as imagens de produção e faz um smoke-test do hash de senha
   (`passlib` + `bcrypt`) dentro das imagens de `api-gateway-prod` e
   `vendas-prod` — os dois serviços que autenticam.
2. **`frontend`** — Node 22, `npm ci`, `npm run lint`, `npm run build`,
   `npm run test -- --run`, dentro de `frontend/`.
3. **`backend`** — Python 3.12, `pip install -r tests/requirements.txt` e
   `pytest -c tests/pytest.ini tests/unit`.
4. **`services`** — matriz de **8 legs** (`api-gateway` + os 7 serviços), uma
   por diretório, com Postgres 15 e Redis 7 como service containers. Cada leg
   instala o `requirements.txt` do próprio serviço, aplica
   `postgres/init-schemas.sql`, roda `alembic upgrade head` a partir de um banco
   vazio e depois `pytest tests`. `fail-fast: false`: um serviço quebrado não
   esconde o estado dos outros.

## `deploy.yml` — Deploy

`push` em `main` (com `paths-ignore` para `landing-page/**`, `docs/**`, `**.md`,
`.github/**` e `scripts/**`) e `workflow_dispatch`.

Este workflow **só produz imagens**. Quem faz o deploy de fato é a Coolify, que
é avisada por `POST {COOLIFY_URL}/api/v1/deploy?uuid={COOLIFY_UUID}` e depois
consultada em `/api/v1/deployments/{uuid}` até terminar (90 tentativas de 10s =
15 min). São 9 imagens: api-gateway, os 7 serviços e o frontend.

**Rollback** é o `workflow_dispatch` com o input `tag`: preenchido com um sha que
já está no ghcr, o build é pulado e aquelas imagens são apenas republicadas como
`:latest` — que é a única tag que a Coolify olha. `tag` vazio reconstrói o commit
atual, igual a um push.

Secrets usados: `PROD_ENV`, `COOLIFY_URL`, `COOLIFY_TOKEN`, `COOLIFY_UUID`.

## `landing.yml` — Landing

`push` em `main` tocando `landing-page/**`, mais `workflow_dispatch`. Espelho do
`deploy.yml`, que ignora exatamente esse diretório: uma mudança de um lado nunca
acorda o outro.

Monta um `dist/` com `index.html`, `404.html`, `.image-slots.state.json` e
`assets/`, e publica com `wrangler@4 pages deploy --project-name runas-landing
--branch main`. Secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.

## `uptime.yml` — Uptime

`schedule` com `cron: '*/10 * * * *'` e `workflow_dispatch` (com input `url`
para ensaiar o alarme). Sonda `https://app.runaserp.com.br/api/health/ready` —
readiness, não liveness: cobre banco, Redis e os 7 serviços, e o corpo do 503 diz
qual caiu. Três tentativas com 20s entre elas; falhando as três, alerta no
Telegram (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`), com o e-mail de falha do
GitHub como fallback se os secrets não existirem.

O `-A` do curl é obrigatório: a zona tem regra de WAF que desafia qualquer
User-Agent contendo `curl` ou `wget` e responde 403 na borda.

O cron pede 10 minutos, mas o GitHub estrangula agendamentos: o próprio arquivo
registra duas execuções reais 32 minutos separadas. A detecção é na casa das
dezenas de minutos.

## `graphify-update.yml` — Auto-Update Graphify Knowledge Graph

**Dispara só em `main`** (`push`, filtrado por `**.py`, `**.ts`, `**.tsx`,
`**.js`, `**.jsx`, `**.vue`), mais `workflow_dispatch`. Não roda em `Developer`:
o bot commita o `graphify-out/` regenerado na branch onde roda, então as duas
branches divergiam nos mesmos arquivos gerados e todo merge para `main`
colidia (o racional, com os PRs que colidiram, está em `graphify-update.yml:5-9`). O próprio arquivo registra que `master` não existe neste repositório.

Passos: instala `graphifyy` (Python 3.11), confere se o último commit realmente
tocou código, roda `graphify update`, e se o `graphify-out/` mudou, commita como
`chore(graphify): auto-update knowledge graph [skip graphify]` e dá push de volta.

Duas travas contra loop:

- o job tem `if: !contains(head_commit.message, '[skip graphify]')`, então o
  próprio commit do bot não o redispara;
- o push usa `GITHUB_TOKEN`, e **um push feito com esse token não dispara
  workflow nenhum** — um refresh do grafo nunca causa deploy.

### Execução manual

**Actions** → **Auto-Update Graphify Knowledge Graph** → **Run workflow**.
(`deploy.yml`, `landing.yml` e `uptime.yml` também têm `workflow_dispatch`; o `ci.yml` não.)

---

**Última atualização**: 2026-09-26
