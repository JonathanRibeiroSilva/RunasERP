# Visão Geral da Arquitetura - Runas

> **Contexto geral, stack tecnológica e estrutura de microsserviços**

Verificado contra o código em 2026-09-26. Onde o código não permite afirmar, o texto diz
`A CONFIRMAR`. Detalhe por serviço: [`microsservicos.md`](microsservicos.md). Como os
serviços conversam: [`comunicacao.md`](comunicacao.md).

---

## Contexto Geral

**Runas** é um ERP SaaS multi-tenant para comércio de alimentos e bebidas. Cada lojista
é uma empresa (tenant) do serviço `empresas`; os dados dos demais serviços carregam
`empresa_id` e o gateway injeta o tenant do usuário autenticado no header `X-Empresa-Id`.

---

## Stack

| Camada | Tecnologia | Versão (fonte) |
|---|---|---|
| Linguagem | Python | 3.12 (`FROM python:3.12-slim` nos Dockerfiles) |
| Framework | FastAPI | 0.141.1, fixado em `requirements.txt` |
| ORM | SQLAlchemy async + asyncpg | 2.0.54 / 0.31.0 |
| Migrations | Alembic | 1.20.0 |
| Banco | PostgreSQL | 15 (`postgres:15-alpine`) |
| Autenticação | JWT HS256 (python-jose) + senha bcrypt (passlib) | 3.5.0 / 1.7.4 — só no gateway |
| Cache / estado | Redis | 7 (`redis:7-alpine`) |
| Mensageria | RabbitMQ + aio-pika | `rabbitmq:3.12-management-alpine`; **sobe no compose, mas nenhum código publica ou consome** (ver `comunicacao.md`) |
| Fila de tarefas | Celery | `celery==5.6.3` está nos requirements dos serviços, **sem uso no código** |
| WhatsApp | Evolution API | configurada por empresa no serviço vendas (`configuracoes_integracao`); o container `evolution-api` existe só no compose de dev |
| Pagamentos | Mercado Pago | preferência de checkout + webhook no serviço vendas |
| Containerização | Docker + Docker Compose | dev, prod, cloudflare e build (4 arquivos na raiz) |
| Testes | Pytest + pytest-asyncio + pytest-cov | 9.1.1 / 1.4.0 / 7.1.0 (`tests/requirements.txt`) |
| Validação | Pydantic | 2.13.5 |
| Frontend | React + TypeScript + Vite | react ^19.3.0, vite ^8.3.1 (`frontend/package.json`) |

---

## Arquitetura de Microsserviços

O sistema possui **7 microsserviços** + **1 API Gateway**, totalizando **8 serviços de
aplicação**, mais o frontend. Há **um único PostgreSQL com um schema por serviço**
(`gateway`, `empresas`, `clientes`, `produtos`, `estoque`, `vendas`, `financeiro`,
`notificacoes` — `postgres/init-schemas.sql`). O isolamento entre tenants é por coluna
`empresa_id`, não por schema.

```
RunasERP/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.cloudflare.yml      # overlay: URLs públicas + Cloudflare Tunnel
├── docker-compose.build.yml
├── .env.example
├── README.md
├── QUICK-START.md
├── FRONTEND_IMPLEMENTACAO.md
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                        # FastAPI, middlewares e routers
│   ├── config.py  database.py  health.py  interno.py  seed.py
│   ├── alembic/
│   ├── auth/
│   │   ├── jwt.py                     # criação/validação de tokens
│   │   ├── oauth2.py                  # get_current_user (bearer/cookie) e RBAC
│   │   └── redis_client.py            # cliente Redis (refresh tokens)
│   ├── middleware/
│   │   ├── rate_limit.py
│   │   ├── logging_middleware.py
│   │   ├── auditoria_middleware.py
│   │   └── inadimplencia_middleware.py
│   ├── models/
│   │   ├── usuario.py
│   │   └── cliente_auth.py            # credenciais de compradores
│   ├── proxy/
│   │   ├── service_proxy.py           # tabela de prefixos -> serviço
│   │   └── idempotency.py
│   ├── repositories/  schemas/  services/  tests/
│   └── routers/
│       ├── auth.py
│       ├── auth_admin.py
│       ├── auth_cliente.py
│       ├── plataforma.py
│       └── proxy.py
├── services/
│   ├── empresas/                      # multi-tenancy (porta 8007)
│   ├── clientes/                      # porta 8001
│   ├── produtos/                      # porta 8002
│   ├── estoque/                       # porta 8003
│   ├── vendas/                        # porta 8004
│   ├── financeiro/                    # porta 8005 (esqueleto)
│   └── notificacoes/                  # porta 8006 (esqueleto)
├── frontend/                          # React + TypeScript + Vite
│   ├── src/
│   ├── public/
│   └── Dockerfile
├── shared/
│   ├── events/base.py
│   ├── exceptions.py
│   └── pagination.py
├── postgres/init-schemas.sql
├── scripts/
├── tests/
└── docs/
```

### Estrutura interna de um serviço

Padrão seguido pelos 7 serviços (com variações: por exemplo `vendas` tem `jobs/`,
`utils/` e `redis_client.py`; `empresas` tem `utils/` e `exceptions.py`):

```
services/{servico}/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── alembic/versions/
├── main.py                            # FastAPI app + routers
├── config.py                          # settings (pydantic-settings)
├── database.py                        # engine async + sessão
├── interno.py                         # valida X-Servico-Interno-Token
├── seed.py
├── models/                            # SQLAlchemy
├── schemas/                           # Pydantic
├── repositories/                      # acesso a dados
├── services/                          # regras de negócio
├── routers/                           # endpoints FastAPI
├── events/publisher.py                # publisher RabbitMQ (não chamado por ninguém)
└── tests/
```

`financeiro` e `notificacoes` têm essa estrutura, mas `models/`, `routers/`, `schemas/`,
`repositories/` e `services/` contêm apenas `__init__.py` vazio.

---

## Visão Geral dos Serviços

Portas: `services/*/Dockerfile` (`EXPOSE` e `CMD uvicorn --port`) e `api-gateway/Dockerfile`;
o `docker-compose.dev.yml` usa as mesmas nos `command:`.

| # | Serviço | Porta | Estado |
|---|---|---|---|
| 1 | api-gateway | 8000 | implementado |
| 2 | clientes | 8001 | implementado |
| 3 | produtos | 8002 | implementado |
| 4 | estoque | 8003 | implementado |
| 5 | vendas | 8004 | implementado |
| 6 | financeiro | 8005 | **esqueleto**: só `/health` |
| 7 | notificacoes | 8006 | **esqueleto**: só `/health` |
| 8 | empresas | 8007 | implementado |

### API Gateway (porta 8000)
- Único ponto de entrada externo; roteia por prefixo de path para os serviços
- Autenticação JWT (usuários admin/operador) e login de compradores, inclusive OAuth Google/Microsoft
- RBAC e injeção de `X-Empresa-Id` / `X-Cliente-Id`
- Rate limiting por IP (300/min por padrão), idempotência via `Idempotency-Key`
- Log estruturado, auditoria de escritas e bloqueio de escrita de tenant inadimplente
- Rotas de plataforma (`/plataforma/*`): provisionar, suspender e cobrar tenants

### Empresas (porta 8007)
- Multi-tenancy: cadastro de empresas/tenants, com slug e CNPJ únicos
- Configuração de catálogo público, tema e plano/limites por empresa

### Clientes (porta 8001)
- Clientes e endereços, crédito e limite, bloqueio/desbloqueio manual
- Validação de CPF e normalização de telefone para E.164

### Produtos (porta 8002)
- Produtos, categorias e variantes (preço de venda calculado por markup)
- Catálogo público / loja online (config, fotos, publicação)
- Fornecedores e vínculo fornecedor-produto

### Estoque (porta 8003)
- Saldo por produto/variante, movimentações, lotes e inventário
- Reserva, liberação, baixa e estorno de estoque por venda (idempotentes)
- Listagens de estoque baixo, zerado e lotes vencendo; relatórios

### Vendas (porta 8004)
- Vendas (balcão) e loja online: carrinho, checkout, rastreio de pedido
- Integração Mercado Pago (preferência + webhook)
- Configuração de entrega (faixas por CEP), de pagamento e de integrações (WhatsApp/SMTP) por empresa
- Workflow de status: PEDIDO, PENDENTE_PAGAMENTO, CONFIRMADA, SEPARADA, EM_ENTREGA, ENTREGUE, FINALIZADA, CANCELADA, REEMBOLSADA
- Dois loops assíncronos dentro do processo (pagamentos pendentes a cada 60 s, reconciliação de estoque a cada 120 s)

### Financeiro (porta 8005) — esqueleto
- Só `/health`. Contas a receber, pagamentos de fiado e cobrança **não existem no código**.

### Notificações (porta 8006) — esqueleto
- Só `/health`. Não há consumidor de eventos, envio de WhatsApp nem histórico neste serviço.

---

## Comunicação Entre Serviços

Resumo (detalhe e linhas de código em [`comunicacao.md`](comunicacao.md)):

- **HTTP síncrono com `httpx`** é o único mecanismo em uso. Cliente → gateway → serviço;
  entre serviços, chamadas diretas carimbadas com `X-Servico-Interno-Token`.
- Integrações existentes: estoque → produtos; vendas → produtos, clientes, estoque,
  empresas e gateway.
- **Eventos assíncronos**: existe o exchange `erp.events` (tipo `topic`, declarado em
  `services/*/events/publisher.py`), mas nenhum código chama `publish()` e não há
  consumidor. Só existem as definições dos 6 tipos de evento em `shared/events/base.py`
  (`pedido.confirmado`, `pedido.cancelado`, `estoque.minimo`, `cobranca.lembrete`,
  `cobranca.vencida`, `conta.quitada`), sem emissor nem receptor.

### Infraestrutura
- **PostgreSQL 15**: 1 instância, 1 database, 8 schemas (um por serviço, incluindo o gateway)
- **Redis 7**: refresh tokens e idempotência no gateway; carrinho/cache no vendas
- **RabbitMQ 3.12**: sobe no compose, sem uso
- **Cloudflare Tunnel**: acesso externo em produção (`app.runaserp.com.br`, ver comentário em `docker-compose.prod.yml`)
- **Docker Compose**: orquestração (dev/prod/cloudflare/build)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Última verificação contra o código:** 2026-09-26
