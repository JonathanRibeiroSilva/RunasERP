# 📋 Arquivos Faltantes para Implementação Completa

Lista detalhada de TODOS os arquivos que precisam ser criados em cada microsserviço.

---

## 🎯 Resumo

Cada microsserviço precisa de:
- ✅ **Estrutura base** (já criada)
- ⏳ **Models** (modelos SQLAlchemy)
- ⏳ **Schemas** (Pydantic)
- ⏳ **Repositories** (acesso a dados)
- ⏳ **Services** (lógica de negócio)
- ⏳ **Routers** (endpoints FastAPI)
- ⏳ **Utils** (validadores, helpers)
- ⏳ **Tests** (testes completos)

---

## 1. Serviço de Clientes (porta 8001)

### ✅ Já Criados
- [x] `config.py`
- [x] `database.py`
- [x] `main.py`
- [x] `Dockerfile`
- [x] `requirements.txt`
- [x] `alembic.ini`
- [x] `alembic/env.py`
- [x] `events/publisher.py`
- [x] `tests/conftest.py`
- [x] `seed.py`
- [x] `models/cliente.py` ✅
- [x] `schemas/cliente.py` ✅
- [x] `repositories/cliente_repository.py` ✅
- [x] `utils/validators.py` ✅

### ⏳ Faltam Criar

```
services/clientes/
├── services/
│   └── cliente_service.py          # Lógica de negócio
├── routers/
│   ├── clientes.py                 # Endpoints de clientes
│   └── enderecos.py                # Endpoints de endereços
├── tests/
│   ├── test_models.py              # Testes de modelos
│   ├── test_repositories.py        # Testes de repositories
│   ├── test_services.py            # Testes de services
│   ├── test_routers.py             # Testes de routers
│   └── test_validators.py          # Testes de validadores
└── models/
    └── __init__.py                 # Atualizar imports
```

**Total**: 9 arquivos

---

## 2. Serviço de Produtos (porta 8002)

### ⏳ Faltam Criar

```
services/produtos/
├── models/
│   ├── categoria.py                # Modelo Categoria
│   ├── produto.py                  # Modelo Produto
│   ├── variante.py                 # Modelo Variante + AtributoVariante
│   ├── catalogo.py                 # Modelo CatalogoConfig + CatalogoFoto
│   ├── fornecedor.py               # Modelo Fornecedor + FornecedorProduto
│   └── __init__.py                 # Imports
├── schemas/
│   ├── categoria.py                # Schemas Categoria
│   ├── produto.py                  # Schemas Produto
│   ├── variante.py                 # Schemas Variante
│   ├── catalogo.py                 # Schemas Catálogo
│   ├── fornecedor.py               # Schemas Fornecedor
│   └── __init__.py                 # Imports
├── repositories/
│   ├── categoria_repository.py
│   ├── produto_repository.py
│   ├── variante_repository.py
│   ├── catalogo_repository.py
│   ├── fornecedor_repository.py
│   └── __init__.py
├── services/
│   ├── produto_service.py          # Lógica de produtos
│   ├── variante_service.py         # Cálculo de preço
│   ├── catalogo_service.py         # Integração com estoque
│   ├── fornecedor_service.py
│   └── __init__.py
├── routers/
│   ├── categorias.py
│   ├── produtos.py
│   ├── variantes.py
│   ├── catalogo_admin.py           # Endpoints admin
│   ├── catalogo_publico.py         # Endpoints públicos
│   ├── fornecedores.py
│   └── __init__.py
├── utils/
│   ├── validators.py               # Validação CNPJ
│   └── __init__.py
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    ├── test_routers.py
    ├── test_validators.py
    └── test_integration.py
```

**Total**: 35 arquivos

---

## 3. Serviço de Estoque (porta 8003)

### ⏳ Faltam Criar

```
services/estoque/
├── models/
│   ├── estoque.py                  # Modelo Estoque
│   ├── movimentacao.py             # Modelo Movimentacao
│   └── __init__.py
├── schemas/
│   ├── estoque.py
│   ├── movimentacao.py
│   └── __init__.py
├── repositories/
│   ├── estoque_repository.py
│   ├── movimentacao_repository.py
│   └── __init__.py
├── services/
│   ├── estoque_service.py          # Entrada/Saída/Ajuste
│   └── __init__.py
├── routers/
│   ├── estoque.py
│   ├── movimentacoes.py
│   └── __init__.py
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    ├── test_routers.py
    └── test_events.py              # Testes de eventos
```

**Total**: 17 arquivos

---

## 4. Serviço de Vendas (porta 8004)

### ⏳ Faltam Criar

```
services/vendas/
├── models/
│   ├── carrinho.py                 # Carrinho + ItemCarrinho
│   ├── pedido.py                   # Pedido + ItemPedido
│   ├── endereco_entrega.py         # EnderecoEntrega
│   ├── pagamento.py                # Pagamento
│   └── __init__.py
├── schemas/
│   ├── carrinho.py
│   ├── pedido.py
│   ├── pagamento.py
│   ├── checkout.py                 # Schema de checkout
│   └── __init__.py
├── repositories/
│   ├── carrinho_repository.py
│   ├── pedido_repository.py
│   ├── pagamento_repository.py
│   └── __init__.py
├── services/
│   ├── carrinho_service.py
│   ├── checkout_service.py         # Fluxo completo
│   ├── pedido_service.py
│   ├── pagamento_service.py
│   └── __init__.py
├── routers/
│   ├── carrinho.py                 # Público
│   ├── checkout.py                 # Público
│   ├── pedidos.py                  # Admin
│   ├── webhook.py                  # Webhook MP
│   └── __init__.py
├── integrations/
│   ├── mercadopago.py              # Cliente MP
│   ├── clientes_client.py          # HTTP para clientes
│   ├── estoque_client.py           # HTTP para estoque
│   └── __init__.py
├── jobs/
│   ├── celery_app.py               # Config Celery
│   ├── tasks.py                    # Task de expiração
│   └── __init__.py
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    ├── test_routers.py
    ├── test_checkout.py            # Testes de checkout
    ├── test_webhook.py             # Testes de webhook
    └── test_integration.py
```

**Total**: 32 arquivos

---

## 5. Serviço Financeiro (porta 8005)

### ⏳ Faltam Criar

```
services/financeiro/
├── models/
│   ├── conta_receber.py            # ContaReceber
│   ├── pagamento_fiado.py          # PagamentoFiado
│   └── __init__.py
├── schemas/
│   ├── conta_receber.py
│   ├── pagamento_fiado.py
│   └── __init__.py
├── repositories/
│   ├── conta_receber_repository.py
│   ├── pagamento_fiado_repository.py
│   └── __init__.py
├── services/
│   ├── financeiro_service.py
│   └── __init__.py
├── routers/
│   ├── contas.py
│   ├── pagamentos.py
│   └── __init__.py
├── integrations/
│   ├── clientes_client.py          # HTTP para clientes
│   └── __init__.py
├── jobs/
│   ├── celery_app.py
│   ├── tasks.py                    # Jobs de vencimento
│   └── __init__.py
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    ├── test_routers.py
    ├── test_jobs.py
    └── test_integration.py
```

**Total**: 22 arquivos

---

## 6. Serviço de Notificações (porta 8006)

### ⏳ Faltam Criar

```
services/notificacoes/
├── models/
│   ├── notificacao.py              # Notificacao
│   └── __init__.py
├── schemas/
│   ├── notificacao.py
│   └── __init__.py
├── repositories/
│   ├── notificacao_repository.py
│   └── __init__.py
├── services/
│   ├── notificacao_service.py
│   └── __init__.py
├── routers/
│   ├── notificacoes.py
│   └── __init__.py
├── integrations/
│   ├── evolution.py                # Cliente Evolution API
│   └── __init__.py
├── consumers/
│   ├── rabbitmq_consumer.py        # Consumer RabbitMQ
│   ├── handlers.py                 # Handlers de eventos
│   └── __init__.py
├── jobs/
│   ├── celery_app.py
│   ├── tasks.py                    # Tasks de retry
│   └── __init__.py
├── utils/
│   ├── deduplication.py            # Deduplicação Redis
│   ├── templates.py                # Templates de mensagens
│   └── __init__.py
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    ├── test_routers.py
    ├── test_consumer.py
    ├── test_integration.py
    └── test_deduplication.py
```

**Total**: 26 arquivos

---

## 📊 Resumo Total

| Serviço | Arquivos Criados | Arquivos Faltantes | Total | % Completo |
|---------|------------------|-------------------|-------|------------|
| **Clientes** | 14 | 9 | 23 | 61% |
| **Produtos** | 10 | 35 | 45 | 22% |
| **Estoque** | 10 | 17 | 27 | 37% |
| **Vendas** | 10 | 32 | 42 | 24% |
| **Financeiro** | 10 | 22 | 32 | 31% |
| **Notificações** | 10 | 26 | 36 | 28% |
| **TOTAL** | **64** | **141** | **205** | **31%** |

---

## 🎯 Prioridade de Implementação

### Alta Prioridade (Semana 1-2)

1. **Completar Clientes** (9 arquivos)
   - Services
   - Routers
   - Testes

2. **Completar Produtos** (35 arquivos)
   - Todos os modelos
   - Repositories
   - Services
   - Routers
   - Testes

### Média Prioridade (Semana 3-4)

3. **Completar Estoque** (17 arquivos)
4. **Completar Vendas - Parte 1** (20 arquivos)
   - Modelos
   - Repositories
   - Carrinho

### Baixa Prioridade (Semana 5-8)

5. **Completar Vendas - Parte 2** (12 arquivos)
   - Checkout
   - Integração MP
   - Jobs

6. **Completar Financeiro** (22 arquivos)
7. **Completar Notificações** (26 arquivos)

---

## 🚀 Próximos Passos

### Opção 1: Gerar Tudo Automaticamente

```bash
# Criar script que gera TODOS os arquivos
python generate_all_implementations.py
```

### Opção 2: Implementar Manualmente (Recomendado)

Seguir o [Guia de Implementação](./GUIA-IMPLEMENTACAO.md) e criar arquivo por arquivo, testando cada um.

### Opção 3: Híbrido

1. Gerar templates de todos os arquivos
2. Implementar lógica de negócio manualmente
3. Testar cada serviço

---

## 📝 Template de Checklist

Use este template para acompanhar o progresso:

```markdown
## Serviço de [Nome]

### Models
- [ ] model1.py
- [ ] model2.py
- [ ] __init__.py

### Schemas
- [ ] schema1.py
- [ ] schema2.py
- [ ] __init__.py

### Repositories
- [ ] repository1.py
- [ ] repository2.py
- [ ] __init__.py

### Services
- [ ] service1.py
- [ ] __init__.py

### Routers
- [ ] router1.py
- [ ] router2.py
- [ ] __init__.py

### Tests
- [ ] test_models.py
- [ ] test_repositories.py
- [ ] test_services.py
- [ ] test_routers.py
- [ ] test_integration.py
```

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0
