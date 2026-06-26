# Visão Geral da Arquitetura - Runas

> **Contexto geral, stack tecnológica e estrutura de microsserviços**

---

## Contexto Geral

Você é um engenheiro sênior Python especializado em arquiteturas de microsserviços. Sua tarefa é gerar o código completo e funcional do backend MVP de um ERP para comércio de alimentos e bebidas chamado **Runas**, seguindo rigorosamente as especificações abaixo. O código deve ser production-ready para MVP: limpo, sem gambiarras, com tratamento de erros, logs e tipagem completa.

---

## Stack Obrigatória

| Camada | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12 |
| Framework | FastAPI | latest |
| ORM | SQLAlchemy | 2.x (async) |
| Migrations | Alembic | latest |
| Banco | PostgreSQL | 15 |
| Autenticação | OAuth2 + JWT | python-jose + passlib |
| Fila | RabbitMQ + Celery | latest |
| Cache/broker backend | Redis | 7 |
| Notificações | Evolution API (WhatsApp) | self-hosted |
| Pagamentos | Mercado Pago API | PIX automático via webhook |
| Containerização | Docker + Docker Compose | latest |
| Testes | Pytest + pytest-asyncio | cobertura básica |
| Validação | Pydantic v2 | latest |

---

## Arquitetura de Microsserviços

O sistema possui **7 microsserviços independentes** + **1 API Gateway**, totalizando **8 serviços**. Cada microsserviço tem seu próprio schema PostgreSQL isolado (multi-tenancy por schema):

```
erp-runas/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.cloudflare.yml      # Cloudflare Tunnel
├── .env
├── .env.example
├── .gitignore
├── README.md
├── QUICK-START.md
├── CHECKLIST_DESENVOLVIMENTO.md
├── FRONTEND_IMPLEMENTACAO.md
├── GUIA_PERFORMANCE.md
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                        # FastAPI + roteamento
│   ├── auth/
│   │   ├── jwt.py                     # JWT tokens
│   │   ├── oauth2.py                  # OAuth2 (Google, Microsoft)
│   │   └── redis_client.py            # Blacklist de tokens
│   ├── middleware/
│   │   ├── rate_limit.py
│   │   └── logging_middleware.py
│   ├── models/
│   │   ├── usuario.py
│   │   └── cliente_auth.py            # OAuth clientes
│   └── routers/
│       ├── auth.py
│       ├── auth_admin.py
│       ├── auth_cliente.py
│       └── proxy.py
├── services/
│   ├── empresas/                      # Multi-tenancy
│   ├── clientes/
│   ├── produtos/
│   ├── estoque/
│   ├── vendas/
│   ├── financeiro/
│   └── notificacoes/
├── frontend/                          # React + TypeScript
│   ├── src/
│   ├── public/
│   └── Dockerfile
└── shared/
    ├── events/
    ├── exceptions.py
    └── pagination.py
```

### Estrutura Interna de Cada Serviço (Padrão Obrigatório)

```
services/{servico}/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/
├── main.py                            # FastAPI app + routers
├── database.py                        # engine async + session
├── models/
│   └── {entidade}.py                  # SQLAlchemy models
├── schemas/
│   └── {entidade}.py                  # Pydantic v2 schemas
├── repositories/
│   └── {entidade}_repository.py       # padrão Repository (acesso a dados)
├── services/
│   └── {entidade}_service.py          # regras de negócio
├── routers/
│   └── {entidade}.py                  # endpoints FastAPI
├── events/
│   └── publisher.py                   # publicador RabbitMQ
└── tests/
    ├── conftest.py
    └── test_{entidade}.py
```

---

## Visão Geral dos Microsserviços

### 1. API Gateway (porta 8000)
- Recebe todas as requisições externas
- Autenticação JWT e OAuth2 (Google, Microsoft)
- Roteamento para serviços internos
- Rate limiting
- Log estruturado
- Gestão de usuários admin e clientes OAuth

### 2. Serviço de Empresas (porta 8001)
- **Multi-tenancy**: Gestão de empresas/tenants
- CRUD de empresas
- Isolamento de dados por empresa_id
- Configurações por empresa

### 3. Serviço de Clientes (porta 8002)
- Gestão de clientes e endereços
- Controle de crédito e limite
- Validação de CPF
- Bloqueio automático por inadimplência

### 4. Serviço de Produtos (porta 8003)
- Produtos, categorias e variantes
- Catálogo público (loja online)
- Gestão de fornecedores
- Upload de fotos
- Cálculo automático de preço de venda

### 5. Serviço de Estoque (porta 8004)
- Controle de estoque por variante
- Movimentações (entrada, saída, ajuste, devolução, perda)
- Gestão de lotes
- Inventário físico
- Alertas de estoque mínimo
- Reserva/liberação para vendas
- Histórico imutável

### 6. Serviço de Vendas (porta 8007)
- Checkout e pedidos (loja online)
- Integração com Mercado Pago (PIX)
- Workflow de vendas (6 estados)
- Gestão de status de pedidos
- Múltiplas formas de pagamento
- Snapshot de dados do produto

### 7. Serviço Financeiro (porta 8005)
- Contas a receber
- Pagamentos fiados
- Controle de vencimentos
- Jobs automáticos de cobrança

### 8. Serviço de Notificações (porta 8006)
- WhatsApp via Evolution API
- Consumidor de eventos RabbitMQ
- Retry automático
- Deduplicação de mensagens

---

## Comunicação Entre Serviços

### HTTP Interno
- Serviços se comunicam via HTTP (httpx async)
- URLs internas via Docker network
- Exemplos de integrações:
  - Vendas → Estoque (reserva/baixa de estoque)
  - Vendas → Clientes (validação de crédito)
  - Produtos → Estoque (consulta de disponibilidade)

### Eventos Assíncronos (RabbitMQ)
- Exchange: `erp.events` (tipo: topic)
- Eventos principais:
  - `pedido.confirmado`
  - `pedido.cancelado`
  - `estoque.minimo`
  - `cobranca.lembrete`
  - `cobranca.vencida`
  - `conta.quitada`

### Infraestrutura
- **PostgreSQL**: 1 instância com 8 schemas isolados (um por serviço)
- **Redis**: Cache, sessões, blacklist de tokens
- **RabbitMQ**: Mensageria assíncrona
- **Cloudflare Tunnel**: Acesso externo (www.runaserp.com.br)
- **Docker Compose**: Orquestração de todos os serviços

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Junho de 2026  
**Versão:** 2.0.0  
**Atualização**: Sistema com 8 serviços (+ Empresas), Multi-tenancy, Loja Online completa
