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

```bash
# 1. Clone e entre no diretório
git clone <repo-url>
cd RunasERP

# 2. Suba todos os serviços (não existe docker-compose.yml simples — sempre use -f)
docker-compose -f docker-compose.dev.yml up -d

# 3. Acesse
# - Frontend: http://localhost:3000
# - API Gateway: http://localhost:8000
# - Swagger: http://localhost:8000/docs
```

**Login padrão**: `admin@runas.com` / `Admin@123`

📖 **Guia completo**: [QUICK-START.md](./QUICK-START.md)

---

## 📊 Status Atual (Agosto 2026)

### ✅ Módulos Completos

Endpoints contados por serviço (decorators de rota em `api-gateway/` e `services/<serviço>/`):

| Módulo | Serviço | Backend | Frontend | Endpoints |
|--------|---------|---------|----------|-----------|
| **API Gateway** (auth, RBAC, proxy) | `api-gateway` | 🟢 100% | - | 27 |
| **Empresas** (multi-tenancy) | `empresas` | 🟢 100% | 🟢 100% | 8 |
| **Clientes** | `clientes` | 🟢 100% | 🟢 100% | 17 |
| **Produtos** (categorias, variantes, fornecedores, catálogo público) | `produtos` | 🟢 100% | 🟢 100% | 42 |
| **Estoque** | `estoque` | 🟢 100% | 🟢 100% | 19 |
| **Loja Online** (vitrine, carrinho, checkout, rastreio, pagamento) | `vendas` | 🟢 100% | 🟢 100% | 40 |

**Total operacional**: 153 endpoints | ~27.000 linhas Python + ~14.000 linhas TypeScript

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
  ║  coolify.runaserp.com.br  ──┴►  Zero Trust · ingress do túnel        ║
  ║                                 app     → frontend-prod:80           ║
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
  ║     stack runaserp · 14 containers  ◄─────────────────┘              ║
  ║                                                                      ║
  ╚══════════════════════════════════════════════════════════════════════╝
```

**Por que o túnel e não nginx + Let's Encrypt:** o TLS termina no edge, então o
host não precisa de certificado, de porta 80/443 nem de firewall — o que não está
escutando não pode ser varrido. E o gatilho de deploy chega *pelo túnel*: um
runner do GitHub não abre conexão confiável para o IP da Hostinger (bloco
`187.127.0.0/18`, reachability instável dependendo do egresso Azure que calhar),
mas a saída para o anycast da Cloudflare sempre funciona.

| | Dev (sua máquina) | Produção (VPS) |
|---|---|---|
| Túnel | `cloudflared` com `cloudflared-config.yml` + credencial em `~/.cloudflared` | modo **token** (`CLOUDFLARE_TUNNEL_TOKEN`), ingress no dashboard Zero Trust |
| Origem de `app.` | `frontend-dev:3000` (Vite dev server, HMR) | `frontend-prod:80` (nginx servindo o bundle) |
| Proxy `/api` | `server.proxy` do Vite (`vite.config.ts`) | `frontend/nginx.conf` → `api-gateway-prod:8000` |
| Imagens | `build:` local, hot reload por bind mount | `pull_policy: always` do ghcr, sem `build:` |
| Ativação | `-f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy` | é o padrão |

### 2. O stack — 14 containers em uma rede bridge

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

   eventos — RabbitMQ, exchange erp.events (topic, durable, persistente):
      vendas      ──pedido.confirmado / pedido.cancelado──►  estoque · financeiro
      estoque     ──estoque.minimo──────────────────────────►  notificacoes
      financeiro  ──cobranca.* / conta.quitada─────────────►  notificacoes
```

| Container | Imagem | Porta interna | Schema | Estado |
|---|---|---|---|---|
| `erp-cloudflared-prod` | `cloudflare/cloudflared` | — | — | 🟢 |
| `erp-frontend-prod` | `ghcr.io/…/frontend` | 80 | — | 🟢 |
| `erp-api-gateway-prod` | `ghcr.io/…/api-gateway` | 8000 | `gateway` | 🟢 27 endpoints |
| `erp-empresas-prod` | `ghcr.io/…/empresas` | 8007 | `empresas` | 🟢 8 |
| `erp-clientes-prod` | `ghcr.io/…/clientes` | 8001 | `clientes` | 🟢 17 |
| `erp-produtos-prod` | `ghcr.io/…/produtos` | 8002 | `produtos` | 🟢 42 |
| `erp-estoque-prod` | `ghcr.io/…/estoque` | 8003 | `estoque` | 🟢 19 |
| `erp-vendas-prod` | `ghcr.io/…/vendas` | 8004 | `vendas` | 🟢 40 |
| `erp-financeiro-prod` | `ghcr.io/…/financeiro` | 8005 | `financeiro` | 🚧 esqueleto |
| `erp-notificacoes-prod` | `ghcr.io/…/notificacoes` | 8006 | `notificacoes` | 🚧 esqueleto |
| `erp-db-prod` | `postgres:15-alpine` | 5432 | — | 🟢 teto de 1 CPU / 1 GB |
| `erp-db-init-prod` | `postgres:15-alpine` | — | — | ⏱️ roda e sai |
| `erp-redis-prod` | `redis:7-alpine` | 6379 | — | 🟢 |
| `erp-rabbitmq-prod` | `rabbitmq:3.12-management-alpine` | 5672 / 15672 | — | 🟢 |
| `evolution-api` (WhatsApp) | Docker Hub | 8080 | `evolution` | 🔴 só no perfil de dev |

Todo serviço vive sob `cpus: 0.5 / memory: 512M`: a VPS tem 1 vCPU, e um serviço
sem teto derruba os outros oito.

**Ordem de subida** — `depends_on` por *condition*, não por nome:

```
   db  ──healthy (pg_isready)──►  db-init  ──completed successfully──┐
   redis  ──healthy (redis-cli ping)──────────────────────────────►  │
   rabbitmq  ──healthy (rabbitmq-diagnostics ping)────────────────►  │
                                                                     ▼
                                          api-gateway  +  7 microsserviços
                                          healthcheck: curl /health
                                          gateway: interval 5s, start_period 60s
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

### 3. Microsserviços — roteamento, isolamento e comunicação

O gateway é o **único** ponto de entrada: nenhum serviço aceita request direto na
própria porta, e nenhum lê o schema de outro.

```
   api-gateway  :8000
   ══════════════════

     routers/auth · auth_cliente · auth_admin
        login · refresh · logout · register · password-reset
        google · microsoft · callback
                     │
     middleware      │   structlog JSON · rate limit 5/min login, 10/min register
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
rota autenticada tira do JWT. O serviço a jusante só enxerga `X-Empresa-Id` —
nunca decide sozinho de qual tenant é o dado.

**Anatomia de um serviço** — idêntica nos sete; copiar um é o jeito de criar o próximo:

```
   services/<nome>/
   ├── main.py             FastAPI + lifespan (init_db, jobs periódicos)
   ├── config.py           pydantic-settings; URL dos vizinhos vem do ambiente
   ├── database.py         engine assíncrono, schema próprio
   ├── routers/            HTTP: valida entrada, delega
   ├── services/           regra de negócio
   ├── repositories/       acesso a dados — só aqui entra SQLAlchemy
   ├── models/             ORM (schema = "<nome>")
   ├── schemas/            Pydantic in/out
   ├── events/publisher.py aio_pika → exchange erp.events
   ├── jobs/               rotinas periódicas
   └── alembic/            migrations próprias, por serviço
```

| Routing key | Publica | Consome |
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
   11  vendas ──publica pedido.confirmado──► RabbitMQ (erp.events)

        └─ baixa indeterminada NUNCA cancela venda paga: fica marcada e o job
           reconciliar_estoque_vendas retenta a cada 120 s
```

**Autenticação.** JWT HS256, `access_token` de 30 min, `refresh_token` de 7 dias em
cookie HttpOnly com blacklist no Redis. O `SECRET_KEY` é compartilhado: o gateway
assina e cada serviço valida por conta própria. RBAC em quatro papéis — ADMIN,
GERENTE, VENDEDOR, OPERADOR.

---

## 📚 Documentação Essencial

### 🎯 Para Começar
- 📖 [O SISTEMA.md](./O%20SISTEMA.md) - Visão geral completa
- ⚡ [QUICK-START.md](./QUICK-START.md) - Setup em 5 minutos

### 💻 Para Desenvolver
- ✅ [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md) - Checklist completo
- 🎨 [FRONTEND_IMPLEMENTACAO.md](./FRONTEND_IMPLEMENTACAO.md) - Guia de implementação frontend
- ⚡ [GUIA_PERFORMANCE.md](./GUIA_PERFORMANCE.md) - Otimização e performance
- 📋 [docs/02-desenvolvimento/](./docs/02-desenvolvimento/) - Guias técnicos
- 🔧 [CLAUDE.md](./CLAUDE.md) - Convenções

### 📁 Documentação Completa
- 📂 [docs/01-principal/](./docs/01-principal/) - Documentação principal
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
- **Alembic** - Migrations
- **Vitest** - Testes de frontend
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

📋 **Guia de desenvolvimento**: [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md)

---

## 📝 Comandos Úteis

```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml up -d                # Subir todos os serviços
docker-compose -f docker-compose.dev.yml logs -f [serviço]    # Ver logs
docker-compose -f docker-compose.dev.yml restart [serviço]    # Reiniciar serviço
docker-compose -f docker-compose.dev.yml down                 # Parar tudo

# Cloudflare Tunnel (acesso externo)
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# Frontend
cd frontend
npm run dev                       # Rodar em desenvolvimento
npm run build                     # Build de produção

# Backend (rodam dentro do container — cada serviço tem seu próprio Alembic)
docker exec -it erp-[serviço]-dev alembic upgrade head    # Rodar migrations
docker-compose -f docker-compose.dev.yml exec [serviço] python seed.py   # Popular dados
pytest                            # Testes de integração (da raiz do repo, serviços no ar)
```

---

## 🔐 Autenticação

O sistema utiliza **OAuth2 com JWT** e **RBAC**:

| Role | Permissões |
|------|-----------|
| **ADMIN** | Acesso total |
| **GERENTE** | Gestão de produtos, clientes, vendas |
| **VENDEDOR** | Criar vendas, consultar dados |
| **OPERADOR** | Apenas leitura |

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

**Convenções**: Veja [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md) e [CLAUDE.md](./CLAUDE.md)

---

## 📄 Licença

**Copyright © 2026 DenebCorp — todos os direitos reservados.** Software proprietário.

| Documento | Aplica-se a | O que concede |
|-----------|-------------|---------------|
| [LICENSE](./LICENSE) | quem tem acesso de leitura ao repositório | leitura e avaliação técnica apenas — **nenhum direito de uso** |
| [EULA comercial](./docs/01-principal/EULA-comercial.md) | clientes sob contrato | uso do sistema nos termos do contrato |

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
