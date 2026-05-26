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

Gere **6 microsserviços independentes** + **1 API Gateway**, cada um com seu próprio banco PostgreSQL:

```
erp-runas/
├── docker-compose.yml
├── docker-compose.override.yml        # dev overrides
├── .env.example
├── .gitignore
├── Makefile                           # comandos utilitários
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                        # roteamento + validação JWT
│   ├── auth/
│   │   ├── jwt.py                     # geração e validação de tokens
│   │   └── oauth2.py                  # fluxo OAuth2
│   └── middleware/
│       ├── rate_limit.py
│       └── logging.py
├── services/
│   ├── clientes/
│   ├── produtos/
│   ├── estoque/
│   ├── vendas/
│   ├── financeiro/
│   └── notificacoes/
└── shared/
    ├── events/                        # DomainEvents compartilhados
    │   └── base.py
    ├── exceptions.py                  # exceções customizadas comuns
    └── pagination.py                  # schema de paginação padrão
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
- Validação JWT em rotas protegidas
- Roteamento para serviços internos
- Rate limiting
- Log estruturado

### 2. Serviço de Clientes (porta 8001)
- Gestão de clientes e endereços
- Controle de crédito e limite
- Validação de CPF
- Bloqueio automático por inadimplência

### 3. Serviço de Produtos (porta 8002)
- Produtos, categorias e variantes
- Catálogo público
- Gestão de fornecedores
- Cálculo automático de preço de venda

### 4. Serviço de Estoque (porta 8003)
- Controle de estoque por variante
- Movimentações (entrada, saída, ajuste)
- Alertas de estoque mínimo
- Histórico imutável

### 5. Serviço de Vendas (porta 8004)
- Carrinho de compras
- Checkout e pedidos
- Integração com Mercado Pago (PIX)
- Gestão de status de pedidos

### 6. Serviço Financeiro (porta 8005)
- Contas a receber
- Pagamentos fiados
- Controle de vencimentos
- Jobs automáticos de cobrança

### 7. Serviço de Notificações (porta 8006)
- WhatsApp via Evolution API
- Consumidor de eventos RabbitMQ
- Retry automático
- Deduplicação de mensagens

---

## Comunicação Entre Serviços

### HTTP Interno
- Serviços se comunicam via HTTP (httpx async)
- URLs internas via Docker network
- Nunca importar código de outro serviço

### Eventos Assíncronos (RabbitMQ)
- Exchange: `erp.events` (tipo: topic)
- Eventos principais:
  - `pedido.confirmado`
  - `pedido.cancelado`
  - `estoque.minimo`
  - `cobranca.lembrete`
  - `cobranca.vencida`
  - `conta.quitada`

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
