# 🏪 Runas ERP

> ERP SaaS multi-tenant para comércio de alimentos e bebidas, em microsserviços FastAPI com frontend React.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-green)
![React](https://img.shields.io/badge/React-19-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Deploy](https://img.shields.io/badge/Deploy-Coolify%20%2B%20Cloudflare-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

Este arquivo é o panorama do sistema. Para instalar e rodar, vá direto ao
[QUICK-START.md](./QUICK-START.md).

---

## 📋 Sobre o Projeto

O **Runas** é um ERP multi-tenant: uma instalação atende várias lojas, com os
dados isolados por `empresa_id`. Um módulo de **Plataforma**, exclusivo do
`SUPER_ADMIN`, administra os tenants (criação, suspensão, plano e cobrança) sem
ler dado de negócio de nenhum deles. Na interface, o painel da plataforma e o ERP
dos lojistas são duas aplicações do mesmo bundle, separadas pelo hostname
(`frontend/src/config/host.ts`): `admin.runaserp.com.br` monta o painel
(`/plataforma` e `/plataforma/tenants`), `app.runaserp.com.br` o ERP. É separação
só de UI: a API `/api/plataforma/*` responde nos dois hosts, protegida por
`require_super_admin`.

Domínios cobertos hoje pelo backend:

- **Empresas** — cadastro dos tenants e multi-tenancy
- **Clientes** — PF/PJ, endereços e crédito fiado
- **Produtos** — catálogo, categorias, variantes, fornecedores e loja online
- **Estoque** — saldos, movimentações e ajustes
- **Vendas** — carrinho, checkout, pedidos e PDV
- **Financeiro** e **Notificações** — ver "Status do Sistema", abaixo: ainda são esqueletos

---

## 🚀 Quick Start

### Pré-requisitos

- Docker 20.10+ com Docker Compose v2
- PowerShell (o orquestrador local é o `erp.ps1`)

### Subir o ambiente local

Não existe `docker-compose.yml` na raiz: os arquivos são
`docker-compose.dev.yml`, `.prod.yml`, `.build.yml` e `.cloudflare.yml`.
O `erp.ps1` já escolhe o certo (`-f docker-compose.dev.yml`).

```powershell
.\erp.ps1 up                       # tudo
.\erp.ps1 up vendas                # gateway + frontend + vendas + dependências
.\erp.ps1 up clientes -NoFrontend  # só backend, pula o Vite
.\erp.ps1 up vendas -Cloudflare    # adiciona o overlay do Cloudflare Tunnel
```

### Acessar a aplicação

| O quê | Onde |
|-------|------|
| Frontend (Vite) | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| Swagger do Gateway | http://localhost:8000/docs |
| Liveness / Readiness | http://localhost:8000/health e `/health/ready` |

Em produção o acesso externo passa pelo Cloudflare Tunnel; o nginx do frontend
recebe `/api/*`, **remove o prefixo `/api`** e repassa ao gateway
(`frontend/nginx.conf`). Por isso as rotas do gateway não têm `/api` no código.

### Login padrão

Os valores de seed vêm do `.env` — os exemplos estão no `.env.example`:
`ADMIN_EMAIL=admin@runas.com` / `ADMIN_PASSWORD=Admin@123` para o admin da loja,
e `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` para o dono da plataforma.

📖 **Guia completo**: [QUICK-START.md](./QUICK-START.md)

---

## 🏗️ Arquitetura

8 serviços HTTP: 1 API Gateway + 7 microsserviços.

```
                        Internet
                           │
                  Cloudflare Tunnel
                           │
                  ┌────────▼────────┐
                  │    frontend     │  nginx no prod (porta 80), Vite no dev
                  │ 3000 dev/80 prod│  (3000); /api/* → gateway, sem o /api
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │   API Gateway   │  OAuth2 + JWT, RBAC, rate limit,
                  │   porta 8000    │  proxy e /health/ready
                  └────────┬────────┘
                           │  httpx (HTTP síncrono)
   ┌──────────┬──────────┬─┴────────┬──────────┬────────────┬───────────┐
┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼───────┐ ┌──▼─────────┐ ┌──▼──────┐
│clientes│ │produtos│ │estoque │ │vendas  │ │financeiro│ │notificacoes│ │empresas │
│  8001  │ │  8002  │ │  8003  │ │  8004  │ │   8005   │ │    8006    │ │  8007   │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └─────┬────┘ └──────┬─────┘ └────┬────┘
     └──────────┴──────────┴──────────┴──────────┴─────────────┴────────────┘
                                      │
                        ┌─────────────┴─────────────┐
                   ┌────▼─────┐               ┌─────▼────┐
                   │PostgreSQL│               │  Redis   │
                   │    15    │               │    7     │
                   └──────────┘               └──────────┘
```

As portas acima são as do código: o `docker-compose.dev.yml` publica
`127.0.0.1:8001..8007` para os serviços e `8000` para o gateway, e o
`docker-compose.prod.yml` usa os mesmos números nas URLs internas
(`CLIENTES_URL=http://clientes-prod:8001`, …).

### Características técnicas

- ✅ **Gateway único** — autenticação OAuth2 + JWT centralizada, RBAC e rate limit
- ✅ **Multi-tenancy** — isolamento por `empresa_id`
- ✅ **Um PostgreSQL, schemas separados** — cada serviço com seu `DATABASE_URL_*`
- ✅ **Comunicação HTTP síncrona** — chamadas serviço-a-serviço via `httpx`
- ✅ **Prova de origem interna** — `SERVICO_INTERNO_TOKEN`, o mesmo valor nos 8
  containers (`api-gateway/interno.py` e `services/*/interno.py`), e
  `PLATAFORMA_INTERNO_TOKEN`, de escopo
  menor, só no gateway e em empresas
- ✅ **Cabeçalhos da plataforma** — `X-Plataforma` identifica a chamada e
  `X-Plataforma-Token` a prova; sem o token, `X-Plataforma` sozinho é afirmação
  sem prova (`api-gateway/routers/plataforma.py`,
  `services/empresas/routers/empresas.py`)
- ✅ **Readiness profundo** — `/health/ready` no gateway verifica banco, Redis e os
  7 serviços; `/health` é só liveness
- ✅ **Redis** — blacklist de tokens (`blacklist:{token}`), idempotência do proxy
  (`api-gateway/proxy/idempotency.py`) e cache curto de inadimplência
  (`api-gateway/middleware/inadimplencia_middleware.py`). Não há sessão em
  Redis: o gateway é stateless por JWT. O rate limit é do `slowapi` sem
  `storage_uri`, ou seja, em memória do processo
  (`api-gateway/middleware/rate_limit.py`)
- ✅ **Cloudflare Tunnel** — container `cloudflared` no compose de produção
- ✅ **Deploy via Coolify** — `.github/workflows/deploy.yml`

### Sobre o RabbitMQ

O RabbitMQ **sobe** (`rabbitmq:3.12-management-alpine` no dev e no prod), o
`aio-pika==10.0.1` está pinado nos 7 `requirements.txt` e cada serviço tem um
`events/publisher.py`. Mas **nenhum código de aplicação chama `publish()`**: as
únicas ocorrências do método são a definição dentro do próprio `publisher.py`.
Na prática a comunicação entre serviços é 100% HTTP síncrono via `httpx`. Trate a
camada de eventos como infraestrutura pronta e não usada, não como arquitetura
viva.

O `celery==5.6.3` está nos `requirements.txt` dos 7 serviços pela mesma razão:
nenhum arquivo `.py` do repositório importa Celery.

📖 [docs/03-arquitetura/visao-geral.md](./docs/03-arquitetura/visao-geral.md) ·
[microsservicos.md](./docs/03-arquitetura/microsservicos.md) ·
[comunicacao.md](./docs/03-arquitetura/comunicacao.md) ·
[plataforma.md](./docs/03-arquitetura/plataforma.md)

---

## 📊 Status do Sistema

Contagem de rotas obtida do código (decoradores `@router.<verbo>` e
`@app.<verbo>`, fora de `tests/`).

### Backend

| Serviço | Rotas | Situação |
|---------|-------|----------|
| **API Gateway** | 40 | Auth, RBAC, proxy, módulo Plataforma e webhook do MP |
| **Produtos** | 43 | Produtos, categorias, variantes, fornecedores, loja online |
| **Vendas** | 43 | Carrinho, checkout, pedidos, PDV |
| **Estoque** | 20 | Saldos, movimentações e ajustes |
| **Clientes** | 18 | PF/PJ, endereços e crédito |
| **Empresas** | 10 | Tenants e multi-tenancy |
| **Financeiro** | 1 | **Esqueleto**: a única rota vive no `main.py`; `models/`, `routers/`, `services/` e `repositories/` têm apenas `__init__.py` |
| **Notificações** | 1 | **Esqueleto**: mesma situação do financeiro |

### Frontend

Páginas em `frontend/src/pages/`: Auth, Clientes, Configuracoes, Dashboard,
Estoque, Financeiro, Login, LojaOnline, LojaOnlinePublico, Perfil, Plataforma,
Produtos, Vendas.

| Módulo | Estado |
|--------|--------|
| **Estoque** | Entregue — `EstoquePage.tsx` (336 linhas), `EstoqueDetalhePage.tsx`, componentes próprios e `hooks/useEstoque.ts` |
| **Vendas/PDV** | Stub — `VendasPage.tsx` tem 47 linhas |
| **Financeiro** | Stub — `FinanceiroPage.tsx` tem 47 linhas |

📖 Detalhe do frontend:
[docs/05-frontend/frontend-current-state.md](./docs/05-frontend/frontend-current-state.md)

### Testes

88 arquivos `test_*.py` versionados (medido em 2026-10-29; contagem em `tests/README.md`). A CI (`.github/workflows/ci.yml`) roda
`pytest -c tests/pytest.ini tests/unit` e `pytest tests`, além de validar os
composes e construir as imagens de produção. São 5 workflows no total: `ci.yml`,
`deploy.yml`, `uptime.yml`, `graphify-update.yml` e `landing.yml`.

A CONFIRMAR: percentual de cobertura — não há gate de coverage nos workflows.

---

## 🛠️ Tecnologias

Versões lidas dos `requirements.txt`, do `frontend/package.json` e das imagens
dos composes.

| Categoria | Tecnologia | Versão |
|-----------|-----------|--------|
| **Linguagem** | Python (imagem `python:3.12-slim`) | 3.12 |
| **Framework** | FastAPI | 0.141.1 |
| **ORM** | SQLAlchemy (asyncio) | 2.0.54 |
| **Migrations** | Alembic | 1.20.0 |
| **Validação** | Pydantic | 2.13.5 |
| **Banco de Dados** | PostgreSQL | 15-alpine |
| **Cache / sessões** | Redis (imagem / client) | 7-alpine / 8.1.0 |
| **Mensageria** | RabbitMQ + aio-pika (presentes, **sem uso** — ver acima) | 3.12 / 10.0.1 |
| **Frontend** | React + React DOM | 19.3 |
| **Roteamento** | react-router-dom | 7.18 |
| **Build** | Vite / TypeScript | 8.3 / 5.2 |
| **UI** | Bootstrap + Sass | 5.3 / 1.104 |
| **Testes** | Pytest / Vitest | — / 5.0 |
| **Notificações** | Evolution API (WhatsApp) | — |
| **Pagamentos** | Mercado Pago (PIX) | — |
| **Deploy** | Coolify + Cloudflare Tunnel | — |

---

## 📦 Estrutura do Projeto

```
RunasERP/
├── O SISTEMA.md                  # este arquivo
├── README.md                     # documentação principal
├── QUICK-START.md                # guia rápido
├── CLAUDE.md                     # instruções para agentes
├── LICENSE                       # licença (sem extensão)
├── erp.ps1                       # orquestrador local
├── docker-compose.dev.yml        # ambiente de desenvolvimento
├── docker-compose.prod.yml       # produção (pull-only)
├── docker-compose.build.yml      # seções de build que o prod não carrega
├── docker-compose.cloudflare.yml # overlay do túnel
├── .env.example                  # variáveis de desenvolvimento
│
├── api-gateway/                  # auth, RBAC, proxy, plataforma
│   ├── auth/  middleware/  models/  proxy/  routers/  services/
│   ├── health.py  interno.py  main.py
│   └── tests/
│
├── services/                     # os 7 microsserviços
│   ├── empresas/  clientes/  produtos/  estoque/
│   └── vendas/  financeiro/  notificacoes/
│       └── cada um: alembic/  models/  repositories/  routers/
│                    schemas/  services/  events/  interno.py  main.py
│
├── frontend/                     # React 19 + Vite
│   ├── src/pages/  src/components/  src/hooks/  src/services/
│   └── nginx.conf                # /api/* → gateway, sem o prefixo
│
├── docs/                         # documentação (índice mais abaixo)
├── tests/                        # unit/  integration/  e2e/  performance/
├── scripts/                      # utilitários
└── .github/workflows/            # ci, deploy, uptime, graphify, landing
```

---

## 🔐 Autenticação e Autorização

OAuth2 + JWT no gateway, com RBAC.

### Roles

Definidas em `api-gateway/models/usuario.py` (`RoleEnum`):

| Role | Escopo |
|------|--------|
| **SUPER_ADMIN** | Dono da plataforma: administra os tenants, não lê dado de negócio deles |
| **ADMIN** | Administrador de uma loja |
| **OPERADOR** | Operação do dia a dia dentro de uma loja |

### Rotas de autenticação

De `api-gateway/routers/auth.py` (prefixo `/auth`):

```
POST /auth/login              # OAuth2 password flow
GET  /auth/me
POST /auth/refresh
POST /auth/logout
POST /auth/forgot-password
POST /auth/reset-password
POST /auth/alterar-senha
```

Clientes da loja online autenticam por rotas próprias
(`api-gateway/routers/auth_cliente.py`), separadas das dos operadores.

**Validade dos tokens** (padrões do compose, ajustáveis por variável de
ambiente): `ACCESS_TOKEN_EXPIRE_MINUTES=30` e `REFRESH_TOKEN_EXPIRE_DAYS=7`.

📖 [docs/10-api-reference/guia-autenticacao.md](./docs/10-api-reference/guia-autenticacao.md)

---

## 📝 Comandos Úteis

**Não existe Makefile neste repositório.** O orquestrador é o `erp.ps1`:

```powershell
.\erp.ps1                     # menu interativo
.\erp.ps1 up [servicos]       # subir (tudo, ou só os serviços pedidos + deps)
.\erp.ps1 down                # parar
.\erp.ps1 restart [servicos]
.\erp.ps1 ps                  # status dos containers
.\erp.ps1 health              # health check
.\erp.ps1 logs vendas         # seguir o log de um serviço (ou de todos)
.\erp.ps1 rebuild [servicos]  # reconstruir imagens
.\erp.ps1 shell erp-vendas-dev
.\erp.ps1 prune               # docker system prune -f
```

Flags: `-Cloudflare` adiciona o overlay do túnel, `-NoFrontend` pula o Vite.
Postgres, Redis e RabbitMQ nunca precisam ser listados: todo serviço os declara
em `depends_on`.

Testes:

```bash
pytest -c tests/pytest.ini tests/unit   # unitários
pytest tests                            # suíte completa
bash tests/test-mvp.sh                  # smoke test do MVP via HTTP
```

---

## 🔄 Fluxos Principais

### Venda à vista (PIX)

1. Cliente monta o carrinho
2. Checkout com PIX
3. Sistema gera o QR Code no Mercado Pago
4. Cliente paga
5. Webhook do Mercado Pago confirma o pagamento
6. Baixa no estoque

### Venda fiada

1. Cliente monta o carrinho
2. Checkout com "Fiado"
3. Sistema verifica o crédito disponível
4. Debita o crédito do cliente
5. Pedido confirmado e baixa no estoque

A CONFIRMAR: o disparo de notificação por WhatsApp ao fim dos dois fluxos — o
serviço de notificações ainda é um esqueleto sem rotas.

📖 Regras de negócio por domínio:
[docs/11-regras-negocio/README.md](./docs/11-regras-negocio/README.md)

---

## 🌐 Integrações

### Mercado Pago (PIX)

- Sandbox e produção
- Webhook para confirmação automática
- Conta da plataforma (`PLATAFORMA_MP_ACCESS_TOKEN`) separada da do lojista

📖 [docs/06-operacao/CONFIGURACAO_MERCADO_PAGO.md](./docs/06-operacao/CONFIGURACAO_MERCADO_PAGO.md) ·
[MERCADOPAGO_PIX_SANDBOX.md](./docs/06-operacao/MERCADOPAGO_PIX_SANDBOX.md)

### Evolution API (WhatsApp)

Container `evolution-api` declarado no `docker-compose.dev.yml` (porta 8080),
mas **fora do `up` padrão**: está sob `profiles: [whatsapp]`, e o comentário do
próprio compose registra que a imagem `atendai/evolution-api` saiu do Docker
Hub. Para subir: `docker compose -f docker-compose.dev.yml --profile whatsapp up
-d evolution-api` (o `erp.ps1` só expõe o profile `proxy`, do Cloudflare). Em
produção o container **não existe**: o `docker-compose.prod.yml` define as
variáveis `EVOLUTION_*` no notificações, mas anota que "evolution-api is not
deployed" e não declara o serviço.

📖 [docs/04-backend/integracao/evolution-api.md](./docs/04-backend/integracao/evolution-api.md)

---

## 📚 Documentação

### Começando

- ⚡ [QUICK-START.md](./QUICK-START.md) — instalar e rodar
- 📚 [docs/README.md](./docs/README.md) — índice completo da documentação
- 🤝 [.github/CONTRIBUTING.md](./.github/CONTRIBUTING.md) — como contribuir

### Arquitetura

- 🏗️ [docs/03-arquitetura/visao-geral.md](./docs/03-arquitetura/visao-geral.md)
- 🧩 [docs/03-arquitetura/microsservicos.md](./docs/03-arquitetura/microsservicos.md)
- 🔌 [docs/03-arquitetura/comunicacao.md](./docs/03-arquitetura/comunicacao.md)
- 🏢 [docs/03-arquitetura/plataforma.md](./docs/03-arquitetura/plataforma.md)
- 💾 [docs/03-arquitetura/persistencia-e-durabilidade.md](./docs/03-arquitetura/persistencia-e-durabilidade.md)

### API

- 🗺️ [docs/10-api-reference/mapeamento-rotas.md](./docs/10-api-reference/mapeamento-rotas.md)
- 🔑 [docs/10-api-reference/guia-autenticacao.md](./docs/10-api-reference/guia-autenticacao.md)
- 🏢 [docs/10-api-reference/plataforma-api.md](./docs/10-api-reference/plataforma-api.md)

### Operação

- 🚢 [docs/06-operacao/deploy.md](./docs/06-operacao/deploy.md)
- 📕 [docs/06-operacao/runbook-producao.md](./docs/06-operacao/runbook-producao.md)
- 🧯 [docs/06-operacao/troubleshooting.md](./docs/06-operacao/troubleshooting.md)

### Desenvolvimento

- ✅ [docs/02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md](./docs/02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md)
- 🎨 [docs/05-frontend/frontend-current-state.md](./docs/05-frontend/frontend-current-state.md)
- 🗓️ [docs/01-visao-geral/roadmap.md](./docs/01-visao-geral/roadmap.md)

---

## 🎯 Roadmap

O roadmap vive em um só lugar, mantido à parte deste panorama:
📖 [docs/01-visao-geral/roadmap.md](./docs/01-visao-geral/roadmap.md)

---

## 📄 Licença

**Propriedade de Runas** — todos os direitos reservados. Software proprietário e
confidencial; uso não autorizado é proibido.

📖 [LICENSE](./LICENSE) · [docs/07-legal/EULA-comercial.md](./docs/07-legal/EULA-comercial.md)

---

<div align="center">

**[⬆ Voltar ao topo](#-runas-erp)**

</div>
