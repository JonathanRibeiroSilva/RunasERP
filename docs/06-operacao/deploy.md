# Deploy — como funciona

Este documento descreve o caminho de um commit ate producao **quando tudo da certo**.
Quando quebra, va para [`runbook-producao.md`](runbook-producao.md).

Toda afirmacao aqui foi lida do arquivo citado. Onde nao deu para confirmar, ha uma
linha `A CONFIRMAR`.

---

## 1. O caminho, em uma frase

Merge em `main` -> GitHub Actions constroi as 9 imagens e publica no **ghcr.io** ->
o runner chama a API do **Coolify** pelo hostname Cloudflare -> o Coolify, na VPS,
**puxa** as imagens e sobe o stack -> o **tunel Cloudflare** (`cloudflared`, um
container do proprio stack) e o unico caminho de entrada.

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
| `ci.yml` | `pull_request` para `main`/`Developer`; `push` nessas duas | 4 jobs de gate (build, frontend, backend, services) |
| `deploy.yml` | `push` em `main`; `workflow_dispatch` | constroi, publica no ghcr e manda o Coolify subir |
| `landing.yml` | `push` em `main` tocando `landing-page/**`; `workflow_dispatch` | publica a landing no Cloudflare Pages |
| `uptime.yml` | cron `*/10 * * * *`; `workflow_dispatch` | sonda producao e alerta no Telegram |
| `graphify-update.yml` | `push` em `main` tocando codigo; `workflow_dispatch` | regenera `graphify-out/` e commita de volta |

### ci.yml — o gate

Dispara em `pull_request` para `[main, Developer]` e em `push` para as mesmas duas
branches (`ci.yml:3-9`). `main` esta na lista de push de proposito: um hotfix
empurrado direto para `main` pularia o gate do PR, e e de `main` que o deploy
constroi (`ci.yml:6-7`).

O `paths-ignore` (`landing-page/**`, `docs/**`, `**.md`) vale **so no push** — o
bloco esta aninhado sob `push:` (`ci.yml:16-19`). Um PR roda o gate inteiro sempre,
aconteca o que acontecer no diff (`ci.yml:10-15`). Repare que a lista e a mesma do
`deploy.yml` **menos** `.github/**`: mudar um workflow nao muda o que roda em
producao, mas muda o que a CI faz, e essa e a unica chance de valida-lo fora de um PR
(`ci.yml:13-15`).

Os 4 jobs:

- **build** (`ci.yml:24`) — valida os dois composes com `docker compose config`
  (`ci.yml:32-35`), constroi todas as imagens de producao com o par
  `docker-compose.prod.yml + docker-compose.build.yml` (`ci.yml:39-40`) e roda um
  smoke-test do `passlib`/`bcrypt` **dentro** das imagens de `api-gateway-prod` e
  `vendas-prod` (`ci.yml:55-72`).
- **frontend** (`ci.yml:74-93`) — `npm ci`, `npm run lint`, `npm run build`,
  `npm run test -- --run`, em Node 22.
- **backend** (`ci.yml:95-109`) — `pytest -c tests/pytest.ini tests/unit` em
  Python 3.12.
- **services** (`ci.yml:115-181`) — matriz de 8 legs (`api-gateway` + os 7 servicos),
  cada uma com Postgres 15 e Redis 7 como service containers, rodando
  `postgres/init-schemas.sql` (`ci.yml:171-172`), depois `alembic upgrade head` a
  partir de um banco vazio (`ci.yml:177-178`), e so entao `pytest tests`
  (`ci.yml:180-181`).

### deploy.yml — o unico que toca producao

**Gatilho.** `push` em `main` (`deploy.yml:16-17`) e `workflow_dispatch`
(`deploy.yml:53-58`). `Developer` chega em `main` por pull request, que e onde a CI
faz o gate (`deploy.yml:3-4`).

**paths-ignore** (`deploy.yml:42-47`): `landing-page/**`, `docs/**`, `**.md`,
`.github/**`, `scripts/**`. As duas ultimas entradas tem historia registrada no
proprio arquivo: o PR #26 mudou so `404.html`, `landing.yml` e `deploy.ps1` — nada
que rode em producao — e o deploy que isso disparou abortou no meio, deixando a
aplicacao fora do ar por 25 minutos (`deploy.yml:24-31`). `scripts/**` entrou pela
mesma evidencia: nenhum Dockerfile copia de `scripts/` (`deploy.yml:36-41`).

`docker-compose.prod.yml` esta **deliberadamente fora** do `paths-ignore`: ele mora
na raiz, o Coolify o le, e uma mudanca nele **tem** de chegar em producao
(`deploy.yml:33-34`).

Concorrencia: grupo `deploy-production` com `cancel-in-progress: false` — um segundo
push espera o primeiro em vez de correr com ele ate o registry (`deploy.yml:60-63`).

**Os passos** (job `deploy`, `ubuntu-latest`, `packages: write`):

1. **Write build env** (`deploy.yml:82-86`) — escreve o secret `PROD_ENV` num `.env`.
   O Compose nao parseia sem as entradas `${VAR:?}`, e os `VITE_*` sao assados no
   bundle em tempo de build, entao esses valores precisam estar corretos **no
   runner** (`deploy.yml:78-81`). O Coolify continua sendo a fonte da verdade do que
   e lido em runtime.
2. **Login no ghcr** (`deploy.yml:88-92`) — `docker/login-action` contra `ghcr.io`
   com o `GITHUB_TOKEN`.
3. **Publish images** (`deploy.yml:113-131`) — `docker compose -f
   docker-compose.prod.yml -f docker-compose.build.yml build --build-arg
   BUILDKIT_INLINE_CACHE=1` seguido de `push` (o par de arquivos vem de `env.FILES`,
   `deploy.yml:66`). Depois cada imagem e re-tagueada e empurrada como `:latest`,
   porque e so isso que o Coolify olha; as tags `:<sha>` ficam no ghcr e sao o alvo
   de um rollback (`deploy.yml:126-131`).
4. **Trigger Coolify deploy** (`deploy.yml:158-167`) —
   `POST ${COOLIFY_URL}/api/v1/deploy?uuid=${COOLIFY_UUID}&force=false`, com
   `Authorization: Bearer ${COOLIFY_TOKEN}`, `--connect-timeout 10 --retry 5
   --retry-delay 10`. O `deployment_uuid` da resposta e lido com `jq`.
5. **Wait for Coolify to finish** (`deploy.yml:187-239`) — polling em
   `${COOLIFY_URL}/api/v1/deployments/<uuid>`, 90 tentativas de 10s (15 min).

**Tres coisas nao obvias nesses dois ultimos passos:**

- `COOLIFY_URL` tem de ser o **hostname Cloudflare na frente do tunel**, nunca o IP
  da VPS. Apontar para o IP pede que um runner do GitHub abra uma conexao de
  **entrada** na VPS, e isso e cara ou coroa: a run 32047638162 respondeu em 0,5s e a
  32048659255, quinze minutos depois, comeu 132s de connect timeout com o host
  ocioso e a porta escutando (`deploy.yml:137-146`). Pelo tunel, a VPS disca para
  fora e o runner so fala com o edge anycast.
- O `-A 'Mozilla/...'` **nao e cosmetico**: a zona tem uma regra de WAF
  ("User-Agent suspeito") que desafia qualquer UA contendo `curl` ou `wget` e
  responde 403 no edge, com `Cf-Mitigated: challenge` (`deploy.yml:152-157`).
- **Perder a API no meio do deploy e esperado.** O `cloudflared` e um container do
  proprio stack sendo derrubado, entao o Coolify para o tunel por onde essa
  requisicao viaja e o edge passa a responder 530 ate o stack novo subir. Por isso o
  loop tolera ate **45 respostas inalcancaveis** (~10-15 min de silencio) antes de
  desistir (`deploy.yml:203-218`).

Em falha, o passo imprime o log do deploy vindo do proprio registro do Coolify,
filtrando as linhas de progresso de pull (`deploy.yml:226-234`).

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
outros workflows**, entao um refresh do grafo nunca deploya (`deploy.yml:14-15`).

### dependabot.yml

Tres ecossistemas, todos semanais (`dependabot.yml:9-38`): `github-actions` em `/`,
`npm` em `/frontend`, `pip` em `/api-gateway`, `/services/*` e `/tests`. PRs
agrupados, nao um por pacote (`dependabot.yml:5-6`): um grupo para `github-actions`,
um para `npm` e **dois** para `pip` — `python-auth` (`bcrypt`, `passlib`,
`python-jose`, `cryptography`, `python-multipart`) separado de `python` (`*`), porque
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
junto com `BUILDKIT_INLINE_CACHE=1` em `deploy.yml:122`; tirar o build arg mata as
entradas de cache em silencio (`docker-compose.build.yml:31-33`).

A imagem do `frontend` e a unica especifica de ambiente: os `VITE_*` sao assados no
bundle em tempo de build, entao a CI tem de construi-la com os valores reais de
producao (`docker-compose.build.yml:94-112`). Na pratica `frontend/Dockerfile` nao
declara nenhum `ARG`, entao nenhum desses build args chega ao `npm run build` e o
bundle sai com os defaults do codigo — inclusive `VITE_HOST_PLATAFORMA`, que nem e
passada e vale `admin` (`frontend/src/config/host.ts:16`). Mudar o rotulo do host do
painel exige declarar o `ARG` no Dockerfile.

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
`postgres/init-schemas.sql` (`ci.yml:171-172`) e producao roda a copia inline.
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

Esta no proprio `workflow_dispatch` do `deploy.yml` (`deploy.yml:48-58`):

- Campo `tag` **vazio** -> reconstroi o commit atual, exatamente como um push faz.
- Campo `tag` com um **sha ja presente no ghcr** -> o build e pulado inteiro; as
  imagens sao puxadas e republicadas como `:latest`, que e a unica coisa que o
  Coolify olha (`deploy.yml:118-124`). Esse e o rollback.

O `ROLLBACK_TAG` e lido por `env:` e nao interpolado dentro do `run:` porque `${{ }}`
em `run:` e substituicao textual — uma tag contendo `$(...)` executaria no runner
(`deploy.yml:107-109`).

**O rollback so troca imagens de volta. Ele nao desfaz DDL** — todo servico roda
`alembic upgrade head` no boot (`docker-compose.prod.yml:85-87`). E por isso que o
`db-backup` existe.

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
  os nomes dos secrets aparecem: os quatro estao listados juntos no comentario
  `deploy.yml:9-10`, e no codigo `PROD_ENV` esta em `deploy.yml:85` e
  `COOLIFY_TOKEN`/`COOLIFY_URL`/`COOLIFY_UUID` em `deploy.yml:164-165`.
- **A CONFIRMAR:** a duracao real de um deploy. Os comentarios do `deploy.yml` citam
  "~15 minutos" (`deploy.yml:18-20`) e "um pull frio das nove imagens ja levou ~10"
  (`deploy.yml:195`), mas nada disso foi medido na escrita deste documento.
- **A CONFIRMAR:** o tamanho da janela de indisponibilidade por deploy.
  `deploy.yml:27-29` afirma que o Coolify derruba o stack antigo antes de o novo
  subir — ou seja, todo deploy e uma janela de queda — mas a duracao dela nao esta
  registrada em nenhum arquivo deste repositorio.
