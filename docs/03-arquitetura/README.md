# 🏗️ Arquitetura do Sistema

Documentação completa da arquitetura do Runas.

## 📑 Índice

### Visão Geral
- [Arquitetura de Microserviços](./microservicos.md) - Estrutura e organização dos serviços
- [Comunicação entre Serviços](./comunicacao.md) - Padrões de comunicação síncrona e assíncrona
- [Banco de Dados](./banco-dados.md) - Estrutura e modelagem de dados
- [Sistema de Autenticação](./autenticacao.md) - JWT, OAuth2 e controle de acesso

### Diagramas
- [Arquitetura Geral](./diagramas/arquitetura-geral.md) - Visão visual da arquitetura
- [Diagramas de Sequência](./diagramas/sequencia.md) - Fluxos detalhados de operações
- [Fluxo de Autenticação](./diagramas/fluxo-autenticacao.md) - Processo de login e autorização

---

## 🎯 Visão Geral da Arquitetura

O Runas utiliza uma **arquitetura de microserviços** com os seguintes componentes principais:

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│                     http://localhost:3000                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                     │
│                     http://localhost:8000                    │
│  • Autenticação JWT                                          │
│  • Rate Limiting                                             │
│  • Roteamento para Microserviços                            │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Clientes   │  │   Produtos   │  │   Estoque    │
│   :8001      │  │   :8002      │  │   :8003      │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Vendas    │  │  Financeiro  │  │ Notificações │
│    :8004     │  │   :8005      │  │   :8006      │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │   RabbitMQ   │  │    Redis     │
│  (8 bancos)  │  │   :5672      │  │   :6379      │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Microserviços

| Serviço | Porta | Responsabilidade | Status |
|---------|-------|------------------|--------|
| **API Gateway** | 8000 | Autenticação, roteamento, rate limiting | ✅ 70% |
| **Clientes** | 8001 | Gestão de clientes, endereços, crédito | ⏳ 5% |
| **Produtos** | 8002 | Catálogo, variantes, fornecedores | ⏳ 5% |
| **Estoque** | 8003 | Controle de estoque, movimentações, lotes | ⏳ 5% |
| **Vendas** | 8004 | Carrinho, pedidos, pagamentos | ⏳ 5% |
| **Financeiro** | 8005 | Contas a receber, vendas fiadas | ⏳ 5% |
| **Notificações** | 8006 | WhatsApp via Evolution API | ⏳ 5% |

### Infraestrutura

| Componente | Porta | Função |
|------------|-------|--------|
| **PostgreSQL** | 5432 | 8 bancos de dados (1 por serviço + Evolution) |
| **RabbitMQ** | 5672 | Mensageria assíncrona entre serviços |
| **Redis** | 6379 | Cache, sessões, rate limiting |
| **pgAdmin** | 5050 | Interface de administração de bancos |
| **Evolution API** | 8080 | Integração com WhatsApp |

---

## 🔄 Padrões de Comunicação

### Comunicação Síncrona (HTTP/REST)
- Frontend ↔ API Gateway
- API Gateway ↔ Microserviços
- Microserviços ↔ Microserviços (quando necessário)

### Comunicação Assíncrona (RabbitMQ)
- Eventos de domínio (ex: `estoque.baixo`, `venda.finalizada`)
- Notificações (ex: envio de WhatsApp)
- Processamento em background

### Cache (Redis)
- Sessões de usuário
- Rate limiting
- Cache de dados frequentes
- Carrinho de compras (TTL 2h)

---

## 🔐 Segurança

### Autenticação
- **JWT** (JSON Web Tokens) para autenticação stateless
- **OAuth2** com Google e Microsoft
- **Refresh Tokens** para renovação automática
- **Redis** para blacklist de tokens revogados

### Autorização
- **RBAC** (Role-Based Access Control)
- Roles: `ADMIN`, `GERENTE`, `VENDEDOR`, `CLIENTE`
- Middlewares de autorização no API Gateway

### Proteção
- **Rate Limiting** (100 req/min por IP)
- **CORS** configurado
- **HTTPS** em produção
- **Validação de entrada** em todos os endpoints

---

## 📊 Banco de Dados

### Estratégia: Database per Service

Cada microserviço possui seu próprio banco PostgreSQL:

```
db_gateway      → API Gateway (usuários, tokens)
db_clientes     → Serviço de Clientes
db_produtos     → Serviço de Produtos
db_estoque      → Serviço de Estoque
db_vendas       → Serviço de Vendas
db_financeiro   → Serviço Financeiro
db_notificacoes → Serviço de Notificações
db_evolution    → Evolution API
```

**Vantagens:**
- Isolamento de dados
- Escalabilidade independente
- Falhas isoladas
- Tecnologias diferentes por serviço (se necessário)

**Desafios:**
- Transações distribuídas (Saga Pattern)
- Consistência eventual
- Joins entre serviços (via API)

---

## 🚀 Escalabilidade

### Horizontal Scaling
- Cada microserviço pode escalar independentemente
- Load balancer (Nginx) distribui requisições
- Stateless design permite múltiplas instâncias

### Vertical Scaling
- Recursos ajustáveis por serviço no Docker Compose
- Otimização de queries e índices
- Cache estratégico com Redis

### Performance
- **Connection Pooling** em todos os serviços
- **Índices** em colunas frequentemente consultadas
- **Paginação** em listagens
- **Cache** de dados estáticos

---

## 📚 Documentos Relacionados

- [Comunicação entre Serviços](./comunicacao.md)
- [Diagramas de Sequência](./diagramas/sequencia.md)
- [Especificação Técnica Completa](../01-visao-geral/arquitetura.md)
- [Regras de Negócio](../11-regras-negocio/)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0 (MVP)
