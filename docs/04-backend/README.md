# Backend - Runas ERP

## 📋 Visão Geral

Documentação técnica do backend do sistema Runas ERP, construído com arquitetura de microsserviços.

---

## 📚 Documentação Disponível

### 🏗️ Arquitetura

- **[Transações de Banco de Dados](./transacoes-banco-dados.md)** ⭐ **NOVO**
  - Conceitos ACID
  - Padrões de implementação
  - Exemplos práticos
  - Boas práticas
  - Troubleshooting

### 🔌 Integrações

- **[Evolution API](./integracao/evolution-api.md)**
  - Integração com WhatsApp
  - Configuração e uso
  - Webhooks

### 🛠️ API Gateway

- Autenticação e autorização
- Rate limiting
- Roteamento de requisições
- Middleware de logging

### 📦 Microsserviços

#### Clientes
- Gestão de clientes
- Controle de crédito
- Endereços
- Histórico

#### Produtos
- CRUD de produtos
- Categorias
- Variantes (SKU)
- Catálogo
- Fornecedores

#### Estoque
- Controle de estoque
- Movimentações
- Lotes
- Alertas
- Inventário

#### Vendas
- Carrinho de compras
- Checkout
- Pedidos
- Pagamentos
- Frete

#### Financeiro
- Contas a receber
- Pagamentos
- Cobranças
- Relatórios

#### Notificações
- WhatsApp
- Eventos
- Histórico

---

## 🔧 Stack Tecnológica

### Core
- **Python 3.11+**
- **FastAPI** - Framework web assíncrono
- **SQLAlchemy 2.0** - ORM com suporte async
- **Pydantic** - Validação de dados
- **Alembic** - Migrations

### Banco de Dados
- **PostgreSQL 15** - Banco principal (1 por serviço)
- **Redis** - Cache e sessões

### Mensageria
- **RabbitMQ** - Message broker
- **Pika** - Cliente Python para RabbitMQ

### Infraestrutura
- **Docker** - Containerização
- **Docker Compose** - Orquestração local
- **Nginx** - Reverse proxy (produção)

### Observabilidade
- **Structlog** - Logging estruturado
- **pgAdmin** - Administração de banco

---

## 🏛️ Arquitetura em Camadas

```
┌─────────────────────────────────────────┐
│              API GATEWAY                │
│  - Autenticação JWT                     │
│  - Rate Limiting                        │
│  - Roteamento                           │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼────┐   ┌───▼────┐   ┌───▼────┐
│ Serviço│   │ Serviço│   │ Serviço│
│Clientes│   │Produtos│   │ Estoque│
└───┬────┘   └───┬────┘   └───┬────┘
    │            │            │
┌───▼────────────▼────────────▼────┐
│         PostgreSQL (por serviço) │
└──────────────────────────────────┘
```

### Camadas por Serviço

```
┌─────────────────────────────────────────┐
│           ROUTER (FastAPI)              │
│  - Endpoints HTTP                       │
│  - Validação de entrada                 │
│  - Tratamento de exceções HTTP          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            SERVICE LAYER                │
│  - Lógica de negócio                    │
│  - Validações de domínio                │
│  - Gerenciamento de transações ⭐       │
│  - Orquestração de operações            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         REPOSITORY LAYER                │
│  - Operações CRUD                       │
│  - Queries SQL                          │
│  - Mapeamento ORM                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              DATABASE                   │
│  - PostgreSQL                           │
│  - Schemas isolados                     │
└─────────────────────────────────────────┘
```

---

## 🔐 Segurança

### Autenticação
- OAuth2 com JWT
- Refresh tokens
- Expiração configurável
- Revogação de tokens

### Autorização
- Roles: ADMIN, OPERADOR
- Permissões por endpoint
- Validação em middleware

### Rate Limiting
- 100 req/min (anônimo)
- 500 req/min (autenticado)
- Por IP e por usuário

### Validação
- Pydantic schemas
- Validação de CPF/CNPJ
- Sanitização de inputs

---

## 🗄️ Banco de Dados

### Estratégia
- **Database per Service** - Cada microsserviço tem seu próprio banco
- **PostgreSQL 15** - Banco relacional robusto
- **Alembic** - Migrations versionadas
- **Transações ACID** - Garantia de consistência ⭐

### Configuração

```python
# database.py
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Objetos acessíveis após commit
    autocommit=False,        # Transações manuais
    autoflush=False          # Controle manual de flush
)
```

### Migrations

```bash
# Criar migration
alembic revision --autogenerate -m "descrição"

# Aplicar migrations
alembic upgrade head

# Reverter migration
alembic downgrade -1
```

---

## 📡 Comunicação entre Serviços

### Síncrona (HTTP)
- Validações em tempo real
- Consultas de dados
- Operações críticas

```python
async with httpx.AsyncClient() as client:
    response = await client.get(f"{PRODUTOS_URL}/produtos/{id}")
```

### Assíncrona (RabbitMQ)
- Notificações
- Eventos de domínio
- Processamento em background

```python
# Publicar evento
await publish_event("estoque.baixo", {
    "produto_id": produto_id,
    "quantidade": quantidade
})

# Consumir evento
@consumer("estoque.baixo")
async def handle_estoque_baixo(message):
    # Processar evento
    pass
```

---

## 🧪 Testes

### Estrutura

```
tests/
├── conftest.py          # Fixtures compartilhadas
├── test_routers.py      # Testes de endpoints
├── test_services.py     # Testes de lógica de negócio
└── test_repositories.py # Testes de acesso a dados
```

### Executar Testes

```bash
# Todos os testes
pytest

# Com coverage
pytest --cov=. --cov-report=html

# Testes específicos
pytest tests/test_services.py -v
```

---

## 📊 Monitoramento

### Logs Estruturados

```python
import structlog

log = structlog.get_logger()

log.info("operacao_sucesso", 
    usuario_id=usuario_id,
    produto_id=produto_id,
    quantidade=quantidade
)

log.error("operacao_falhou",
    error=str(e),
    stack_trace=traceback.format_exc()
)
```

### Health Checks

Todos os serviços expõem endpoint `/health`:

```json
{
  "status": "healthy",
  "service": "produtos",
  "timestamp": "2026-05-26T10:30:00Z"
}
```

---

## 🚀 Deploy

### Desenvolvimento

```bash
# Subir todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f [servico]

# Rebuild
docker-compose up -d --build
```

### Produção

```bash
# Usar docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d

# Com Nginx
docker-compose -f docker-compose.nginx.yml up -d
```

---

## 📖 Guias Relacionados

- [Transações de Banco de Dados](./transacoes-banco-dados.md) ⭐
- [Evolution API](./integracao/evolution-api.md)
- [Arquitetura Geral](../03-arquitetura/README.md)
- [Setup do Projeto](../02-setup/README.md)
- [API Reference](../10-api-reference/README.md)

---

## 🤝 Contribuindo

### Padrões de Código

1. **Seguir a estrutura de camadas**
   - Router → Service → Repository

2. **Usar transações atômicas**
   - Sempre em operações de escrita
   - Ver [documentação de transações](./transacoes-banco-dados.md)

3. **Validar dados**
   - Pydantic schemas
   - Validações de negócio no service

4. **Documentar endpoints**
   - Docstrings descritivas
   - Exemplos de uso

5. **Escrever testes**
   - Cobertura mínima de 80%
   - Testes unitários e de integração

### Checklist de PR

- [ ] Código segue os padrões do projeto
- [ ] Transações implementadas corretamente
- [ ] Testes escritos e passando
- [ ] Documentação atualizada
- [ ] Migrations criadas (se necessário)
- [ ] Logs estruturados adicionados

---

**Última atualização:** 2026-05-26  
**Versão:** 1.0.0
