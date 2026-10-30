# GitHub Actions Workflows

Este diretório contém os workflows do RunasERP. São **5**, e cada arquivo carrega
nos próprios comentários o motivo de cada decisão (quais paths ignora, por que o
`-A` do curl existe, qual run de produção provou o quê). Este README é o índice;
o arquivo é a fonte da verdade.

| Workflow | Dispara em | Faz |
|---|---|---|
| `ci.yml` | PR para `Developer` + manual + chamado pelo `deploy.yml` | Portão de qualidade escopado pelo diff: `checks` e, conforme o escopo, `build`, `frontend`, `services`, `migration-replay` |
| `deploy.yml` | push em `main` + execução manual | `test ∥ publish → deploy`: testa tudo, publica `:<sha>` no ghcr, promove `:latest`, manda a Coolify subir e confere a saúde |
| `landing.yml` | push em `main` tocando `landing-page/**` + manual | Publica a landing no Cloudflare Pages |
| `uptime.yml` | cron + manual | Sonda produção e alerta no Telegram |
| `graphify-update.yml` | push em `main` tocando código + manual | Regenera e commita o `graphify-out/` |

**A CI não dispara em push.** O código chega em `Developer` por PR (com CI) e em
`main` por PR de promoção (sem CI próprio: o `deploy.yml` roda a CI inteira no merge).

---

## `ci.yml` — CI

Três gatilhos (`ci.yml:3-21`):

- `pull_request` **só para `Developer`** (`ci.yml:7-8`). O PR Developer → `main` não
  tem CI próprio de propósito: o merge em `main` passa pelo `deploy.yml`, que chama
  este workflow com `full`, e um gatilho aqui rodaria a mesma CI duas vezes
  (`ci.yml:4-6`). O filtro é pela BASE do PR: um PR empilhado (base diferente de
  `Developer`) não dispara nada, e "no checks reported" não é "rodando". Abra sempre
  contra `Developer`.
- `workflow_dispatch` (`ci.yml:10`): roda tudo, para pré-checar uma branch antes de
  abrir o PR (**Actions** → **CI** → **Run workflow**).
- `workflow_call` (`ci.yml:12-21`), usado pelo job `test` do `deploy.yml`, com dois
  inputs: `full` (todos os escopos, seja qual for o diff) e `build_images` (padrão
  `true`; o deploy passa `false` porque o `publish` já constrói as imagens).

Um push novo no mesmo PR cancela a rodada anterior (`ci.yml:31-33`); fora de PR o
grupo é o `run_id` e nada cancela nada.

O escopo vem do diff. O `checks` roda sempre e decide o que os outros jobs fazem
(`ci.yml:141-164`): em PR, o `dorny/paths-filter` marca só o que o diff toca; em
dispatch ou com `full`, marca tudo, então um serviço novo é testado sem editar o
`ci.yml`. Um PR que muda só `docs/` não gasta o ciclo das nove imagens, mas o
próprio `checks` ainda roda.

| Job | Roda quando | O que faz |
|---|---|---|
| `checks` | sempre | Decide o escopo (`ci.yml:39-164`), valida `docker-compose.prod.yml` e `docker-compose.dev.yml` com `docker compose config`, cada um com o próprio `.env*.example` (`ci.yml:171-174`), e roda os unitários `pytest -c tests/pytest.ini tests/unit` (`ci.yml:180-181`) |
| `build` | há imagem no escopo e `build_images` não é `false` (`ci.yml:191-194`) | Constrói **só as imagens afetadas** (`ci.yml:215-216`) e faz o smoke do `passlib`/`bcrypt` dentro de `api-gateway-prod` e `vendas-prod` quando uma delas foi reconstruída (`ci.yml:223-233`, `scripts/ci-smoke-auth.sh`) |
| `frontend` | o diff toca `frontend/**` (`ci.yml:237`) | Node 22, `npm ci`, `npm run lint`, `npm run build`, `npm run test -- --run`, dentro de `frontend/` (`ci.yml:235-257`) |
| `services` | há serviço no escopo (`ci.yml:265`) | **Um job só**, não uma matriz: `bash scripts/ci-services.sh $SERVICES` (`ci.yml:263-316`). Postgres 15 e Redis 7 como service containers; para cada serviço, venv e banco próprios, `postgres/init-schemas.sql`, `alembic upgrade head` a partir de um banco vazio e `pytest tests`. Roda todos e falha no fim, então um serviço quebrado não esconde os outros |
| `migration-replay` | fora de PR, ou PR que toca migration, `database.py`, `postgres/**` ou `docker-compose.dev.yml` (`ci.yml:337-339`) | Sobe o stack real num **único** Postgres, de volume vazio (`ci.yml:357-361`), que é o formato de produção; pega revisions de serviços diferentes brigando por um objeto compartilhado. Termina com `down -v` (`ci.yml:382-384`) |

O antigo job `backend` virou o passo "Unit tests" do `checks`. O job `services` não
tem mais `matrix`: oito legs cobravam oito minutos por ~3 s de teste cada
(`ci.yml:259-262`).

## `deploy.yml` — Deploy

```text
test ──────┐   CI inteira (ci.yml com full), sem construir imagem
publish ───┴─► deploy   promove :<sha> para :latest, Coolify, health check
```

Dispara em `push` em `main` (com `paths-ignore` para `landing-page/**`, `docs/**`,
`**.md`, `.github/**` e `scripts/**`, `deploy.yml:20-51`) e em `workflow_dispatch`
(`deploy.yml:57-69`). Todo merge em `main` fora do `paths-ignore` entrega: o PR de
promoção não roda CI, e este pipeline é o portão (`deploy.yml:15-17`). `test` e `publish` rodam em paralelo,
e o `deploy` espera os dois. Concorrência: grupo `deploy-production`, sem cancelar
(`deploy.yml:72-74`).

1. **`test`** (`deploy.yml:89-98`) — chama o `ci.yml` com `full: true` e
   `build_images: false`. Pulado quando o dispatch traz `tag`.
2. **`publish`** (`deploy.yml:102-151`) — o runner constrói as 9 imagens (a VPS
   nunca constrói), faz o smoke de auth **antes** do push e empurra **só** `:<sha>`
   (`deploy.yml:150-151`). Uma rodada que falha deixa `:<sha>` órfãos no ghcr e
   mais nada. Pulado quando o dispatch traz `tag`.
3. **`deploy`** (`deploy.yml:161-267`) — roda depois dos dois, e também quando
   foram pulados (`deploy.yml:163`: um rollback por `tag` não tem `test` nem
   `publish`). Em ordem:
   - lê o sha que está no ar, o do último deployment `production` com sucesso (`deploy.yml:193-195`);
   - **promove `:<sha>` para `:latest`** com `scripts/promote-latest.sh`
     (`deploy.yml:198-200`), uma cópia de manifesto dentro do ghcr: é a única tag
     que a Coolify lê, então este é o momento em que a versão vai ao ar;
   - manda a Coolify subir e espera terminar, `scripts/coolify-deploy.sh`
     (`deploy.yml:204-210`; 90 tentativas de 10 s = 15 min);
   - confere `GET /api/health/ready` por até 3 minutos, `scripts/health-ready.sh`
     (`deploy.yml:217-227`; 18 tentativas de 10 s);
   - se a saúde passou, grava o sha como deployment `production` (`deploy.yml:229-231`);
   - se não passou, o **rollback automático** (`deploy.yml:240-267`).

Este workflow não deploya: quem faz o deploy de fato é a Coolify, avisada por
`POST {COOLIFY_URL}/api/v1/deploy?uuid={COOLIFY_UUID}` e consultada em
`/api/v1/deployments/{uuid}` até terminar. São 9 imagens: api-gateway, os 7 serviços
e o frontend.

### O sha no ar e o rollback automático

O último deployment `production` com sucesso é o sha que **passou no health check pela última
vez**, isto é, o que está no ar (`deploy.yml:157-160`). Ninguém a cria à mão: nasce
no primeiro deploy verde e só anda depois de um health verde.

Se o health falha, `scripts/rollback-decide.sh` decide, a partir dos arquivos que
mudaram entre o sha no ar e o novo, uma de três respostas:

| Resposta | Significa | O job faz |
|---|---|---|
| `reverter` | sem migration no salto | promove o sha de volta, redeploya e reconfere a saúde |
| `migration` | o salto adiciona ou muda `alembic/versions/` | **não reverte**: a migration já rodou no boot, e imagem velha contra schema novo é pior que o deploy que falhou; a decisão é humana |
| `sem-producao` | nenhum deployment `production` registrado ainda | não reverte (o primeiro deploy fica sem rollback automático) |

O job termina **vermelho em todos os casos**, porque o deploy pedido não aconteceu
(`deploy.yml:233-235`).

### Rollback manual e ensaio

`workflow_dispatch` com o input `tag` (`deploy.yml:59-62`) preenchido com um sha que
já está no ghcr: `test` e `publish` são pulados e o `deploy` promove aquele sha para
`:latest`. `tag` vazio reconstrói o commit atual, igual a um push.

O input `ensaio_rollback` (`deploy.yml:66-69`) ensaia o rollback automático com a
stack saudável: use-o junto com `tag` = o sha no ar (`scripts/production-sha.sh get`); a primeira consulta
de saúde pede um caminho que não existe e desiste em uma tentativa
(`deploy.yml:223-225`), então o rollback roda de verdade.

Secrets usados: `PROD_ENV`, `COOLIFY_URL`, `COOLIFY_TOKEN`, `COOLIFY_UUID`. O
`deploy` pede `deployments: write` só para registrar o sha no ar (`deploy.yml:166-169`).

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
(`ci.yml`, `deploy.yml`, `landing.yml` e `uptime.yml` também têm `workflow_dispatch`.)

---

**Última atualização**: 2026-10-29
