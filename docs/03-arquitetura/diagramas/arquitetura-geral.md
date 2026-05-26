# 🏗️ Arquitetura Visual - Runas

Diagramas e visualizações da arquitetura do sistema.

---

## 📊 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE                                  │
│                    (Web / Mobile / API)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                 │
│                      (porta 8000)                                │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Autenticação │  │ Rate Limiting│  │   Logging    │          │
│  │     JWT      │  │              │  │  Estruturado │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────────────────────────────────────────┐           │
│  │           Roteamento para Microsserviços         │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CLIENTES   │    │   PRODUTOS   │    │   ESTOQUE    │
│  (porta 8001)│    │  (porta 8002)│    │  (porta 8003)│
│              │    │              │    │              │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │PostgreSQL│ │    │ │PostgreSQL│ │    │ │PostgreSQL│ │
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    VENDAS    │    │  FINANCEIRO  │    │ NOTIFICAÇÕES │
│  (porta 8004)│    │  (porta 8005)│    │  (porta 8006)│
│              │    │              │    │              │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │PostgreSQL│ │    │ │PostgreSQL│ │    │ │PostgreSQL│ │
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────────────┴────────────────────┘
                             │
                             │ Eventos
                             ▼
        ┌────────────────────────────────────────┐
        │            RABBITMQ                     │
        │         (porta 5672/15672)              │
        │                                         │
        │  Exchange: erp.events (topic)          │
        │  ├─ pedido.confirmado                  │
        │  ├─ pedido.cancelado                   │
        │  ├─ estoque.minimo                     │
        │  ├─ cobranca.lembrete                  │
        │  ├─ cobranca.vencida                   │
        │  └─ conta.quitada                      │
        └────────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌──────────────┐                        ┌──────────────┐
│    REDIS     │                        │CELERY WORKER │
│ (porta 6379) │                        │   + BEAT     │
│              │                        │              │
│ • Tokens     │                        │ • Jobs       │
│ • Cache      │                        │ • Vencimento │
│ • Dedup      │                        │ • Lembrete   │
└──────────────┘                        └──────────────┘
```

---

## 🔄 Fluxo de Autenticação

```
┌────────┐                                    ┌─────────────┐
│Cliente │                                    │ API Gateway │
└───┬────┘                                    └──────┬──────┘
    │                                                │
    │  POST /auth/login                              │
    │  (email + senha)                               │
    ├───────────────────────────────────────────────>│
    │                                                │
    │                                         ┌──────▼──────┐
    │                                         │  Validar    │
    │                                         │  Credenciais│
    │                                         └──────┬──────┘
    │                                                │
    │                                         ┌──────▼──────┐
    │                                         │   Gerar     │
    │                                         │ Access Token│
    │                                         │Refresh Token│
    │                                         └──────┬──────┘
    │                                                │
    │                                         ┌──────▼──────┐
    │                                         │   Salvar    │
    │                                         │Refresh Token│
    │                                         │  no Redis   │
    │                                         └──────┬──────┘
    │                                                │
    │  200 OK                                        │
    │  {access_token, refresh_token}                │
    │<───────────────────────────────────────────────┤
    │                                                │
    │  GET /clientes                                 │
    │  Authorization: Bearer {access_token}          │
    ├───────────────────────────────────────────────>│
    │                                                │
    │                                         ┌──────▼──────┐
    │                                         │  Validar    │
    │                                         │    Token    │
    │                                         └──────┬──────┘
    │                                                │
    │                                         ┌──────▼──────┐
    │                                         │  Rotear p/  │
    │                                         │  Clientes   │
    │                                         └──────┬──────┘
    │                                                │
    │                                                ▼
    │                                         ┌─────────────┐
    │                                         │  Serviço    │
    │                                         │  Clientes   │
    │                                         └──────┬──────┘
    │                                                │
    │  200 OK                                        │
    │  {lista de clientes}                           │
    │<───────────────────────────────────────────────┤
    │                                                │
```

---

## 🛒 Fluxo de Venda à Vista (PIX)

```
┌────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐
│Cliente │  │ Vendas  │  │Estoque │  │Mercado   │  │Notifica  │
│        │  │         │  │        │  │Pago      │  │ções      │
└───┬────┘  └────┬────┘  └───┬────┘  └────┬─────┘  └────┬─────┘
    │            │            │            │             │
    │ 1. Adicionar itens      │            │             │
    │    ao carrinho          │            │             │
    ├───────────>│            │            │             │
    │            │            │            │             │
    │            │ 2. Verificar estoque    │             │
    │            ├───────────>│            │             │
    │            │<───────────┤            │             │
    │            │   OK       │            │             │
    │            │            │            │             │
    │ 3. Checkout (PIX)       │            │             │
    ├───────────>│            │            │             │
    │            │            │            │             │
    │            │ 4. Gerar QR Code PIX    │             │
    │            ├───────────────────────>│             │
    │            │<───────────────────────┤             │
    │            │   QR Code              │             │
    │            │            │            │             │
    │<───────────┤            │            │             │
    │  QR Code   │            │            │             │
    │            │            │            │             │
    │ 5. Cliente paga         │            │             │
    │            │            │            │             │
    │            │            │ 6. Webhook │             │
    │            │<───────────────────────┤             │
    │            │   Pagamento aprovado   │             │
    │            │            │            │             │
    │            │ 7. Dar baixa no estoque│             │
    │            ├───────────>│            │             │
    │            │<───────────┤            │             │
    │            │   OK       │            │             │
    │            │            │            │             │
    │            │ 8. Publicar evento     │             │
    │            │   pedido.confirmado    │             │
    │            ├───────────────────────────────────>│
    │            │            │            │             │
    │            │            │            │ 9. Enviar   │
    │            │            │            │    WhatsApp │
    │<───────────┼────────────┼────────────┼─────────────┤
    │  Confirmação            │            │             │
    │            │            │            │             │
```

---

## 💳 Fluxo de Venda Fiada

```
┌────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐
│Cliente │  │ Vendas  │  │Clientes│  │Financeiro│  │Estoque   │
│        │  │         │  │        │  │          │  │          │
└───┬────┘  └────┬────┘  └───┬────┘  └────┬─────┘  └────┬─────┘
    │            │            │            │             │
    │ 1. Checkout (Fiado)     │            │             │
    ├───────────>│            │            │             │
    │            │            │            │             │
    │            │ 2. Verificar crédito    │             │
    │            ├───────────>│            │             │
    │            │<───────────┤            │             │
    │            │   Crédito OK            │             │
    │            │            │            │             │
    │            │ 3. Debitar crédito      │             │
    │            ├───────────>│            │             │
    │            │<───────────┤            │             │
    │            │   OK       │            │             │
    │            │            │            │             │
    │            │ 4. Criar conta a receber│             │
    │            ├───────────────────────>│             │
    │            │<───────────────────────┤             │
    │            │   Conta criada         │             │
    │            │            │            │             │
    │            │ 5. Dar baixa no estoque│             │
    │            ├───────────────────────────────────>│
    │            │<───────────────────────────────────┤
    │            │   OK                   │             │
    │            │            │            │             │
    │<───────────┤            │            │             │
    │  Pedido    │            │            │             │
    │  Confirmado│            │            │             │
    │            │            │            │             │
```

---

## 📅 Fluxo de Cobrança Automática

```
┌──────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
│Celery    │  │Financeiro│  │Clientes│  │Notifica  │
│Beat      │  │          │  │        │  │ções      │
└────┬─────┘  └────┬─────┘  └───┬────┘  └────┬─────┘
     │             │            │             │
     │ 1. Job diário (00:00)    │             │
     ├────────────>│            │             │
     │             │            │             │
     │             │ 2. Buscar contas vencidas│
     │             │            │             │
     │             │ 3. Marcar como VENCIDO   │
     │             │            │             │
     │             │ 4. Verificar crédito     │
     │             ├───────────>│             │
     │             │<───────────┤             │
     │             │            │             │
     │             │ 5. Bloquear se necessário│
     │             ├───────────>│             │
     │             │<───────────┤             │
     │             │            │             │
     │             │ 6. Publicar evento       │
     │             │   cobranca.vencida       │
     │             ├───────────────────────>│
     │             │            │             │
     │             │            │ 7. Enviar   │
     │             │            │    WhatsApp │
     │             │            │             │
     │             │            │             │
     │ 8. Job lembrete (3 dias antes)        │
     ├────────────>│            │             │
     │             │            │             │
     │             │ 9. Buscar contas a vencer│
     │             │            │             │
     │             │ 10. Publicar evento      │
     │             │    cobranca.lembrete     │
     │             ├───────────────────────>│
     │             │            │             │
     │             │            │ 11. Enviar  │
     │             │            │     WhatsApp│
     │             │            │             │
```

---

## 🗄️ Modelo de Dados Simplificado

### Clientes

```
┌─────────────────┐
│    Cliente      │
├─────────────────┤
│ id (PK)         │
│ cpf (UK)        │
│ nome            │
│ telefone        │
│ email           │
│ limite_credito  │
│ credito_disp    │
│ dia_vencimento  │
│ bloqueado       │
│ ativo           │
└────────┬────────┘
         │ 1:N
         │
┌────────▼────────┐
│    Endereco     │
├─────────────────┤
│ id (PK)         │
│ cliente_id (FK) │
│ cep             │
│ logradouro      │
│ numero          │
│ bairro          │
│ cidade          │
│ uf              │
│ principal       │
└─────────────────┘
```

### Produtos

```
┌─────────────────┐
│   Categoria     │
├─────────────────┤
│ id (PK)         │
│ nome (UK)       │
│ descricao       │
└────────┬────────┘
         │ 1:N
         │
┌────────▼────────┐
│    Produto      │
├─────────────────┤
│ id (PK)         │
│ categoria_id(FK)│
│ nome            │
│ descricao       │
│ ativo           │
└────────┬────────┘
         │ 1:N
         │
┌────────▼────────┐
│    Variante     │
├─────────────────┤
│ id (PK)         │
│ produto_id (FK) │
│ sku (UK)        │
│ preco_custo     │
│ markup_pct      │
│ preco_venda     │
│ ativo           │
└─────────────────┘
```

### Vendas

```
┌─────────────────┐
│    Carrinho     │
├─────────────────┤
│ id (PK)         │
│ cliente_id      │
│ status          │
│ expira_em       │
└────────┬────────┘
         │ 1:N
         │
┌────────▼────────┐
│  ItemCarrinho   │
├─────────────────┤
│ id (PK)         │
│ carrinho_id(FK) │
│ variante_id     │
│ quantidade      │
│ preco_unitario  │
└─────────────────┘

┌─────────────────┐
│     Pedido      │
├─────────────────┤
│ id (PK)         │
│ cliente_id      │
│ origem          │
│ modalidade_pagto│
│ modalidade_entr │
│ status          │
│ subtotal        │
│ frete           │
│ total           │
└────────┬────────┘
         │ 1:N
         │
┌────────▼────────┐
│   ItemPedido    │
├─────────────────┤
│ id (PK)         │
│ pedido_id (FK)  │
│ variante_id     │
│ quantidade      │
│ preco_unitario  │
│ subtotal        │
└─────────────────┘
```

---

## 🔌 Integrações Externas

```
┌─────────────────────────────────────────────────────┐
│                     Runas                           │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           │                      │
           ▼                      ▼
┌──────────────────┐    ┌──────────────────┐
│  Mercado Pago    │    │  Evolution API   │
│                  │    │   (WhatsApp)     │
├──────────────────┤    ├──────────────────┤
│ • Gerar QR PIX   │    │ • Enviar msgs    │
│ • Webhook        │    │ • Templates      │
│ • Consultar      │    │ • Retry          │
│   pagamento      │    │ • Deduplicação   │
│ • Validar HMAC   │    │                  │
└──────────────────┘    └──────────────────┘
```

---

## 📊 Camadas da Aplicação

```
┌─────────────────────────────────────────────────┐
│                   ROUTERS                       │
│         (Endpoints FastAPI - HTTP)              │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│                  SERVICES                       │
│         (Regras de Negócio - Lógica)            │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│                REPOSITORIES                     │
│         (Acesso a Dados - Queries)              │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│                   MODELS                        │
│         (SQLAlchemy - ORM)                      │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│                 POSTGRESQL                      │
│         (Banco de Dados)                        │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Comunicação entre Serviços

### Síncrona (HTTP)

```
Vendas ──HTTP──> Clientes  (verificar crédito)
Vendas ──HTTP──> Estoque   (verificar disponibilidade)
Vendas ──HTTP──> Estoque   (dar baixa)
Financeiro ──HTTP──> Clientes  (atualizar crédito)
Produtos ──HTTP──> Estoque  (consultar quantidade)
```

### Assíncrona (RabbitMQ)

```
Vendas ──Event──> Notificações  (pedido.confirmado)
Vendas ──Event──> Notificações  (pedido.cancelado)
Estoque ──Event──> Notificações  (estoque.minimo)
Financeiro ──Event──> Notificações  (cobranca.vencida)
Financeiro ──Event──> Notificações  (cobranca.lembrete)
Financeiro ──Event──> Notificações  (conta.quitada)
```

---

## 🎯 Conclusão

Esta arquitetura oferece:

✅ **Escalabilidade**: Cada serviço pode escalar independentemente  
✅ **Resiliência**: Falha em um serviço não afeta os outros  
✅ **Manutenibilidade**: Código organizado e separado por domínio  
✅ **Performance**: Comunicação assíncrona para operações não críticas  
✅ **Segurança**: Autenticação centralizada no gateway  

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
