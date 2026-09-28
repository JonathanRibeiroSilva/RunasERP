# Runbook de produção

Você está com o sistema quebrado e com pressa. Comando primeiro, explicação depois.

Toda afirmação aqui foi lida do código ou do config, com a fonte citada. Onde não
deu para confirmar, existe uma linha **A CONFIRMAR** — leia como lacuna, não como fato.

## Quando usar este documento

- Produção fora do ar, degradada, ou um deploy que não terminou.
- Alarme do Telegram (workflow `Uptime`).
- Precisa fazer rollback, restaurar backup, ou mexer na VPS.

Quando **não** usar: problema no seu ambiente local (docker compose de dev, teste que
falha na sua máquina) — isso é `docs/06-operacao/troubleshooting.md`. Nada aqui se
aplica a dev: o compose de produção é outro arquivo, sem `build:` e sem portas expostas.

---

## Fatos que mudam o diagnóstico (leia antes de investigar qualquer coisa)

1. **`/health` não prova nada.** Em `app.runaserp.com.br/health` quem responde é o
   nginx do frontend, com um `return 200 "ok\n"` estático (`frontend/nginx.conf:57-60`).
   No gateway, `/health` é liveness rasa de propósito — responde 200 com o Redis
   fora (`api-gateway/main.py:104-107`). **Use sempre `/api/health/ready`.**
2. **Toda requisição de diagnóstico precisa de `-A` com UA de navegador.** A zona tem
   uma regra de WAF ("User-Agent suspeito") que desafia qualquer UA contendo `curl`
   ou `wget` e devolve **403 do próprio edge**, sem tocar a VPS
   (`.github/workflows/deploy.yml:152-157`, `.github/workflows/uptime.yml:33-37`,
   `scripts/medir-downtime.sh:29-33`). Um curl padrão mede o Cloudflare, não o ERP.
3. **Todo deploy é uma janela de indisponibilidade, por desenho.** Não é incidente.
   Ver a seção [Deploy derruba a stack](#deploy-derruba-a-stack-inteira-isso-é-esperado).
4. **A VPS é apertada:** 1 vCPU / 4 GB, e é por isso que ela só puxa imagem, nunca
   constrói (`docker-compose.prod.yml:5-7`, `.github/workflows/deploy.yml:94-95`).

### O comando de diagnóstico

```bash
curl -sS -A 'Mozilla/5.0' -w '\n%{http_code}\n' \
  https://app.runaserp.com.br/api/health/ready
```

- **200** → banco, Redis e os 7 serviços estão de pé.
- **503** → o corpo traz `{"status":"degraded","down":[...]}` **nomeando quem caiu**
  (`api-gateway/health.py:20-36`, `api-gateway/main.py:154-171`).
- **502 / 530 / 403** → não é o readiness respondendo. Vá para
  [Códigos do edge](#códigos-do-edge-502-vs-503-vs-530-vs-403).

> **A CONFIRMAR:** o acesso SSH à VPS (hostname, alias, usuário) não está registrado
> em nenhum arquivo do repositório. Os comandos `docker ...` abaixo rodam **na VPS**.

---

## Como o deploy funciona (6 linhas)

1. Merge em `main` dispara `.github/workflows/deploy.yml` (`:16-17`), respeitando o
   `paths-ignore` (`:42-47` — `docs/`, `**.md`, `.github/`, `scripts/`, `landing-page/`
   não deployam; `docker-compose.prod.yml` **não** está na lista, de propósito: `:33-34`).
2. O runner constrói e publica as 9 imagens no ghcr (`:113-124`).
3. As mesmas imagens são republicadas como `:latest`, que é a única tag que o Coolify
   olha (`:126-131`).
4. O job faz POST em `${COOLIFY_URL}/api/v1/deploy?uuid=...` (`:158-167`).
5. O Coolify roda `docker compose -f docker-compose.prod.yml up -d --wait` na VPS,
   só puxando imagens — não há `build:` nenhum nesse arquivo
   (`docker-compose.prod.yml:1-7`).
6. O job fica em polling no registro de deploy do Coolify por até 15 min (`:187-239`).

`COOLIFY_URL` **tem de ser o hostname do Cloudflare na frente do túnel**, nunca o IP
da VPS: apontar para o IP pede ao runner do GitHub uma conexão *de entrada*, e isso é
cara ou coroa — a mesma chamada respondeu em 0,5 s numa run e estourou 132 s de
connect timeout quinze minutos depois, com o host ocioso (`deploy.yml:137-146`).

---

## ROLLBACK

```
GitHub → Actions → Deploy → Run workflow → input "tag" = <sha já publicado no ghcr>
```

Com `tag` preenchida, **nada é construído**: as imagens daquele sha são puxadas do ghcr
e republicadas como `:latest`, que é o que o Coolify consome
(`deploy.yml:48-58` e `:113-131`). Com `tag` vazia, o workflow reconstrói o commit atual,
igual a um push.

> ### ⚠️ O rollback reverte IMAGENS. Nunca reverte DDL.
> Cada serviço roda `alembic upgrade head` no boot, e o rollback só troca as imagens de
> volta — ele nunca desfaz DDL (`docker-compose.prod.yml:85-88`). **Migration ruim não
> volta por aqui.** Se o problema for de schema, o caminho é
> [restaurar o dump](#restore-do-dump).

---

## Deploy derruba a stack inteira (isso é esperado)

**O que você vê:** site fora do ar durante um deploy; 502 ou 530 no navegador.

**O que é:** o Coolify 4.3 para e remove **todo** container do app antes do `up -d`
(`docker-compose.prod.yml:90-91`; a mesma coisa dita em `deploy.yml:26-29`: "Coolify
tears the old stack down before the new one is up, so every deploy is an outage
window"). São 13 containers de vida longa mais 2 one-shot (`db-backup` e `db-init`,
ambos `restart: "no"`), pela lista de `container_name:` do compose.

**Não investigue.** Espere o deploy terminar e confirme com `/api/health/ready`.

Grandezas medidas que existem no repositório:

| Medida | Valor | Fonte |
|---|---|---|
| Deploy só do frontend | ~3 s de 502 (medido em 2026-08-24) | `uptime.yml:44-46` |
| Cadeia de healthcheck antes do ajuste de `start_interval` | ~90 s de site fora por deploy | `docker-compose.prod.yml:335-339` |
| Boot frio (túnel sobe antes do frontend existir) | ~20 s de 502 | `docker-compose.prod.yml:569-570` |
| "~2m26s" que o CI reporta | é o tempo do Coolify, **não** o que o visitante viu | `scripts/medir-downtime.sh:5-7` |

> **A CONFIRMAR:** a janela de ~80 s de indisponibilidade por deploy citada na
> auditoria não aparece em nenhum arquivo do repositório. Para ter o número real,
> rode `scripts/medir-downtime.sh` **de fora** durante um deploy (ver
> [Scripts de emergência](#scripts-de-emergência)) e registre o resultado aqui.

### "Deploy failed" com exit code 255

**Confira o exit code antes de investigar.** 255 costuma ser queda da conexão SSH
entre o Coolify e o host, não falha real do deploy — a stack pode ter subido normalmente.
Confirme pelo `/api/health/ready` e pelos containers antes de mexer em qualquer coisa.

> **A CONFIRMAR:** essa correspondência (255 = SSH) vem da operação, não de nenhum
> arquivo deste repositório — o `deploy.yml` fala com a API do Coolify e não usa SSH
> em nenhum passo. Anexe aqui o trecho do log do Coolify na próxima ocorrência.

### O job de deploy falhou dizendo "unreachable"

Perder a API do Coolify no meio do deploy é **esperado**: o `cloudflared` é um container
da própria stack sendo deployada, então o Coolify derruba o túnel pelo qual essa
requisição viaja, e o edge passa a responder 530 para o `COOLIFY_URL` até a stack nova
subir (`deploy.yml:203-209`). O workflow tolera ~45 falhas seguidas (~10-15 min) antes de
desistir (`deploy.yml:210-221`). Se ele desistiu, o túnel não voltou — aí produção está
fora de verdade.

---

## Backup: é ele que autoriza a migration

Antes de qualquer coisa neste deploy poder mudar o banco, o container
`erp-db-backup-prod` roda (`docker-compose.prod.yml:103-128`):

1. `pg_dump -Fc -f /backups/.parcial.dump`
2. valida com `pg_restore --list /backups/.parcial.dump`
3. só então renomeia para `/backups/erp-<UTC>.dump`
4. mantém os **14 dumps** mais recentes (`ls -1t /backups/erp-*.dump | tail -n +15 | xargs -r rm -f`)

**Fail-closed:** `db-init` espera o backup sair com 0
(`docker-compose.prod.yml:147-148`) e todo serviço espera o `db-init`
(`docker-compose.prod.yml:35`). **Deploy que não consegue fazer backup não migra.**

Os dumps ficam em **`/data/erp/backups`** na VPS — bind mount absoluto
(`docker-compose.prod.yml:116`), e não volume nomeado, porque o Coolify reescreve a
seção `volumes` e descarta `external:` (`docker-compose.prod.yml:98-102`). Consequência
direta: a proteção que o `external: true` do `db_data` aparenta dar
(`docker-compose.prod.yml:583-588`) **não existe em produção**.

Limite conhecido: mesmo disco do banco. Cobre migration ruim ou escrita ruim —
**não** cobre perder a VPS. Off-site continua em aberto (`docker-compose.prod.yml:100-102`).

```bash
# na VPS: o que existe
ls -lht /data/erp/backups
# o último deploy fez backup?
docker logs erp-db-backup-prod        # imprime "backup ok: <arquivo> (<tamanho>)"
```

> Não confunda com `GET /plataforma/tenants/{id}/dumps`: essa rota devolve lista vazia
> e `"restauracao": "manual"` — ela é placeholder de tela, não lista estes dumps
> (`api-gateway/routers/plataforma.py:390-405`).

### RESTORE do dump

O dump está no host (`/data/erp/backups`) e **não** está montado dentro de
`erp-db-prod`; quem tinha o mount foi o `erp-db-backup-prod`, que já saiu. Rode um
container descartável na mesma rede (`runaserp_erp-network`,
`docker-compose.prod.yml:598-600`), com o mesmo mount:

```bash
# 1. PARE quem escreve no banco: o gateway, os 7 serviços e o frontend
#    (deixe db/redis/rabbitmq de pé; o cloudflared também fica, ou você perde o túnel)
docker stop erp-api-gateway-prod erp-empresas-prod erp-clientes-prod \
            erp-produtos-prod erp-estoque-prod erp-vendas-prod \
            erp-financeiro-prod erp-notificacoes-prod erp-frontend-prod

# 2. Escolha o dump e confira que ele abre
ls -lht /data/erp/backups
docker run --rm -v /data/erp/backups:/backups postgres:15-alpine \
  pg_restore --list /backups/erp-<CARIMBO>.dump | head

# 3. Restaure. As credenciais são as mesmas do compose (POSTGRES_USER,
#    POSTGRES_PASSWORD, POSTGRES_DB), mas elas NÃO estão no shell do host —
#    o Coolify é quem as injeta nos containers. Exporte os valores antes.
docker run --rm --network runaserp_erp-network \
  -v /data/erp/backups:/backups \
  -e PGPASSWORD="$POSTGRES_PASSWORD" postgres:15-alpine \
  pg_restore -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
             --clean --if-exists /backups/erp-<CARIMBO>.dump

# 4. Suba os apps de volta (os mesmos nomes do passo 1)
docker start erp-api-gateway-prod erp-empresas-prod erp-clientes-prod \
             erp-produtos-prod erp-estoque-prod erp-vendas-prod \
             erp-financeiro-prod erp-notificacoes-prod erp-frontend-prod
```

> `docker start`, e não `docker compose up -d`: **o repositório não existe na VPS**.
> O Coolify copia só o `docker-compose.prod.yml` para
> `/data/coolify/applications/<uuid>/` e mais nada (`docker-compose.prod.yml:59-64`),
> então um `docker compose -f docker-compose.prod.yml ...` de qualquer outro diretório
> falha por falta do arquivo. Se precisar mesmo do compose, rode de dentro dessa pasta —
> e note que isso reexecuta `db-backup` e `db-init`.

> **A CONFIRMAR:** este procedimento é derivado do que o compose declara
> (rede, mount, credenciais, formato `-Fc`), mas **não há registro de ele ter sido
> executado em produção**. Ensaie numa cópia antes de precisar dele, e corrija estes
> passos com o que acontecer de verdade. Atenção especial ao `--clean --if-exists`:
> ele derruba os objetos existentes antes de recriar.

### Migrations em produção

Cada serviço roda `alembic upgrade head` como **subprocesso** no lifespan
(`api-gateway/database.py:47-66`, chamado em `api-gateway/main.py:41,45`). Não é pelo
API Python do alembic porque `alembic/env.py` chama `fileConfig()`, que substituiria a
configuração de logging do app em execução.

**A falha é FATAL de propósito:** `subprocess.run(..., check=True)` derruba o startup —
o container entra em **crashloop**, não em degradação. Servir com schema velho é pior
que container reiniciando (o `check=True` está em `api-gateway/database.py:64-65`; o
porquê, em `:52-53`).

Os baselines já estão carimbados (ex.: `services/financeiro/alembic/versions/20260919_baseline.py`,
que escreve a primeira linha em `financeiro.alembic_version` e não roda DDL nenhum),
**mas uma revision nova RODA no boot**. Uma constraint que não passa nos dados de
produção = crashloop, não aviso.

Há ainda uma guarda explícita: se `alembic/versions/` chegar vazio na imagem, o boot
falha com mensagem própria em vez de subir healthy com schema vazio
(`api-gateway/database.py:56-64`).

---

## Diagnóstico por sintoma

### Códigos do edge: 502 vs 503 vs 530 vs 403

Tabela de leitura dos códigos, como o próprio medidor documenta
(`scripts/medir-downtime.sh:17-22`):

| Código | O que provavelmente é | Como confirmar | Como resolver |
|---|---|---|---|
| **530** | `cloudflared` caiu — Cloudflare error 1033, **não há origin registrado** | `docker logs erp-cloudflared-prod \| grep "Registered tunnel connection"` (imagem distroless, sem shell: é a única verificação possível — `docker-compose.prod.yml:574-575`) | Se for durante um deploy, espere. Senão: `docker start erp-cloudflared-prod` |
| **502/504** | Túnel de pé, container do **frontend** não existe naquele instante | `docker ps -a \| grep erp-frontend-prod` | Durante deploy: esperado (`docker-compose.prod.yml:565-570`). Fora de deploy: ver [crashloop](#container-em-crashloop) |
| **503** | Veio do **readiness**, e o corpo nomeia quem caiu | leia o `"down":[...]` da resposta | trate o serviço nomeado |
| **403** | **WAF do Cloudflare**, não o backend | header `Cf-Mitigated: challenge` na resposta | refaça com `-A 'Mozilla/5.0'` |
| **000** | a sonda não conectou (rede local / DNS) — **não é downtime do site** | — | conserte sua rede |

Por que o 530 é pior que o 502, e por que o compose é assim de propósito: o `cloudflared`
**não** tem `depends_on` nem `pull_policy: always`, ao contrário de todos os outros
serviços. Com `frontend-prod: {condition: service_healthy}` ali, recriar o frontend
recriava o túnel junto: ele desregistrava e o Cloudflare servia a própria página 530
durante toda a cadeia `api-gateway -> frontend`. Sem isso, o pior que um deploy faz é
502 pelos segundos em que o container do frontend não existe
(`docker-compose.prod.yml:560-570`).

### `/` responde 200 mas `/api` responde 502

**O que provavelmente é:** o nginx do frontend cacheou o IP antigo do gateway. O gateway
é recriado a cada deploy e ganha IP novo; o frontend só é recriado quando a imagem dele
muda. Com hostname literal no `proxy_pass`, o nginx resolve uma vez no boot e cacheia
para sempre — no deploy `p29ktqvytryu78w81d66l7jz` esse nginx passou **20+ min**
proxiando para um container morto (`frontend/nginx.conf:26-33`).

**Como confirmar:** o `/api/health/ready` dá 502 (HTML do nginx, não JSON) enquanto
`curl` de dentro da rede para o gateway responde:

```bash
docker exec erp-frontend-prod wget -qO- http://api-gateway-prod:8000/health
```

**Como resolver:** `docker restart erp-frontend-prod`.

**Correção permanente já está no código:** `resolver 127.0.0.11 valid=10s` + hostname em
variável (`set $gateway api-gateway-prod:8000`), que força resolução por requisição
(`frontend/nginx.conf:34-37`). Se o sintoma aparecer, **verifique se a imagem do frontend
em produção já tem esse bloco** — uma imagem anterior à correção ainda cacheia.

### 403 em PUT / PATCH / DELETE no `/api`

**Cheque o Cloudflare antes de culpar a aplicação:**

```bash
curl -sSI -X PUT -A 'Mozilla/5.0' https://app.runaserp.com.br/api/<rota> | grep -i cf-
```

Se aparecer **`Cf-Mitigated: challenge`**, quem respondeu foi o edge — a requisição nunca
chegou à VPS, e não há nada para procurar no log do gateway. A regra de WAF conhecida e
documentada é a de **User-Agent** (`deploy.yml:152-157`): `curl/8.5.0` → 403 do edge,
UA Mozilla → resposta real do backend, mesma URL e mesmo método.

> **A CONFIRMAR:** uma regra de WAF que desafie especificamente métodos de escrita
> (PUT/PATCH/DELETE) não está documentada em nenhum arquivo do repositório — só a regra
> de User-Agent está. Se o `Cf-Mitigated` aparecer com UA de navegador, registre aqui
> qual regra da zona disparou.

### Tela "Endereço errado" depois do login

**O que é:** não é falha. O painel da plataforma e o ERP dos lojistas são o mesmo
bundle, e o hostname decide qual aplicação ele monta (`frontend/src/config/host.ts`).
`escolherPorta()` mostra a tela `PortaErrada` (`frontend/src/App.tsx:88-106`) quando a
conta entrou pelo host errado:

- **super admin** entrando por `app.runaserp.com.br` → tem de entrar por
  `admin.runaserp.com.br`;
- **lojista** (ADMIN/OPERADOR) entrando por `admin.runaserp.com.br` → tem de entrar por
  `app.runaserp.com.br`.

**Como resolver:** clicar em **Sair** e fazer login de novo no host certo. É tela e
não redirect de propósito: o cookie de sessão é host-only (`set_auth_cookies` não
passa `domain=`, `api-gateway/routers/auth.py:29`), então a sessão de um host não
existe no outro. `/perfil` funciona nos dois. No host `app` a tela diz só "Esta conta
não tem acesso a este sistema.", sem nomear o painel.

**`/plataforma` no host `app` devolve 404 do nginx:** também não é falha. O
`frontend/nginx.conf` responde 404 em `/plataforma` quando o host não começa com
`admin.`, para o endereço não revelar que o painel existe. O painel é só
`admin.runaserp.com.br/plataforma`.

**Antes do login do app, o `admin` exige o login do Cloudflare Access** (302 para
`*.cloudflareaccess.com`). Quem não passa dali não está na policy Allow por e-mail,
configurada fora do repositório (painel da Cloudflare), segundo verificação de
2026-09-28 — isso não é problema do app, e o log do gateway não terá nada.

A separação é só de UI: `/api/plataforma/*` responde nos dois hosts e continua
protegido por `require_super_admin`. Em dev (`localhost`) a tela não aparece — as duas
aplicações convivem; use `admin.localhost:3000` para reproduzir o comportamento de
produção.

### Container em crashloop

```bash
docker ps -a --filter name=erp- --format '{{.Names}}\t{{.Status}}'
docker logs --tail 100 erp-<servico>-prod
```

**Onde olhar a migration culpada:** o `alembic upgrade head` roda no startup, antes de
qualquer log de requisição. Procure no log, nessa ordem:

1. a linha `gateway.starting` (ou equivalente do serviço) sem a `gateway.started`
   depois — o boot morreu entre as duas, ou seja, dentro do `init_db()`
   (`api-gateway/main.py:41-47`);
2. o traceback de `subprocess.CalledProcessError` / a saída do alembic com o nome da
   revision e o erro do Postgres;
3. `alembic/versions/ sem revisions` → a imagem foi construída sem as migrations,
   problema de `.dockerignore`, não de banco (`api-gateway/database.py:56-64`).

Se a revision nova falhou por causa dos dados (constraint), rollback de imagem **não
resolve** — ou corrige-se a migration e faz-se um novo deploy, ou
[restaura-se o dump](#restore-do-dump).

Lembre também que **o Docker nunca age no `unhealthy`**: `restart: unless-stopped`
reinicia em saída de processo, não em probe falhando — um container pode ficar parado
ali, `unhealthy` e `running` (`uptime.yml:3-6`).

### O alarme do Telegram tocou

O workflow `Uptime` sonda `https://app.runaserp.com.br/api/health/ready` 3x com 20 s de
intervalo, e só então alarma (`uptime.yml:58-73`). A mensagem já carrega o `"down":[...]`
quando a resposta veio do readiness; quando vem "sem detalhe", a resposta **não** era do
readiness (foi 502/530/403) — e isso já é informação (`uptime.yml:68-71`, `:91`).

Nessa ordem:

1. **Tem deploy em andamento?** Se sim, é o comportamento esperado — a tolerância inteira
   são 3 tentativas x 20 s, e um deploy de backend mostra 503 por mais tempo que isso
   (`uptime.yml:48-51`). Espere e reconfira.
2. `curl -sS -A 'Mozilla/5.0' https://app.runaserp.com.br/api/health/ready` — leia o `down[]`.
3. Sem resposta do readiness → [Códigos do edge](#códigos-do-edge-502-vs-503-vs-530-vs-403).
4. Na VPS: `docker ps -a --filter name=erp-` e o log de quem estiver fora.

Duas limitações que você precisa saber ao interpretar o alarme:

- **Detecção é de dezenas de minutos**, não de 10: o GitHub estrangula cron agendado —
  com `*/10` as duas primeiras execuções reais saíram com 32 min de diferença
  (`uptime.yml:14-20`).
- **A notificação "Container Status Changes" do Coolify não cobre isto**: o dispatch de
  `ContainerStopped` está comentado nos dois pontos de chamada em
  `app/Actions/Docker/GetContainersStatus.php` na v4.1.2. O Coolify cobre o servidor e o
  deploy; nada além deste workflow cobre a aplicação (`uptime.yml:8-11`).

Para ensaiar o alarme sem quebrar nada: `workflow_dispatch` do Uptime com o input `url`
apontando para outra coisa (`uptime.yml:21-25`).

---

## Scripts de emergência

### `scripts/resgate-vps.sh` — rode NA VPS ANTES de destruir qualquer coisa

```bash
bash scripts/resgate-vps.sh
# PRONTO: /tmp/resgate-vps.tar.gz — baixe com scp antes de destruir qualquer coisa.
```

Gera `/tmp/resgate-vps.tar.gz` com (`scripts/resgate-vps.sh:7-33`):
inventário de containers/volumes/redes; `working_dir` e `config_files` de cada stack
compose ativa (revela **qual** compose subiu o banco); os arquivos que não estão no git
(`nginx`, `.env`, `docker-compose*.yml`, `cloudflared-config.yml`); um `pg_dumpall` do
container de banco que ele encontrar; e os certificados do volume `letsencrypt-certs`,
se existir.

Traga o tarball para fora com `scp` **antes** de remover volume, container ou a VPS.

### `scripts/medir-downtime.sh` — mede o downtime real, de fora

```bash
./scripts/medir-downtime.sh              # sonda 1x/s até Ctrl-C e imprime o resumo
./scripts/medir-downtime.sh resumo x.csv # reanalisa um csv já gravado
./scripts/medir-downtime.sh teste        # autoteste do resumo
```

Sonda dois alvos em paralelo, que separam as camadas (`scripts/medir-downtime.sh:13-15`):
`/health` = túnel + container do frontend; `/api/health` = túnel + frontend + gateway
(o caminho real do usuário). Ajustável por env: `BASE`, `INTERVALO`, `TIMEOUT`
(`:24-27`). Se aparecer 403 no resumo, ele avisa que **a medição não vale** — foi o WAF
respondendo (`:79`).

---

## O cron obrigatório: régua de inadimplência

`POST /plataforma/jobs/regua`, protegido pelo header `X-Job-Token`, comparado com
`PLATAFORMA_JOB_TOKEN` (`api-gateway/routers/plataforma.py:480-493`). É chamado pelo cron
do host, não por scheduler residente — decisão explícita para não manter um beat worker
comendo RAM 24 h por dia numa VPS de 1 vCPU (`plataforma.py:486-489`).

**Sem esse cron, a régua de inadimplência não roda.** Sugestão que está no `.env.example:120-123`:

```cron
0 3 * * * curl -fsS -X POST -H "X-Job-Token: SEU_TOKEN" http://localhost:8000/plataforma/jobs/regua
```

> ⚠️ **Esse comando não funciona como está na VPS de produção.** Não há **nenhum**
> `ports:` em `docker-compose.prod.yml` — nada da stack está publicado no host
> (`docker-compose.prod.yml:48-49`), então `localhost:8000` no host não alcança o gateway.
> Do host, o caminho que existe é entrar no container (a imagem do gateway tem `curl`,
> é o que o healthcheck usa — `docker-compose.prod.yml:334`):
>
> ```cron
> 0 3 * * * docker exec erp-api-gateway-prod curl -fsS -X POST -H "X-Job-Token: SEU_TOKEN" http://localhost:8000/plataforma/jobs/regua
> ```
>
> **A CONFIRMAR:** qual das duas formas está de fato instalada no crontab da VPS, e se
> `PLATAFORMA_JOB_TOKEN` está preenchido no Coolify (vazio = a rota rejeita **toda**
> chamada com 403, `plataforma.py:492`).

---

## Índice de decisões: onde cada racional não óbvio está comentado

Quando alguém perguntar "por que está assim?", a resposta já está escrita:

| Decisão | Onde |
|---|---|
| `paths-ignore` do deploy (e por que `docker-compose.prod.yml` ficou de fora) | `.github/workflows/deploy.yml:18-47` |
| `tag` do `workflow_dispatch` = rollback sem build | `.github/workflows/deploy.yml:48-58` |
| `COOLIFY_URL` tem de ser o hostname do túnel, não o IP | `.github/workflows/deploy.yml:137-146` |
| `-A` no curl: regra de WAF por User-Agent | `.github/workflows/deploy.yml:152-157`, `uptime.yml:33-37` |
| Perder a API do Coolify no meio do deploy é esperado | `.github/workflows/deploy.yml:203-209` |
| Por que o "Container Status Changes" do Coolify não cobre a aplicação | `.github/workflows/uptime.yml:3-11` |
| Por que o cron `*/10` não significa 10 minutos | `.github/workflows/uptime.yml:14-20` |
| Sem `build:` no compose de produção (1 vCPU) | `docker-compose.prod.yml:1-7` |
| `pull_policy: always` (o deploy que subiu imagem de 15 h atrás) | `docker-compose.prod.yml:26-30` |
| `db-init`: por que os schemas são criados inline e não por arquivo montado | `docker-compose.prod.yml:130-139` |
| Backup fail-closed antes de qualquer migration | `docker-compose.prod.yml:85-102` |
| `start_interval` nos healthchecks (e os 89% de CPU do dockerd) | `docker-compose.prod.yml:335-356` |
| `cloudflared` sem `depends_on`: 502 é melhor que 530 | `docker-compose.prod.yml:560-570` |
| `external: true` no `db_data` e o que o Coolify faz com ele | `docker-compose.prod.yml:98-102`, `:573-584` |
| `resolver` no nginx: o IP do gateway muda a cada deploy | `frontend/nginx.conf:26-37` |
| Migration como subprocesso, e por que a falha é fatal | `api-gateway/database.py:47-66` |
| 503 nomeando quem caiu, em vez de 200 degradado | `api-gateway/health.py:20-36` |
| `/health` raso de propósito | `api-gateway/main.py:104-110` |
