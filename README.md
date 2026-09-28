<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="landing-page/assets/img/brand/runas-white.png">
    <img src="landing-page/assets/img/brand/runas-black.png" alt="Runas ERP" width="320">
  </picture>
</div>

#  Runas ERP

> Sistema ERP completo para comércio de alimentos e bebidas com arquitetura de microsserviços

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![React](https://img.shields.io/badge/React-19-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Status](https://img.shields.io/badge/Status-Operacional-success)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-Propriet%C3%A1ria-red)

---

> ### ⚖️ Software proprietário — não é open source
>
> Copyright © 2026 **DenebCorp**. Todos os direitos reservados.
>
> Este repositório é **privado**. Quando o acesso de leitura é concedido — avaliação
> técnica, processo seletivo, due diligence — ele autoriza **apenas ler o código**.
> Nenhum direito de usar, executar, copiar, modificar ou distribuir é concedido.
>
> Detalhes em [LICENSE](./LICENSE). Vitrine pública do produto:
> [landing-page/](./landing-page/) · [runaserp.com.br](https://www.runaserp.com.br)

---

## 🚀 Quick Start

```powershell
# 1. Clone e entre no diretório
git clone <repo-url>
cd RunasERP

# 2. Suba o stack de desenvolvimento — erp.ps1 é o entrypoint
.\erp.ps1 up                    # tudo
.\erp.ps1 up vendas             # só vendas + gateway + frontend + dependências
.\erp.ps1                       # menu interativo (Menu.bat chama o mesmo script)

# 3. Acesse
# - Frontend: http://localhost:3000
# - API Gateway: http://localhost:8000
# - Swagger: http://localhost:8000/docs   (só com DOCS_ENABLED=true — ver abaixo)
```

> O Swagger vem **desligado**: `DOCS_ENABLED` é `False` por padrão
> (`api-gateway/config.py:84`) e não é definido em nenhum `.env` nem nos composes,
> então `/docs`, `/redoc` e `/openapi.json` respondem 404 até você exportar
> `DOCS_ENABLED=true` para o gateway (`api-gateway/main.py:62-64`).

> `erp.ps1` é um wrapper fino sobre `docker compose -f docker-compose.dev.yml`.
> **Não existe `docker-compose.yml` simples** neste repositório: chamando o compose
> direto, o `-f` é sempre obrigatório —
> `docker-compose -f docker-compose.dev.yml up -d`.

**Login padrão**: `admin@runas.com` / `Admin@123`

📖 **Guia completo**: [QUICK-START.md](./QUICK-START.md)

---

## 📊 Status Atual (Agosto 2026)

### ✅ Módulos Completos

Endpoints contados por serviço (decorators de rota em `api-gateway/` e `services/<serviço>/`):

| Módulo | Serviço | Backend | Frontend | Endpoints |
|--------|---------|---------|----------|-----------|
| **API Gateway** (auth, RBAC, proxy) | `api-gateway` | 🟢 100% | - | 27 |
| **Plataforma** (plano de controle: tenants, assinaturas, auditoria) | `api-gateway` → router `/plataforma` | 🟢 100% | 🟢 100% | 13 |
| **Empresas** (multi-tenancy) | `empresas` | 🟢 100% | 🟢 100% | 9 |
| **Clientes** | `clientes` | 🟢 100% | 🟢 100% | 17 |
| **Produtos** (categorias, variantes, fornecedores, catálogo público) | `produtos` | 🟢 100% | 🟢 100% | 42 |
| **Estoque** | `estoque` | 🟢 100% | 🟢 100% | 19 |
| **Loja Online** (vitrine, carrinho, checkout, rastreio, pagamento) | `vendas` | 🟢 100% | 🟢 100% | 42 |

**Total conferido**: 129 endpoints nos cinco serviços com rotas (9 + 17 + 42 + 19 + 42)
mais os 13 do router `/plataforma` = **142**. O número do API Gateway fica fora da
soma enquanto não for reproduzido.

> **A CONFIRMAR**: o `27` do API Gateway não foi reproduzido a partir do código —
> contando decorators, `routers/` tem 19 rotas próprias de auth (`auth.py` 7 +
> `auth_admin.py` 4 + `auth_cliente.py` 8), 13 de plataforma e 29 repasses de
> `proxy.py`, mais `/health` e `/health/ready` em `main.py`. Falta definir qual
> desses conjuntos o número conta. As demais linhas foram recontadas por
> decorator de rota nos `routers/` de cada serviço.

### 🟡 Backend Pronto (Frontend Pendente)

| Módulo | Backend | Frontend | Prioridade |
|--------|---------|----------|------------|
| **Vendas/PDV** (interno) | 🟢 100% (serviço `vendas`) | 🔴 placeholder | 🔥 Alta |
| **Pedidos Online** (painel admin) | 🟢 100% (serviço `vendas`) | 🔴 placeholder | 🔥 Alta |

### 🔴 Planejado

- **Financeiro** - serviço criado, sem models/routers ainda (frontend é placeholder)
- **Notificações** - serviço criado, sem models/routers ainda
- Relatórios Avançados

---

## 🏗️ Arquitetura

Cinco recortes do mesmo sistema, do DNS até a função: **ingresso**, **stack**,
**microsserviços**, **entrega** e **um request de ponta a ponta**.

### 1. Ingresso — do DNS ao container

Não existe porta inbound aberta na VPS. Todo tráfego entra por uma conexão que o
próprio host abriu para fora (Cloudflare Tunnel), e o apex nem chega na VPS.

```
  navegador        Mercado Pago     Google / Microsoft    GitHub Actions
  admin + loja     webhook          OAuth2 callback       runner do CI
      │                │                  │                    │
      └────────────────┴─────────┬────────┴────────────────────┘
                                 │  HTTPS
  ╔══════════════════════════════▼═══════════════════════════════════════╗
  ║ CLOUDFLARE  —  DNS · TLS · WAF                                       ║
  ║                                                                      ║
  ║  runaserp.com.br + www    ──►  Pages · landing-page/                 ║
  ║                                estático, nunca toca a VPS            ║
  ║                                                                      ║
  ║  app.runaserp.com.br      ──┐                                        ║
  ║  admin.runaserp.com.br    ──┤   (admin: Cloudflare Access antes)     ║
  ║  coolify.runaserp.com.br  ──┴►  Zero Trust · ingress do túnel        ║
  ║                                 app     → frontend-prod:80           ║
  ║                                 admin   → frontend-prod:80 (o mesmo) ║
  ║                                 coolify → host.docker.internal:8000  ║
  ╚══════════════════════════════╤═══════════════════════════════════════╝
                                 ┊  QUIC — a conexão é SEMPRE iniciada de dentro
                                 ┊  (o edge nunca disca para a VPS)
  ╔══════════════════════════════▼═══════════════════════════════════════╗
  ║ VPS Hostinger  —  1 vCPU / 4 GB  —  NENHUMA porta inbound aberta     ║
  ║                                                                      ║
  ║   ┌────────────────────────┐                                         ║
  ║   │  erp-cloudflared-prod  │──── HTTP interno ───►  stack (§2)       ║
  ║   │  modo token, distroless│──── host-gateway ───►  Coolify          ║
  ║   └────────────────────────┘                          │              ║
  ║                               docker compose up -d    │              ║
  ║     stack runaserp · 15 containers  ◄─────────────────┘              ║
  ║                                                                      ║
  ╚══════════════════════════════════════════════════════════════════════╝
```

**Por que o túnel e não nginx + Let's Encrypt:** o TLS termina no edge, então o
host não precisa de certificado, de porta 80/443 nem de firewall — o que não está
escutando não pode ser varrido. E o gatilho de deploy chega *pelo túnel*: um
runner do GitHub não abre conexão confiável para o IP da Hostinger (bloco
`187.127.0.0/18`, reachability instável dependendo do egresso Azure que calhar),
mas a saída para o anycast da Cloudflare sempre funciona.

**`app` e `admin` são o mesmo container.** Quem decide se o bundle monta o ERP do
lojista ou o painel da plataforma é o hostname lido no navegador
(`frontend/src/config/host.ts`), não a imagem. A rota `admin` do túnel e o
Cloudflare Access na frente dela estão configurados fora do repositório (painel da
Cloudflare), segundo verificação de 2026-09-28 — ver
[docs/03-arquitetura/plataforma.md §5](./docs/03-arquitetura/plataforma.md).

| | Dev (sua máquina) | Produção (VPS) |
|---|---|---|
| Túnel | `cloudflared` com `cloudflared-config.yml` + credencial em `~/.cloudflared` | modo **token** (`CLOUDFLARE_TUNNEL_TOKEN`), ingress no dashboard Zero Trust |
| Origem de `app.` | `frontend-dev:3000` (Vite dev server, HMR) | `frontend-prod:80` (nginx servindo o bundle) |
| Proxy `/api` | `server.proxy` do Vite (`vite.config.ts`) | `frontend/nginx.conf` → `api-gateway-prod:8000` |
| Imagens | `build:` local, hot reload por bind mount | `pull_policy: always` do ghcr, sem `build:` |
| Ativação | `-f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy` | é o padrão |

### 2. O stack — 15 containers em uma rede bridge

```
                   ┌──────────────────────────────────────┐
                   │  cloudflared  —  o único ingress     │
                   └──────────────────┬───────────────────┘
                                      │
                   ┌──────────────────▼───────────────────┐
                   │  frontend-prod                   :80 │
                   │  nginx + SPA React 19                │
                   │  /api/ → gateway · /assets/ 1 ano    │
                   └──────────────────┬───────────────────┘
                                      │ proxy_pass  /api/  →  :8000/
                   ┌──────────────────▼───────────────────┐
                   │  api-gateway                   :8000 │
                   │  JWT HS256 · RBAC · rate limit       │
                   │  OAuth2 Google / Microsoft           │
                   │  injeta X-Empresa-Id / X-Cliente-Id  │
                   └──────────────────┬───────────────────┘
        ┌─────────┬─────────┬─────────┼─────────┬─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼         ▼         ▼
    ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
    │Empresas││Clientes││Produtos││Estoque ││ Vendas ││Financ. ││Notific.│
    │ :8007  ││ :8001  ││ :8002  ││ :8003  ││ :8004  ││ :8005~ ││ :8006~ │
    └───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
        └─────────┴─────────┴─────────┼─────────┴─────────┴─────────┘
                                      │ cada serviço só enxerga o próprio schema
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
     ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
     │  PostgreSQL 15     │  │  Redis 7           │  │  RabbitMQ 3.12     │
     │  1 schema/serviço  │  │  cache · carrinho  │  │  erp.events (topic)│
     │  volume externo    │  │  blacklist refresh │  │  durable           │
     └────────────────────┘  └────────────────────┘  └────────────────────┘
```

`~` = serviço criado, sem models/routers ainda. Nenhum container publica porta no
host: o único caminho de fora para dentro é o `cloudflared`.

```
   chamadas HTTP diretas, dentro da rede (não passam pelo gateway):
      vendas   ──►  empresas (slug → id) · clientes (cadastro) · produtos (preço)
      vendas   ──►  estoque (reserva e baixa)
      estoque  ──►  produtos (valida o produto)

   eventos — PREVISTOS, ainda NAO ligados (ver ressalva abaixo):
      vendas      ──pedido.confirmado / pedido.cancelado──►  estoque · financeiro
      estoque     ──estoque.minimo──────────────────────────►  notificacoes
      financeiro  ──cobranca.* / conta.quitada─────────────►  notificacoes
```

> ⚠️ **A mensageria está montada, não em uso.** O RabbitMQ sobe no stack e cada
> serviço traz `events/publisher.py`, que declara o exchange `erp.events` como
> topic durable e publica com `DeliveryMode.PERSISTENT`. Só que `EventPublisher` /
> `get_publisher()` **não têm nenhum call site fora do próprio módulo**, e não há
> `declare_queue`, `queue_bind` nem consumidor em lugar nenhum de `api-gateway/`,
> `services/` ou `shared/`. As routing keys existem como classes em
> `shared/events/base.py`. Hoje toda a integração entre serviços é HTTP direto
> (bloco acima); o caminho por evento é o desenho, não o comportamento.
> A própria baseline de notificacoes registra isso:
> `services/notificacoes/alembic/versions/20260919_baseline.py:16` fala do ledger
> de dedupe "quando houver um consumidor".

| Container | Imagem | Porta interna | Schema | Estado |
|---|---|---|---|---|
| `erp-cloudflared-prod` | `cloudflare/cloudflared` | — | — | 🟢 |
| `erp-frontend-prod` | `ghcr.io/…/frontend` | 80 | — | 🟢 |
| `erp-api-gateway-prod` | `ghcr.io/…/api-gateway` | 8000 | `gateway` | 🟢 27 endpoints |
| `erp-empresas-prod` | `ghcr.io/…/empresas` | 8007 | `empresas` | 🟢 9 |
| `erp-clientes-prod` | `ghcr.io/…/clientes` | 8001 | `clientes` | 🟢 17 |
| `erp-produtos-prod` | `ghcr.io/…/produtos` | 8002 | `produtos` | 🟢 42 |
| `erp-estoque-prod` | `ghcr.io/…/estoque` | 8003 | `estoque` | 🟢 19 |
| `erp-vendas-prod` | `ghcr.io/…/vendas` | 8004 | `vendas` | 🟢 42 |
| `erp-financeiro-prod` | `ghcr.io/…/financeiro` | 8005 | `financeiro` | 🚧 esqueleto |
| `erp-notificacoes-prod` | `ghcr.io/…/notificacoes` | 8006 | `notificacoes` | 🚧 esqueleto |
| `erp-db-prod` | `postgres:15-alpine` | 5432 | — | 🟢 teto de 1 CPU / 1 GB |
| `erp-db-backup-prod` | `postgres:15-alpine` | — | — | ⏱️ roda e sai — `pg_dump -Fc` antes de cada deploy |
| `erp-db-init-prod` | `postgres:15-alpine` | — | — | ⏱️ roda e sai |
| `erp-redis-prod` | `redis:7-alpine` | 6379 | — | 🟢 |
| `erp-rabbitmq-prod` | `rabbitmq:3.12-management-alpine` | 5672 / 15672 | — | 🟢 |
| `evolution-api` (WhatsApp) | Docker Hub | 8080 | `evolution` | 🔴 só no perfil de dev |

Todo serviço vive sob `cpus: 0.5 / memory: 512M`: a VPS tem 1 vCPU, e um serviço
sem teto derruba os outros oito.

**Ordem de subida** — `depends_on` por *condition*, não por nome:

```
   db  ──healthy (pg_isready)──►  db-backup  ──exit 0──►  db-init  ──exit 0──┐
   redis  ──healthy (redis-cli ping)───────────────────────────────────────► │
   rabbitmq  ──healthy (rabbitmq-diagnostics ping)─────────────────────────► │
                                                                             ▼
                                          api-gateway  +  7 microsserviços
                                          healthcheck do Docker: curl /health
                                            — liveness, raso de propósito
                                          gateway:  start_interval 5s · interval 60s
                                                    start_period 60s · timeout 10s
                                                    retries 3
                                                          │
                                                          │  api-gateway healthy
                                                          ▼
                                          frontend-prod  (wget 127.0.0.1/health)
                                                          ┊
                                                          ┊  SEM depends_on
                                                          ▼  — proposital
                                          cloudflared  (sobrevive ao deploy)
```

> `db-init` existe porque o SQLAlchemy emite `CREATE TABLE <schema>.<tabela>` e
> **nunca** `CREATE SCHEMA`; e porque o Coolify copia só o compose para a VPS, sem
> o repositório — o bind mount de `postgres/init-schemas.sql` virava um diretório
> vazio. O `cloudflared` não depende de ninguém **de propósito**: reiniciando junto
> com o frontend, o túnel desregistra e a Cloudflare devolve **530** (sem origem)
> durante toda a cadeia de healthchecks. Sem o `depends_on`, o pior caso é um 502
> de alguns segundos.

**`db-backup` — dump antes de qualquer migration.** Todo serviço roda
`alembic upgrade head` no boot e o rollback do `deploy.yml` só troca as imagens de
volta: ele nunca desfaz DDL. Por isso o `db-backup` é *fail-closed* — o `db-init`
espera ele sair com 0 e todos os serviços esperam o `db-init`, então um deploy que
não consegue fazer backup também não migra. Ele roda em **todo deploy** porque o
Coolify 4.3 para e remove todos os containers da aplicação antes do `up -d`, o que
faz o one-shot subir de novo. O dump sai como `pg_dump -Fc` em nome temporário,
é verificado com `pg_restore --list` e só então renomeado, e os **14 mais recentes**
ficam retidos. O destino é um bind mount absoluto, `/data/erp/backups` — não um
volume nomeado: o Coolify reescreve a seção `volumes` e descarta o `external:`,
mas passa bind mount intacto. Isso cobre migration ruim e escrita ruim, **não**
cobre perder a VPS; off-site continua em aberto.

**`/health` não é `/health/ready`.** O healthcheck do Docker bate em `/health`, que
é *liveness* e é raso de propósito — um blip no Redis não pode marcar o container do
gateway como morto. A prova de que o sistema está de pé é `/health/ready`
(`api-gateway/main.py` + `api-gateway/health.py`): sonda Postgres, Redis e os sete
serviços em paralelo e
devolve **503 nomeando quem caiu**. É essa rota que a sonda externa consome —
`.github/workflows/uptime.yml` bate em `https://app.runaserp.com.br/api/health/ready`
a cada 10 minutos de cron (na prática, dezenas de minutos: o GitHub estrangula
agendamento). Nenhum outro sinal de saúde olha de fora da caixa: o Docker não age
sozinho em `unhealthy` (`restart: unless-stopped` reinicia em saída de processo, não
em probe reprovado) e o Coolify só lê o healthcheck durante o deploy.

### 3. Microsserviços — roteamento, isolamento e comunicação

O gateway é o **único** ponto de entrada: nenhum serviço publica porta no host em
produção, e nenhum lê o schema de outro. A validação do carimbo de origem interna,
porém, ainda é *fail-open* — quem alcançasse a rede interna passaria (ver
*Autenticação* → `X-Servico-Interno-Token`).

```
   api-gateway  :8000
   ══════════════════

     routers/auth · auth_cliente · auth_admin
        login · refresh · logout · register · password-reset
        google · microsoft · callback
                     │
     middleware      │   structlog JSON · rate limit 10/min login e register, 5/min forgot-password
                     ▼
     _inject_context_headers          (pipeline único — sem injeção por rota)
        slug público  → SELECT id FROM empresas.empresas → X-Empresa-Id
        JWT do usuário → X-Empresa-Id     JWT do cliente → X-Cliente-Id
                     │
                     ▼
     SERVICE_URLS
          │
          ├─ /clientes ─────────────────────────►  clientes      :8001
          ├─ /produtos /categorias /variantes ──►  produtos      :8002
          │  /fornecedores /loja-online
          ├─ /estoque ──────────────────────────►  estoque       :8003
          ├─ /loja /carrinho /pagamentos ───────►  vendas        :8004
          ├─ /contas ───────────────────────────►  financeiro    :8005  ~
          ├─ /notificacoes ─────────────────────►  notificacoes  :8006  ~
          └─ /empresas ─────────────────────────►  empresas      :8007
```

**Multi-tenancy.** Rota pública de loja resolve `empresa_id` pelo slug da URL;
rota autenticada tira do JWT. O serviço a jusante nunca decide sozinho de qual
tenant é o dado — ele lê o que o gateway carimbou:

| Header | Quem injeta | Quem valida |
|---|---|---|
| `X-Empresa-Id` / `X-Cliente-Id` | `_inject_context_headers` (`api-gateway/proxy/service_proxy.py:89`) | `get_empresa_id` em `services/<nome>/utils/tenant.py` (clientes, estoque, produtos, vendas) e `exigir_tenant` em `services/empresas/routers/empresas.py:27` — *fail closed*, 400 sem ele |
| `X-Servico-Interno-Token` | `auth_interno()`, opt-in por chamada | middleware `validar_token_interno` (`services/*/interno.py`) |
| `X-Plataforma: 1` + `X-Plataforma-Token` | só o router `/plataforma` do gateway, que roda depois do `require_super_admin` | `exigir_plataforma` em `services/empresas/routers/empresas.py` |

`X-Plataforma: 1` sozinho era afirmação sem prova: quem alcançasse a porta 8007
virava plataforma e apagava tenant. O `SERVICO_INTERNO_TOKEN` não fecha isso — é o
**mesmo** nos 8 containers, e prova apenas "veio de algum deles". Daí o
`PLATAFORMA_INTERNO_TOKEN`, de escopo menor: só o gateway e o serviço `empresas` o
conhecem.

**Plano de controle — Plataforma.** Acima dos tenants existe um segundo plano, que
não é um oitavo microsserviço: é o router `/plataforma` dentro do próprio gateway
(`api-gateway/routers/plataforma.py`), registrado **antes** do proxy porque o
Starlette casa por ordem de registro e o proxy tem catch-all
(`api-gateway/main.py`).

```
   /plataforma   ── dependencies=[Depends(require_super_admin)] no router inteiro
   ══════════════
     GET    /tenants                              listar
     POST   /tenants                              provisionar (cria empresa + admin)
     PATCH  /tenants/{id}/suspender · /reativar   corta e devolve acesso
     PATCH  /tenants/{id}/plano                   plano e limites
     GET    /tenants/{id}/auditoria               trilha de escritas
     POST   /auditoria/{registro_id}/reverter     desfaz uma escrita
     GET    /tenants/{id}/exportar · /dumps       saída de dados e backups
     POST   /tenants/{id}/assinatura              gera link de assinatura (Mercado Pago)
     DELETE /tenants/{id}/assinatura              cancela

   router_publico  ── separado de propósito: estes dois não têm usuário logado
     POST   /webhook/mercadopago                  assinatura paga / vencida
     POST   /jobs/regua                           cron do host; exige X-Job-Token
```

Três peças sustentam isso fora do router:

- `AuditoriaMiddleware` no gateway grava a trilha de intenção que
  `/tenants/{id}/auditoria` lê e `/auditoria/{id}/reverter` desfaz;
- `InadimplenciaMiddleware` devolve **402** em qualquer método de escrita enquanto o
  tenant estiver em somente-leitura, com uma lista de rotas liberadas;
- a régua de vencimentos roda por **cron do host batendo em `/jobs/regua`**, não por
  scheduler residente — um beat worker comeria RAM 24 h por dia para trabalhar 200 ms
  nesta VPS de 1 vCPU.

No frontend, `pages/Plataforma/` atende duas rotas exclusivas de SUPER_ADMIN:
`/plataforma`, a visão geral (`PlataformaDashboard.tsx`), e `/plataforma/tenants`, a
lista de lojistas (`PlataformaPage.tsx` + `TenantDetalhe.tsx`: provisionar, plano,
suspender, cobrança, auditoria), ambas carregadas com `lazy()`. O painel e o ERP dos
lojistas são duas aplicações do mesmo bundle, separadas pelo hostname: se o primeiro
rótulo for `VITE_HOST_PLATAFORMA` (padrão `admin`, ou seja `admin.runaserp.com.br`),
monta o painel. `escolherPorta()` (`frontend/src/config/host.ts`) mostra a tela
"Endereço errado" ao super admin fora do host `admin` e ao lojista dentro dele —
tela, não redirect, porque o cookie de sessão é host-only. `/perfil` vale nos dois
lados; em dev (`localhost`) as duas aplicações convivem. Fora do host `admin` as rotas
`/plataforma*` nem são registradas, e o nginx do frontend devolve 404 nelas. A
separação é só do frontend:
`/api/plataforma/*` responde nos dois hosts, protegido por `require_super_admin`.

Detalhamento em [docs/03-arquitetura/plataforma.md](./docs/03-arquitetura/plataforma.md)
e [docs/10-api-reference/plataforma-api.md](./docs/10-api-reference/plataforma-api.md).

**Anatomia de um serviço** — o molde dos sete (com dois desvios reais, listados logo abaixo); copiar um é o jeito de criar o próximo:

```
   services/<nome>/
   ├── main.py             FastAPI + lifespan (init_db; jobs periódicos só em vendas)
   ├── config.py           pydantic-settings; URL dos vizinhos vem do ambiente
   ├── database.py         engine assíncrono, schema próprio
   ├── routers/            HTTP: valida entrada, delega
   ├── services/           regra de negócio
   ├── repositories/       acesso a dados — só aqui entra SQLAlchemy
   ├── models/             ORM (schema = "<nome>")
   ├── schemas/            Pydantic in/out
   ├── events/publisher.py aio_pika → exchange erp.events (ver ressalva abaixo)
   └── alembic/            migrations próprias, por serviço
```

> Dois desvios reais do molde: `jobs/` e `scripts/` existem **só** em
> `services/vendas/`; `utils/` existe em clientes, empresas, estoque, produtos e
> vendas, não em financeiro nem em notificacoes. O resto (`main.py`, `config.py`,
> `database.py`, `interno.py`, `routers/`, `services/`, `repositories/`, `models/`,
> `schemas/`, `events/publisher.py`, `alembic/`) está nos sete.

Routing keys **previstas** — declaradas em `shared/events/base.py`, nenhuma
publicada ou consumida em código hoje (ver a ressalva da seção 2):

| Routing key | Publicaria | Consumiria |
|---|---|---|
| `pedido.confirmado` / `pedido.cancelado` | vendas | estoque, financeiro, notificacoes |
| `estoque.minimo` | estoque | notificacoes |
| `cobranca.lembrete` / `cobranca.vencida` / `conta.quitada` | financeiro | notificacoes |

**Jobs do serviço de vendas** — os dois primeiros rodam *dentro* do container, como
`asyncio.Task` do lifespan; os demais são scripts sob demanda:

| Job | Intervalo | O que faz |
|---|---|---|
| `verificar_pagamentos_pendentes` | 60 s (in-process) | cancela pagamento online expirado, devolve estoque |
| `reconciliar_estoque_vendas` | 120 s (in-process) | retenta baixa de estoque indeterminada em venda **paga** |
| `limpar_reservas` | 1 min | expira reserva temporária de carrinho/checkout |
| `verificar_timeouts_separacao` | 1 h | alerta em 12 h e 24 h, auto-cancela em 48 h |
| `limpar_carrinhos_abandonados` | diário | remove carrinho Redis parado há mais de 7 dias |

### 4. Entrega — do push ao container rodando

```
   feat/*  ──►  Developer  ──PR──►  ci.yml  ──merge──►  main
                                    compose · 9 imagens          │
                                    vitest · pytest              │
        ┌───────────────────────┬────────────────────────────────┤
        ▼                       ▼                                ▼
   deploy.yml              landing.yml                   graphify-update.yml
   ignora *.md, docs/,     só landing-page/              regrava o grafo
   landing-page/, .github/ wrangler pages deploy         (GITHUB_TOKEN não
        │                       │                         dispara workflow)
        │                       └──►  Cloudflare Pages
        │
        ├─ build + push ──►  ghcr.io/…/<serviço>:<sha>   e   :latest
        │
        └─ POST /api/v1/deploy ──(pelo túnel · UA não-curl · retry 5×)──►  Coolify
                                                                             │
              docker compose -f docker-compose.prod.yml up -d --wait  ◄──────┤
              pull_policy: always  (:latest é tag móvel)                     │
                                                                             │
              poll /api/v1/deployments/{uuid}  ──►  finished | failed  ◄──────┘
```

| Arquivo | Lido por | Papel |
|---|---|---|
| `docker-compose.dev.yml` | sua máquina | dev local: `build:` do fonte, hot reload, portas no host |
| `docker-compose.cloudflare.yml` | sua máquina | overlay: URLs públicas + túnel (`--profile proxy`) |
| `docker-compose.prod.yml` | **Coolify** | runtime de produção — **pull only**, zero `build:` |
| `docker-compose.build.yml` | GitHub Actions | overlay sobre o prod: devolve os `build:` para a CI |

> A VPS de 1 vCPU não constrói nove imagens sem matar o stack em execução: o runner
> constrói, o host só puxa. `pull_policy: always` é obrigatório porque `:latest` é
> tag móvel e o padrão do Compose (`missing`) mantém a cópia velha para sempre.
> Rollback é `TAG=<sha>` — a CI publica todo commit com as duas tags.
>
> O `paths-ignore` completo do `deploy.yml` tem cinco entradas, uma a mais que
> o diagrama comporta: `landing-page/**`, `docs/**`, `**.md`, `.github/**` e
> `scripts/**`. O do `ci.yml` são as três primeiras.

### 5. Um request de ponta a ponta — checkout PIX na loja online

```
    1  navegador ──GET /loja/{slug}──► edge ─► túnel ─► nginx ─► SPA React
    2  navegador ──POST /api/carrinho/itens──► nginx ──proxy_pass──► gateway
    3  gateway    resolve slug → empresa_id, injeta X-Empresa-Id ──► vendas
    4  vendas ──► Redis: grava carrinho + reserva temporária
    5  vendas ──HTTP──► estoque: valida saldo disponível
    6  navegador ──POST /api/pagamentos (PIX)──► gateway ──► vendas
    7  vendas ──► Mercado Pago: cria preference com
                  notification_url = {API_BASE_URL}/loja/{slug}/webhook/mercadopago
    8  Mercado Pago ──QR Code PIX──► navegador

   ═══════════════════  cliente paga — minutos depois  ═══════════════════

    9  Mercado Pago ──POST webhook──► edge ─► túnel ─► nginx ─► gateway ─► vendas
   10  vendas     idempotente por payment id ──► baixa definitiva no estoque
   11  (previsto, ainda nao ligado) vendas publicaria pedido.confirmado
        no exchange erp.events — nenhum publisher e chamado hoje

        └─ baixa indeterminada NUNCA cancela venda paga: fica marcada e o job
           reconciliar_estoque_vendas retenta a cada 120 s
```

**Autenticação.** JWT HS256, `access_token` de 30 min, `refresh_token` de 7 dias em
cookie HttpOnly com blacklist no Redis. O `SECRET_KEY` é compartilhado: o gateway
assina e cada serviço valida por conta própria. RBAC em três papéis —
SUPER_ADMIN, ADMIN, OPERADOR (`api-gateway/models/usuario.py`).

---

## 📚 Documentação Essencial

### 🎯 Para Começar
- 📖 [O SISTEMA.md](./O%20SISTEMA.md) - Visão geral completa
- ⚡ [QUICK-START.md](./QUICK-START.md) - Setup em 5 minutos

### 💻 Para Desenvolver
- ✅ [CHECKLIST_DESENVOLVIMENTO.md](./docs/02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md) - Checklist completo
- 🎨 [FRONTEND_IMPLEMENTACAO.md](./FRONTEND_IMPLEMENTACAO.md) - Guia de implementação frontend
- 📋 [docs/02-desenvolvimento/](./docs/02-desenvolvimento/) - Guias técnicos
- 🔧 [CLAUDE.md](./CLAUDE.md) - Convenções

### 📁 Documentação Completa
- 📂 [docs/06-operacao/](./docs/06-operacao/) - Runbooks de operação
- 📂 [docs/07-legal/](./docs/07-legal/) - Licenciamento e EULA
- 📂 [docs/03-arquitetura/](./docs/03-arquitetura/) - Arquitetura do sistema
- 📂 [docs/04-backend/](./docs/04-backend/) - Backend e APIs
- 📂 [docs/05-frontend/](./docs/05-frontend/) - Frontend React
- 📂 [docs/10-api-reference/](./docs/10-api-reference/) - Referência completa de APIs
- 📂 [docs/11-regras-negocio/](./docs/11-regras-negocio/) - Regras de negócio
- 🌐 [landing-page/](./landing-page/) - Site institucional do produto (HTML/CSS/JS estático)

---

## 🛠️ Tecnologias

### Backend
- **FastAPI** 0.141 - Framework web moderno
- **SQLAlchemy** 2.0 - ORM assíncrono
- **PostgreSQL** 15 - Banco de dados
- **Redis** 7 - Cache e sessões
- **RabbitMQ** 3.12 - Mensageria

### Frontend
- **React** 19 - UI library
- **TypeScript** 5 - Type safety
- **Vite** 8 - Build e dev server
- **React Bootstrap** 2 + **Bootstrap** 5 - Componentes UI
- **TanStack Query** 5 - Data fetching e cache
- **Axios** - Cliente HTTP
- **React Hook Form** + **Zod** - Formulários e validação
- **React Router** 7 - Navegação

### DevOps
- **Docker** + **Docker Compose** - Containerização
- **GitHub Actions** - CI (`ci.yml`), deploy (`deploy.yml`), landing (`landing.yml`), sonda de uptime (`uptime.yml`)
- **GHCR** (`ghcr.io`) - registry das imagens, tag `:<sha>` e `:latest`
- **Coolify** 4.3 - orquestra o `docker-compose.prod.yml` na VPS; o deploy é disparado por `POST /api/v1/deploy`
- **Cloudflare** - Tunnel (único ingress da VPS), DNS/TLS/WAF e Pages (landing page)
- **Alembic** - Migrations, uma por serviço
- **pytest** - Testes de backend | **Vitest** - Testes de frontend
- **Git** - Versionamento

---

## 🎯 Próximas Implementações

Para um roadmap detalhado, consulte: [docs/01-visao-geral/roadmap.md](./docs/01-visao-geral/roadmap.md)

### Alta Prioridade
- **PDV (Vendas)** - Frontend para ponto de venda
- **Pedidos Online** - Painel admin para pedidos da loja online
- **Relatórios** - Dashboards e relatórios

### Médio Prazo
- **Financeiro** - Gestão financeira completa
- **Notificações** - Sistema de notificações WhatsApp
- **Analytics** - Métricas e análises avançadas

📋 **Guia de desenvolvimento**: [CHECKLIST_DESENVOLVIMENTO.md](./docs/02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md)

---

## 📝 Comandos Úteis

### `erp.ps1` — o entrypoint

Wrapper fino sobre `docker compose -f docker-compose.dev.yml`. É por aqui que se
sobe o ambiente; `Menu.bat` só chama o mesmo script sem argumento (menu interativo).
Postgres, Redis e RabbitMQ nunca são listados: todo serviço os declara em
`depends_on`, então o Compose os sobe sozinho.

```powershell
.\erp.ps1                          # menu interativo
.\erp.ps1 up                       # tudo
.\erp.ps1 up vendas                # gateway + frontend + vendas + dependências
.\erp.ps1 up vendas,estoque        # vários de uma vez
.\erp.ps1 up clientes -NoFrontend  # só backend, pula o Vite (o mais pesado)
.\erp.ps1 up vendas -Cloudflare    # soma o overlay do Cloudflare Tunnel
.\erp.ps1 logs vendas              # segue um serviço (ou todos, se omitido)
.\erp.ps1 down | restart | ps | health | rebuild | prune
.\erp.ps1 shell erp-vendas-dev
```

### Compose cru

Só quando precisar de algo que o `erp.ps1` não expõe. O `-f` é sempre obrigatório —
**não existe `docker-compose.yml` simples** neste repositório.

```bash
docker-compose -f docker-compose.dev.yml up -d                # Subir todos os serviços
docker-compose -f docker-compose.dev.yml logs -f [serviço]    # Ver logs
docker-compose -f docker-compose.dev.yml restart [serviço]    # Reiniciar serviço
docker-compose -f docker-compose.dev.yml down                 # Parar tudo

# Cloudflare Tunnel (acesso externo)
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
```

### Frontend e backend

```bash
# Frontend
cd frontend
npm run dev                       # Rodar em desenvolvimento
npm run build                     # Build de produção
npm run lint
npm run test -- --run             # Vitest, o mesmo comando que a CI roda

# Backend (rodam dentro do container — cada serviço tem seu próprio Alembic)
docker exec -it erp-[serviço]-dev alembic upgrade head    # Rodar migrations
docker-compose -f docker-compose.dev.yml exec [serviço] python seed.py   # Popular dados

# Testes de unidade — o mesmo comando do gate da CI (.github/workflows/ci.yml)
pip install -r tests/requirements.txt
pytest -c tests/pytest.ini tests/unit
```

> `pytest` sozinho na raiz **não** é o gate: vários arquivos direto em `tests/` são
> scripts manuais que batem num serviço vivo em localhost e falham sem o stack no ar.
> A CI escopa por caminho (`tests/unit`) por isso mesmo, e roda os testes de cada
> serviço numa *leg* separada, a partir do diretório do próprio serviço — eles
> importam achatado (`from main import app`), então dois no mesmo processo brigam
> por quem fica primeiro no `sys.path`.

---

## 🔐 Autenticação

O sistema utiliza **OAuth2 com JWT** e **RBAC**. Os papéis são três — o enum
`RoleEnum` em `api-gateway/models/usuario.py`:

| Role | Escopo | Guard que o exige |
|------|--------|-------------------|
| **SUPER_ADMIN** | plano de controle da plataforma; `empresa_id` nulo, sem tenant | `require_super_admin` — todo o router `/plataforma` |
| **ADMIN** | administração do próprio tenant, incluindo gestão de usuários | `require_admin` |
| **OPERADOR** | operação dentro do tenant | `require_admin_or_operador` |

### Prova de origem interna (`X-Servico-Interno-Token`)

Os serviços tratam `X-Empresa-Id` e `X-Cliente-Id` como identidade. Quem alcançasse
a porta de um serviço direto escolhia o tenant que quisesse. O carimbo que fecha
isso é um segredo compartilhado, o **mesmo nos 8 containers**
(`SERVICO_INTERNO_TOKEN`), enviado no header `X-Servico-Interno-Token`:

- **enviar** é opt-in, uma chamada por vez, via `auth_interno()` — estes serviços
  também falam com Mercado Pago, viacep e Evolution API, e mandar o segredo interno
  para terceiro é vazar credencial;
- **validar** é o middleware `validar_token_interno` de cada serviço
  (`services/<nome>/interno.py`), que isenta apenas `/health` — o healthcheck do
  Docker bate em `localhost:PORTA/health` sem passar pelo gateway;
- cobertura em `tests/unit/test_auth_servico_a_servico.py`.

> ⚠️ **Hoje a validação é FAIL-OPEN**: se o segredo estiver faltando em qualquer um
> dos dois lados, o middleware apenas registra `servico_interno.ausente` e deixa
> passar. É deliberado enquanto o deploy não for blue-green — o stack velho cai antes
> do novo subir, então existe uma janela em que o chamador já carimba e o validador
> ainda não tem a env (ou o contrário), e fechar nessa janela seria 403 no checkout,
> na baixa de estoque e no job de reconciliação. Fechar é trocar o `log.warning` pelo
> `return` do ramo seguinte — uma linha — depois de medir `servico_interno.ausente`
> zerado em produção.

O token é estático, não um claim assinado: responde "veio de dentro" e nada mais —
não diz **qual** serviço chamou nem expira. Para as rotas de plataforma, que apagam
tenant, isso não basta; por isso elas exigem também o `X-Plataforma-Token`, de
escopo menor (ver *Multi-tenancy*).

---

## 🤝 Contribuindo

```bash
# 1. Crie uma branch
git checkout -b feat/nova-feature

# 2. Desenvolva e commit (seguindo Conventional Commits)
git commit -m "feat(modulo): adiciona nova funcionalidade"

# 3. Push e PR
git push origin feat/nova-feature
```

**Convenções**: Veja [CHECKLIST_DESENVOLVIMENTO.md](./docs/02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md) e [CLAUDE.md](./CLAUDE.md)

---

## 📄 Licença

**Copyright © 2026 DenebCorp — todos os direitos reservados.** Software proprietário.

| Documento | Aplica-se a | O que concede |
|-----------|-------------|---------------|
| [LICENSE](./LICENSE) | quem tem acesso de leitura ao repositório | leitura e avaliação técnica apenas — **nenhum direito de uso** |
| [EULA comercial](./docs/07-legal/EULA-comercial.md) | clientes sob contrato | uso do sistema nos termos do contrato |

Para licenciar ou pedir permissão: **legal@runas.com**

Dependências de terceiros permanecem sob suas licenças originais.

---

## 📞 Contato

- **Email**: dev@runas.com.br
- **Documentação**: [docs/](./docs/)

---

<div align="center">

**Versão 1.0.0** | Agosto 2026

Desenvolvido por **Equipe DenebCorp**

[⬆ Voltar ao topo](#-runas-erp)

</div>
