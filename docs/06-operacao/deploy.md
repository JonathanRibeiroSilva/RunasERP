# Deploy — como funciona

Este documento descreve o caminho de um commit ate producao **quando tudo da certo**.
Quando quebra, va para [`runbook-producao.md`](runbook-producao.md).

Toda afirmacao aqui foi lida do arquivo citado. Onde nao deu para confirmar, ha uma
linha `A CONFIRMAR`.

---

## 1. O caminho, em uma frase

Merge em `main` -> GitHub Actions roda a CI inteira e, em paralelo, constroi as 9
imagens e publica `:<sha>` no **ghcr.io** -> com testes e smoke verdes, o runner
promove `:<sha>` para `:latest` e chama a API do **Coolify** pelo hostname Cloudflare
-> o Coolify, na VPS, **puxa** as imagens e sobe o stack -> o runner confere
`/api/health/ready` -> o **tunel Cloudflare** (`cloudflared`, um container do proprio
stack) e o unico caminho de entrada.

A VPS nunca constroi nada. `docker-compose.prod.yml` nao tem **um unico** `build:`
como chave de servico — verifique com `grep -nE '^\s+build:' docker-compose.prod.yml`,
que nao retorna nada. (Cuidado: `grep -c 'build:'` retorna **1**, e e o comentario da
linha 4 dizendo que nao ha nenhum.) O motivo esta escrito
no topo do arquivo: a VPS e 1 vCPU / 4 GB e nao constroi nove imagens sem matar o
stack que esta rodando (`docker-compose.prod.yml:1-10`).

---

## 2. Os workflows

Cinco workflows em `.github/workflows/` mais o `.github/dependabot.yml`.

| Arquivo | Dispara quando | O que faz |
|---|---|---|
| `ci.yml` | `pull_request` para `Developer`; `workflow_dispatch`; `workflow_call` (do `deploy.yml`) | gate escopado pelo diff: `checks` mais build, frontend, services e migration-replay |
| `deploy.yml` | `push` em `main`; `workflow_dispatch` | `test` e `publish` em paralelo, depois `deploy`: promove `:latest`, manda o Coolify subir e confere a saude |
| `landing.yml` | `push` em `main` tocando `landing-page/**`; `workflow_dispatch` | publica a landing no Cloudflare Pages |
| `uptime.yml` | cron `*/10 * * * *`; `workflow_dispatch` | sonda producao e alerta no Telegram |
| `graphify-update.yml` | `push` em `main` tocando codigo; `workflow_dispatch` | regenera `graphify-out/` e commita de volta |

### ci.yml — o gate

Tres gatilhos (`ci.yml:3-21`): `pull_request` para `Developer` e so ela
(`ci.yml:7-8`), `workflow_dispatch` (`ci.yml:10`) e `workflow_call`
(`ci.yml:12-21`). **Nao ha `push`.** Um PR `Developer` -> `main` nao tem CI proprio
de proposito: o merge em `main` passa pelo `deploy.yml`, que chama este workflow com
`full: true`, e um gatilho aqui rodaria a mesma CI duas vezes (`ci.yml:4-6`). O filtro
e pela base do PR: um PR empilhado (base diferente de `Developer`) nao dispara nada.

O `workflow_dispatch` roda tudo e serve para pre-checar uma branch antes do PR. O
`workflow_call` tem dois inputs: `full` (todos os escopos, seja qual for o diff) e
`build_images` (padrao `true`; o deploy passa `false`, porque o `publish` ja constroi)
(`ci.yml:12-21`). Um push novo no mesmo PR cancela a rodada anterior
(`ci.yml:31-33`).

**Escopo pelo diff.** O job `checks` decide o que o resto roda (`ci.yml:141-164`): em
PR, o `dorny/paths-filter` marca so o que o diff toca; em dispatch ou com `full`,
marca tudo. As chaves do filtro sao os proprios valores que os jobs consomem — um
diretorio de servico ou uma chave do `docker-compose.build.yml` (`ci.yml:59-62`) — e
`tests/unit/test_pipeline_ci_deploy.py` falha se um servico ficar sem chave.

Os jobs:

- **checks** (`ci.yml:39-181`) — roda sempre. Decide o escopo, valida os dois composes
  com `docker compose config` (`ci.yml:171-174`) e roda
  `pytest -c tests/pytest.ini tests/unit` em Python 3.12 (`ci.yml:180-181`). Esse
  passo e o que antes era o job `backend`.
- **build** (`ci.yml:189-233`) — so se ha imagem no escopo e `build_images` nao e
  `false` (`ci.yml:191-194`). Constroi **so as imagens afetadas**, com o par
  `docker-compose.prod.yml + docker-compose.build.yml` (`ci.yml:215-216`), e roda o
  smoke do `passlib`/`bcrypt` **dentro** de `api-gateway-prod` e `vendas-prod` quando
  uma das duas foi reconstruida (`ci.yml:223-233`).
- **frontend** (`ci.yml:235-257`) — so se o diff toca `frontend/` (`ci.yml:237`).
  `npm ci`, `npm run lint`, `npm run build`, `npm run test -- --run`, em Node 22.
- **services** (`ci.yml:263-316`) — so se ha servico no escopo (`ci.yml:265`). **Um
  job, nao uma matriz**: `bash scripts/ci-services.sh $SERVICES` (`ci.yml:316`), com
  Postgres 15 e Redis 7 como service containers (`ci.yml:268-281`). Para cada servico
  o script cria venv e banco proprios, roda `postgres/init-schemas.sql`
  (`scripts/ci-services.sh:58`), `alembic upgrade head` a partir de um banco vazio
  (`scripts/ci-services.sh:66`) e so entao `pytest tests`
  (`scripts/ci-services.sh:67`); roda todos e falha no fim. Oito legs cobravam oito
  minutos por ~3 s de teste cada (`ci.yml:259-262`).
- **migration-replay** (`ci.yml:335-384`) — em dispatch e no `full`; em PR, so se o
  diff toca migration, `database.py`, `postgres/**` ou `docker-compose.dev.yml`
  (`ci.yml:337-339`, filtro em `ci.yml:134-139`). Sobe os 8 apps contra **um unico**
  Postgres, de volume vazio (`ci.yml:357-361`), que e o formato de producao, e termina
  com `down -v` (`ci.yml:382-384`).

### deploy.yml — o unico que toca producao

**Gatilho.** `push` em `main` (`deploy.yml:20-21`) e `workflow_dispatch`
(`deploy.yml:57-69`). `Developer` chega em `main` por pull request **sem CI proprio**:
o portao e o proprio `deploy.yml`, que roda a CI inteira antes de promover
(`deploy.yml:15-17`).

**Forma.** Tres jobs (`deploy.yml:9-13`):

```text
test ──────┐   CI inteira (ci.yml com full), sem construir imagem
publish ───┴─► deploy   promove :<sha> para :latest, Coolify, health check
```

`test` e `publish` rodam em paralelo e o `deploy` espera os dois. Nada move o
`:latest` — o que o Coolify e o cache de build leem — antes de os testes e o smoke
passarem (`deploy.yml:12-13`).

**paths-ignore** (`deploy.yml:46-51`): `landing-page/**`, `docs/**`, `**.md`,
`.github/**`, `scripts/**`. As duas ultimas entradas tem historia registrada no
proprio arquivo: o PR #26 mudou so `404.html`, `landing.yml` e `deploy.ps1` — nada
que rode em producao — e o deploy que isso disparou abortou no meio, deixando a
aplicacao fora do ar por 25 minutos (`deploy.yml:28-35`). `scripts/**` entrou pela
mesma evidencia: nenhum Dockerfile copia de `scripts/` (`deploy.yml:40-45`).

`docker-compose.prod.yml` esta **deliberadamente fora** do `paths-ignore`: ele mora
na raiz, o Coolify o le, e uma mudanca nele **tem** de chegar em producao
(`deploy.yml:37-38`).

Concorrencia: grupo `deploy-production` com `cancel-in-progress: false` — um segundo
push espera o primeiro em vez de correr com ele ate o registry (`deploy.yml:72-74`).

**Os jobs, em ordem:**

1. **test** (`deploy.yml:89-98`) — chama o `ci.yml` com `full: true` e
   `build_images: false`. Pulado quando o dispatch traz `tag` (`deploy.yml:90`). As
   `permissions` repetem o que o `ci.yml` pede de si mesmo, senao o GitHub recusa a
   run inteira na abertura (`deploy.yml:86-88`).
2. **publish** (`deploy.yml:102-151`) — o runner constroi, a VPS so puxa:
   - **Write build env** (`deploy.yml:120-123`) — escreve o secret `PROD_ENV` num
     `.env`. O Compose nao parseia sem as entradas `${VAR:?}`, e os `VITE_*` sao
     assados no bundle em tempo de build, entao esses valores precisam estar corretos
     **no runner** (`deploy.yml:114-119`). O Coolify continua sendo a fonte da verdade
     do que e lido em runtime.
   - **Login no ghcr** (`deploy.yml:125-129`) — `docker/login-action` contra
     `ghcr.io` com o `GITHUB_TOKEN`.
   - **Build the images** (`deploy.yml:139-140`) — `docker compose $FILES build
     --build-arg BUILDKIT_INLINE_CACHE=1`, com `FILES` = o par
     `docker-compose.prod.yml + docker-compose.build.yml` (`deploy.yml:79-80`).
   - **Smoke de auth** (`deploy.yml:145-146`) — `scripts/ci-smoke-auth.sh`, antes do
     push: uma imagem que nao sabe hashear senha nao chega ao registry.
   - **Push** (`deploy.yml:150-151`) — **so a tag `:<sha>`**. O `:latest` nao e
     empurrado aqui; uma run que falha deixa `:<sha>` orfaos no ghcr e mais nada. As
     tags `:<sha>` ficam la e sao o alvo de um rollback.
3. **deploy** (`deploy.yml:161-267`; `deployments: write` so para registrar o sha no ar,
   `packages: write` para o `:latest`, `deploy.yml:166-169`) — roda depois de `test` e
   `publish`, **tambem quando os dois foram pulados** (`deploy.yml:163`: um rollback
   por `tag` nao tem `test` nem `publish`). O checkout traz o historico inteiro
   (`deploy.yml:175-176`), porque o rollback compara o sha no ar com o novo.
   1. **Write build env** e login (`deploy.yml:180-189`) — `docker compose config
      --images` tambem precisa das entradas `${VAR:?}`.
   2. **Read the live sha** (`deploy.yml:193-195`) — o sha do ultimo deployment `production` com sucesso,
      lido **antes** de promover; vazio se nenhum foi registrado ainda.
   3. **Promote the sha to latest** (`deploy.yml:198-200`) — `scripts/promote-latest.sh`
      copia o manifesto de `:<sha>` para `:latest` dentro do ghcr com `docker buildx
      imagetools create` (`scripts/promote-latest.sh:25-28`): nada e puxado para o
      runner, sao segundos. **Este e o momento em que a versao vai ao ar**, porque
      `:latest` e a unica tag que o Coolify olha.
   4. **Deploy through Coolify** (`deploy.yml:204-210`) — `scripts/coolify-deploy.sh`:
      `POST ${COOLIFY_URL}/api/v1/deploy?uuid=${COOLIFY_UUID}&force=false`, com
      `Authorization: Bearer ${COOLIFY_TOKEN}`, `--connect-timeout 10 --retry 5
      --retry-delay 10` (`scripts/coolify-deploy.sh:37-41`); o `deployment_uuid` da
      resposta e lido com `jq` (`:43`). Depois faz polling em
      `${COOLIFY_URL}/api/v1/deployments/<uuid>`, 90 tentativas de 10s = 15 min
      (`:60-101`).
   5. **Check production health** (`deploy.yml:217-227`) — `scripts/health-ready.sh`
      pede `GET https://app.runaserp.com.br/api/health/ready` ate 200: 18 tentativas
      de 10s, tres minutos (`scripts/health-ready.sh:6-7`, `:23-24`). Coolify terminar
      diz que os containers subiram, nao que o app responde. O passo tem
      `continue-on-error` para o rollback decidir (`deploy.yml:212-219`).
   6. **Mark the sha as production** (`deploy.yml:229-231`) — so com health verde,
      `scripts/production-sha.sh set $TAG`: um deployment `production` com status `success`, nao uma tag git (o `GITHUB_TOKEN` nao move tag para tras, nem por `git push` nem pela API, quando o `.github/workflows` dos dois shas difere). O ultimo deployment e o sha que
      passou no health check pela ultima vez, isto e, o que esta no ar; ninguem a cria
      a mao, o primeiro deploy verde faz (`deploy.yml:157-160`).
   7. **Automatic rollback** (`deploy.yml:240-267`) — so se o health falhou. Veja a
      secao 6.

**Tres coisas nao obvias no deploy pelo Coolify** (todas em
`scripts/coolify-deploy.sh`):

- `COOLIFY_URL` tem de ser o **hostname Cloudflare na frente do tunel**, nunca o IP
  da VPS. Apontar para o IP pede que um runner do GitHub abra uma conexao de
  **entrada** na VPS, e isso e cara ou coroa: a run 32047638162 respondeu em 0,5s e a
  32048659255, quinze minutos depois, comeu 132s de connect timeout com o host
  ocioso e a porta escutando (`scripts/coolify-deploy.sh:10-18`). Pelo tunel, a VPS
  disca para fora e o runner so fala com o edge anycast.
- O `-A 'Mozilla/...'` **nao e cosmetico**: a zona tem uma regra de WAF
  ("User-Agent suspeito") que desafia qualquer UA contendo `curl` ou `wget` e
  responde 403 no edge, com `Cf-Mitigated: challenge`
  (`scripts/coolify-deploy.sh:24-28`). O `health-ready.sh` carrega o mesmo `-A`
  (`scripts/health-ready.sh:14-16`).
- **Perder a API no meio do deploy e esperado.** O `cloudflared` e um container do
  proprio stack sendo derrubado, entao o Coolify para o tunel por onde essa
  requisicao viaja e o edge passa a responder 530 ate o stack novo subir. Por isso o
  loop tolera ate **45 respostas inalcancaveis** (~10-15 min de silencio) antes de
  desistir (`scripts/coolify-deploy.sh:69-86`).

Em falha, o script imprime o log do deploy vindo do proprio registro do Coolify,
filtrando as linhas de progresso de pull (`scripts/coolify-deploy.sh:92-98`).

### landing.yml

Espelho invertido do `deploy.yml`: aquele ignora `landing-page/**`, este observa
**so** `landing-page/**` (`landing.yml:9-15`). A landing e um site estatico no
Cloudflare Pages, projeto `runas-landing`, servindo o apex e o `www`
(`landing.yml:3-4`). Publica com `npx --yes wrangler@4 pages deploy dist
--project-name runas-landing --branch main --commit-dirty=true`
(`landing.yml:66-69`), a partir de uma copia encenada em
`dist/` (`landing.yml:52-57`). O app fica no subdominio, atras do tunel — nada disso
passa pela VPS.

Concorrencia ao contrario do deploy: `cancel-in-progress: true`, porque o Pages serve
o que terminou por ultimo (`landing.yml:20-25`).

### uptime.yml

Cron `*/10 * * * *` (`uptime.yml:20`), mas o proprio arquivo registra que o GitHub
estrangula agendamentos: com `*/10`, as duas primeiras execucoes reais cairam com 32
minutos de diferenca (`uptime.yml:14-19`). Sonda
`https://app.runaserp.com.br/api/health/ready` 3 vezes com 20s entre elas
(URL efetiva em `uptime.yml:31`, mesmo default do `workflow_dispatch` em
`uptime.yml:25`; o laco em `uptime.yml:58-67`) e, em falha, manda a mensagem no Telegram
(`uptime.yml:78-95`) — com fallback para o e-mail de falha do GitHub quando os
secrets nao existem (`uptime.yml:85-88`).

Usa `/api/health/ready` e nao `/api/health` porque o segundo e liveness e responde
200 com o Postgres morto; o `/ready` sonda banco, Redis e os sete servicos, e o corpo
do 503 diz qual caiu (`uptime.yml:39-42`).

### graphify-update.yml

So `main`, so arquivos de codigo (`**.py`, `**.ts`, `**.tsx`, `**.js`, `**.jsx`,
`**.vue`) — `graphify-update.yml:4-18`. Pula a si mesmo quando a mensagem do commit
contem `[skip graphify]` (`graphify-update.yml:27`) e commita `graphify-out/` com
essa marca (`graphify-update.yml:105`) usando o `GITHUB_TOKEN`
(`graphify-update.yml:109-114`). Um push feito com o `GITHUB_TOKEN` **nao dispara
outros workflows**, entao um refresh do grafo nunca deploya (`deploy.yml:18-19`).

### dependabot.yml

Tres ecossistemas, todos semanais (`dependabot.yml:9-38`): `github-actions` em `/`,
`npm` em `/frontend`, `pip` em `/api-gateway`, `/services/*` e `/tests`. PRs
agrupados, nao um por pacote (`dependabot.yml:5-6`): um grupo para `github-actions`,
um para `npm` e **dois** para `pip` — `python-auth` (`bcrypt`, `passlib`,
`pyjwt`, `cryptography`, `python-multipart`) separado de `python` (`*`), porque
um pacote cai no primeiro grupo que casa e o bcrypt 5 entrou em producao escondido
num PR de 27 pacotes (`dependabot.yml:39-48`). `typescript` e
`eslint` majors estao ignorados (`dependabot.yml:25-29`), e `bcrypt` major/minor
tambem (`dependabot.yml:53-55`).

---

## 3. Onde as imagens sao construidas

**No runner, nunca na VPS.** As secoes `build:` moram num arquivo separado,
`docker-compose.build.yml`, que **so a CI carrega** (`docker-compose.build.yml:1-6`).
O motivo e explicito: o Coolify constroi todo servico em que encontra um `build:`, e
com as secoes fora do arquivo que ele le, nao ha o que construir — so puxar.

Os nomes das imagens **nao** se repetem no `docker-compose.build.yml`: vem da chave
`image:` do `docker-compose.prod.yml`, para que o build tagueie exatamente o que
producao vai puxar (`docker-compose.build.yml:8-9`).

Sao **9 imagens**, publicadas em `ghcr.io/jonathanribeirosilva/runaserp/<nome>` (o
default de `${REGISTRY}`): `api-gateway`, `empresas`, `clientes`, `produtos`,
`estoque`, `vendas`, `financeiro`, `notificacoes`, `frontend`
(`docker-compose.prod.yml:287, 363, 382, 398, 414, 431, 470, 486, 511`).

`cache_from` aponta cada servico para o `:latest` ja publicado
(`docker-compose.build.yml:42-43` e analogos). Esse e o unico item daquele arquivo que
producao sente: sem ele, o `pip install` re-executava a cada run e gerava um digest
novo para dependencias identicas — o deploy `u6g9bhcoqgpxhhzel2thseg2` gastou 2m39s
puxando, 2m20s so extraindo, com o site fora do ar, para um commit cuja unica mudanca
era uma linha de YAML (`docker-compose.build.yml:11-25`). O `cache_from` so funciona
junto com `BUILDKIT_INLINE_CACHE=1` em `deploy.yml:140`; tirar o build arg mata as
entradas de cache em silencio (`docker-compose.build.yml:31-33`).

A imagem do `frontend` e a unica especifica de ambiente: os `VITE_*` sao assados no
bundle em tempo de build, entao a CI tem de construi-la com os valores reais de
producao (`docker-compose.build.yml:94-112`). Na pratica `frontend/Dockerfile` nao
declara nenhum `ARG`, entao nenhum desses build args chega ao `npm run build` e o
bundle sai com os defaults do codigo — inclusive `VITE_HOST_PLATAFORMA`, que nem e
passada e vale `admin` (`frontend/src/config/host.ts:16`). Mudar o rotulo do host do
painel exige declarar o `ARG` no Dockerfile, passá-lo em `docker-compose.build.yml` e
trocar o `^admin\.` fixo em `frontend/nginx.conf:72` (senão o próprio host novo do
painel recebe 404 em `/plataforma`).

---

## 4. O que a VPS faz

O Coolify le `docker-compose.prod.yml` e roda o equivalente a
`docker compose -f docker-compose.prod.yml up -d --wait` (`docker-compose.prod.yml:1-2`).

**15 servicos declarados**, sendo 2 one-shot (`db-backup`, `db-init`) e 13 de vida
longa (`docker-compose.prod.yml:51-571`).

### pull_policy: always

Todo servico da aplicacao tem `pull_policy: always` — pela ancora `x-service`
(`docker-compose.prod.yml:30`) e, no caso do `frontend-prod`, numa linha propria
porque ele nao usa a ancora (`docker-compose.prod.yml:516`). O motivo: `:latest` e
tag movel e o default `missing` do Compose mantem a copia que o host ja tem sem nunca
mais consultar o registry — foi assim que um deploy subiu com uma imagem de quinze
horas minutos depois de a CI publicar a nova, sem nada em log nenhum dizendo isso
(`docker-compose.prod.yml:26-30`).

### A ordem de subida

Cada servico da aplicacao espera (`docker-compose.prod.yml:31-37`): `db` healthy,
`db-init` completado com sucesso, `redis` healthy, `rabbitmq` healthy. Um Postgres
healthy nao e um Postgres utilizavel aqui: os servicos fazem
`CREATE TABLE <schema>.<tabela>` e o SQLAlchemy nunca cria o schema.

Antes disso, **`db-backup`** (`docker-compose.prod.yml:103-128`) dumpa o banco para o
bind mount absoluto `/data/erp/backups` (`docker-compose.prod.yml:115-116`) e o
`db-init` espera ele sair 0 (`docker-compose.prod.yml:147-148`). Fail-closed: um
deploy que nao consegue fazer backup nao migra. Bind mount absoluto e nao volume
nomeado porque o Coolify reescreve a secao `volumes` e descarta `external:`
(`docker-compose.prod.yml:98-102`) — a mesma observacao vale para `db_data`, que
**parece** protegido por `external: true` em `docker-compose.prod.yml:583-588` e,
segundo o comentario do proprio arquivo, nao esta.

**`db-init`** (`docker-compose.prod.yml:140-238`) cria os 9 schemas — `gateway`,
`empresas`, `clientes`, `produtos`, `estoque`, `vendas`, `financeiro`,
`notificacoes`, `evolution` — com SQL **inline no compose**, e o proprio arquivo diz
que isso e um espelho de `postgres/init-schemas.sql`
(`docker-compose.prod.yml:158-167`). **As duas copias tem de andar juntas**: a CI roda
`postgres/init-schemas.sql` (`scripts/ci-services.sh:58`) e producao roda a copia inline.
Divergiram, a CI valida algo que producao nao tem.

O SQL inline existe porque o Coolify copia so o arquivo de compose para
`/data/coolify/applications/<uuid>/` e mais nada; o `./postgres/init-schemas.sql`
relativo ao repo resolvia para um caminho inexistente, o Docker criava um diretorio
vazio no lugar e o `psql` morria com "could not read from input file: Is a directory"
(`docker-compose.prod.yml:59-64`).

### Sem portas de entrada

Nao ha nginx-prod nem Let's Encrypt: o TLS termina na Cloudflare e o trafego chega
pelo tunel, entao o host nao precisa de nenhuma porta inbound
(`docker-compose.prod.yml:9-10`). A infra (`db`, `redis`, `rabbitmq`) nao tem
mapeamento de porta para o host (`docker-compose.prod.yml:48-49`).

---

## 5. O tunel Cloudflare — dev e producao sao diferentes

Os dois usam a mesma imagem `cloudflare/cloudflared:latest`, e so.

**Desenvolvimento — modo credencial.** Sobe como extensao do ambiente de dev:

```
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
```

(`docker-compose.cloudflare.yml:4`). Roda `tunnel --config /etc/cloudflared/config.yml
run` (`docker-compose.cloudflare.yml:35`) e monta dois volumes: o
`cloudflared-config.yml` do repo e o `~/.cloudflared` da maquina, de onde sai o
arquivo de credencial (`docker-compose.cloudflare.yml:42-44`). O ingress esta **no
repo**: `cloudflared-config.yml` fixa o tunel
`2c06d803-6aeb-47da-afd0-c644e9ce3fba` e seu `credentials-file`
(`cloudflared-config.yml:1-2`) e roteia `app.runaserp.com.br ->
http://frontend-dev:3000`, com catch-all 404 (`cloudflared-config.yml:6-13`). Tem
`depends_on` de `frontend-dev` e `api-gateway` (`docker-compose.cloudflare.yml:36-38`)
e vive sob o profile `proxy` (`docker-compose.cloudflare.yml:50-51`).

**Producao — modo token, gerenciado pelo Coolify.** Nao ha arquivo de credencial para
montar: roda `tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}`
(`docker-compose.prod.yml:551`), e o ingress **nao** esta no repo — esta configurado
no dashboard do Cloudflare Zero Trust (`docker-compose.prod.yml:542-550`):

```
app.runaserp.com.br     -> http://frontend-prod:80
admin.runaserp.com.br   -> http://frontend-prod:80  (painel da plataforma)
coolify.runaserp.com.br -> http://host.docker.internal:8000
```

**`app` e `admin` sao o mesmo container.** Nao ha segunda imagem nem segundo
servico: o nginx do `frontend-prod` tem `server_name _` e serve o mesmo bundle aos dois
hosts, e quem decide qual aplicacao montar e o hostname lido no navegador
(`frontend/src/config/host.ts`; `docker-compose.prod.yml:549-550`). O backend tambem
nao muda: `/api/plataforma/*` responde nos dois hosts, protegido so por
`require_super_admin`. Detalhes em
[docs/03-arquitetura/plataforma.md §5](../03-arquitetura/plataforma.md).

O comentario do compose e so documentacao. A rota `admin.runaserp.com.br ->
frontend-prod:80` no tunel e o **Cloudflare Access** na frente do `admin` (policy
Allow por e-mail) estao configurados **fora do repositorio**, no painel da
Cloudflare, segundo verificacao de 2026-09-28: `admin` responde 302 para o login do
Access, `app` responde 200. Nada no codigo comprova ou recria isso — se o tunel for
refeito, a rota e a policy tem de ser refeitas a mao.

Estado em producao: o PR #113 (commit `4643422`) chegou a `main` pelo PR #114 (merge
`1df3a0f`, 2026-09-28) e o workflow Deploy desse push terminou com sucesso; em
2026-09-28 o bundle servido por `app.runaserp.com.br` ja continha a tela "Endereco
errado". **A CONFIRMAR:** o fluxo completo do super admin em `admin.` depois do login
do Access (nao testado).

O `extra_hosts: host.docker.internal:host-gateway`
(`docker-compose.prod.yml:557-558`) existe porque o Coolify escuta **no host**, nao na
`erp-network`. E isso que faz o gatilho de deploy chegar pelo tunel em vez de como
conexao de entrada no IP da VPS.

**O `cloudflared` de producao e o oposto de todos os outros servicos**
(`docker-compose.prod.yml:559-570`): **sem `depends_on`** e **sem
`pull_policy: always`**, os dois de proposito. Ele e o unico ingress e tem de
sobreviver aos containers que fronteia. Com `frontend-prod: {condition:
service_healthy}` ali, recriar o frontend recriava o tunel junto: ele se
desregistrava e a Cloudflare servia o **530** dela mesma — origem nenhuma — pela
cadeia inteira de healthcheck. Sem isso, o pior que um deploy faz e um 502 pelos
segundos em que o container do frontend nao existe, e o `cloudflared` re-resolve
`frontend-prod` a cada requisicao.

A imagem e distroless: nao ha shell para healthcheck. A verificacao e pelo log
(`docker-compose.prod.yml:574-575`):

```
docker logs erp-cloudflared-prod | grep "Registered tunnel connection"
```

---

## 6. Rollback

Tres caminhos, todos no `deploy.yml`.

**Automatico.** Se o health check pos-deploy falha (`deploy.yml:217-227`), o passo
**Automatic rollback** (`deploy.yml:240-267`) pergunta ao `scripts/rollback-decide.sh`
o que fazer, passando o sha que estava no ar (o do ultimo deployment `production`, lido antes de
promover) e os arquivos que mudaram entre ele e o novo (`deploy.yml:247-252`):

| Resposta | Quando | O que o job faz |
|---|---|---|
| `reverter` | nenhum arquivo de `alembic/versions/` no salto | promove o sha antigo de volta para `:latest`, redeploya pelo Coolify e confere a saude de novo (`deploy.yml:258-265`) |
| `migration` | o salto adiciona ou muda uma migration | **nao reverte** (`deploy.yml:256-257`): a migration ja rodou no boot, e a imagem velha subiria contra o schema novo, o que e pior que o deploy que falhou. A decisao e humana |
| `sem-producao` | nenhum deployment `production` registrado ainda | nao reverte (`deploy.yml:254-255`): o primeiro deploy verde o registra |

So `alembic/versions/` conta; `alembic.ini` e `env.py` nao mudam o schema
(`scripts/rollback-decide.sh:14-25`). O job termina **vermelho nos tres casos**,
porque o deploy pedido nao aconteceu (`deploy.yml:233-235`). A lista de arquivos vem
de uma atribuicao propria de proposito: se o `git diff` falhar (o sha no ar nao esta
no historico), o passo para, em vez de entregar uma lista vazia, que o script leria
como "sem migration" e reverteria as cegas (`deploy.yml:237-239`).

**Manual.** `workflow_dispatch` com o campo `tag` (`deploy.yml:59-62`):

- `tag` **vazio** -> `test` e `publish` rodam sobre o commit atual, exatamente como um
  push faz.
- `tag` com um **sha ja presente no ghcr** -> `test` e `publish` sao pulados
  (`deploy.yml:90`, `deploy.yml:103`) e o `deploy` promove aquele sha para `:latest`,
  que e a unica coisa que o Coolify olha (`deploy.yml:198-200`). Esse e o rollback
  manual. O health check roda igual e, se passar, o deployment `production` passa a registrar
  aquele sha.

O `tag` entra por `env:` (`TAG`, `deploy.yml:171`) e nao interpolado dentro do `run:`,
porque `${{ }}` em `run:` e substituicao textual — uma tag contendo `$(...)` executaria
no runner.

**Ensaio.** `ensaio_rollback` (`deploy.yml:66-69`), junto com `tag` = o sha no ar
(`scripts/production-sha.sh get`): a primeira consulta de saude pede um caminho que nao existe e desiste em
uma tentativa (`deploy.yml:223-225`), entao o rollback automatico roda de verdade com a
stack saudavel.

**O rollback so troca imagens de volta. Ele nao desfaz DDL** — todo servico roda
`alembic upgrade head` no boot (`docker-compose.prod.yml:85-87`). E por isso que o
`db-backup` existe, e por isso o automatico para quando o salto cruza uma migration.

---

## 7. A CONFIRMAR

- **A CONFIRMAR:** o valor de `COOLIFY_URL`. E um secret do repositorio, nao esta no
  codigo. O comentario em `docker-compose.prod.yml:547` mostra
  `coolify.runaserp.com.br -> http://host.docker.internal:8000` como rota do tunel, o
  que torna esse o candidato obvio, mas o valor efetivo do secret nao foi lido.
- **A CONFIRMAR:** a versao do Coolify em producao. `docker-compose.prod.yml:90` fala
  em "Coolify 4.3" e `uptime.yml:10` cita o codigo-fonte da "v4.1.2" — os dois
  comentarios nao concordam.
- **A CONFIRMAR:** como o app esta configurado **dentro** do Coolify (qual repo, qual
  branch, qual caminho de compose, qual UUID). Nada disso vive neste repositorio; so
  os nomes dos secrets aparecem: `PROD_ENV` em `deploy.yml:122` e `:182`, e
  `COOLIFY_URL`/`COOLIFY_TOKEN`/`COOLIFY_UUID` em `deploy.yml:207-209` (de novo em
  `deploy.yml:244-246`, no rollback).
- **A CONFIRMAR:** a duracao real de um deploy. Os comentarios do `deploy.yml` citam
  "~15 minutos" (`deploy.yml:22-23`) e "um pull frio das nove imagens ja levou ~10"
  (`scripts/coolify-deploy.sh:61`), mas nada disso foi medido na escrita deste documento.
- **A CONFIRMAR:** o tamanho da janela de indisponibilidade por deploy.
  `deploy.yml:31-32` afirma que o Coolify derruba o stack antigo antes de o novo
  subir — ou seja, todo deploy e uma janela de queda — mas a duracao dela nao esta
  registrada em nenhum arquivo deste repositorio.
