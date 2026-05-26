# Tecnologias e Padrões - Runas

> **Stack tecnológica, padrões de código, automações e configurações**

---

## Docker Compose — Estrutura Completa

```yaml
# docker-compose.yml deve conter:
# - api-gateway (porta 8000)
# - clientes (porta 8001, db-clientes)
# - produtos (porta 8002, db-produtos)
# - estoque (porta 8003, db-estoque)
# - vendas (porta 8004, db-vendas)
# - financeiro (porta 8005, db-financeiro)
# - notificacoes (porta 8006, db-notificacoes)
# - rabbitmq:3.12-management (porta 5672 + 15672 painel)
# - redis:7-alpine
# - evolution-api (porta 8080)
# - db-evolution (postgres para Evolution API)
# Todos os serviços na mesma rede: erp-network
# Volumes nomeados para cada banco
# Health checks em todos os serviços
# Variáveis de ambiente via .env
```

---

## Configuração de Ambiente (.env.example)

```env
# JWT
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# Redis
REDIS_URL=redis://redis:6379/0

# Mercado Pago
MP_ACCESS_TOKEN=
MP_WEBHOOK_SECRET=
MP_PUBLIC_KEY=

# Evolution API (WhatsApp)
EVOLUTION_URL=http://evolution-api:8080
EVOLUTION_API_KEY=
EVOLUTION_INSTANCE=runas

# Telefone responsável (alertas internos)
TELEFONE_RESPONSAVEL=+5500000000000

# Databases (um por serviço)
DATABASE_URL_CLIENTES=postgresql+asyncpg://erp:erp@db-clientes:5432/clientes
DATABASE_URL_PRODUTOS=postgresql+asyncpg://erp:erp@db-produtos:5432/produtos
DATABASE_URL_ESTOQUE=postgresql+asyncpg://erp:erp@db-estoque:5432/estoque
DATABASE_URL_VENDAS=postgresql+asyncpg://erp:erp@db-vendas:5432/vendas
DATABASE_URL_FINANCEIRO=postgresql+asyncpg://erp:erp@db-financeiro:5432/financeiro
DATABASE_URL_NOTIFICACOES=postgresql+asyncpg://erp:erp@db-notificacoes:5432/notificacoes

# URLs internas entre serviços
CLIENTES_URL=http://clientes:8001
ESTOQUE_URL=http://estoque:8003
FINANCEIRO_URL=http://financeiro:8005

# pgAdmin
PGADMIN_EMAIL=admin@runas.local
PGADMIN_PASSWORD=admin123

# Seed / Admin inicial
ADMIN_EMAIL=admin@runas.local
ADMIN_PASSWORD=admin123
```

---

## Padrões de Código Obrigatórios

### database.py (padrão para todos os serviços)

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### Repository Pattern (padrão)

```python
class ClienteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar(self, data: ClienteCreate) -> Cliente: ...
    async def buscar_por_id(self, id: UUID) -> Cliente | None: ...
    async def buscar_por_cpf(self, cpf: str) -> Cliente | None: ...
    async def listar(self, filtros: ClienteFiltros, skip: int, limit: int) -> tuple[list[Cliente], int]: ...
    async def atualizar(self, id: UUID, data: ClienteUpdate) -> Cliente: ...
    async def soft_delete(self, id: UUID) -> None: ...
```

### Tratamento de Erros (padrão para todos os routers)

```python
# Usar HTTPException com códigos semânticos:
# 400 → dados inválidos de negócio
# 401 → não autenticado
# 403 → sem permissão (role insuficiente)
# 404 → recurso não encontrado
# 409 → conflito (CPF duplicado, estoque insuficiente, cliente bloqueado)
# 422 → validação Pydantic (automático)
# 500 → erro interno (logar sempre)
```

### Schema de Resposta Padrão (Pydantic v2)

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int
```

### Logging Estruturado (JSON)

```python
import structlog
log = structlog.get_logger()
# Usar em todo service: log.info("cliente.criado", cliente_id=str(id), cpf_hash=hash)
# NUNCA logar CPF, telefone ou dados pessoais em plain text
```

---

## Testes — Padrão Pytest

Gerar testes para **cada serviço** cobrindo:

```python
# conftest.py de cada serviço:
# - fixture de banco em memória (SQLite async para testes)
# - fixture de cliente HTTP async (httpx.AsyncClient)
# - fixture de usuário admin autenticado

# Testes obrigatórios por serviço:
# clientes: test_criar_cliente_valido, test_cpf_invalido, test_cpf_duplicado,
#           test_soft_delete_com_pedido_aberto, test_credito_disponivel_calculado
# produtos: test_criar_produto, test_preco_venda_calculado, test_catalogo_visivel
# estoque:  test_entrada, test_saida_insuficiente, test_alerta_minimo
# vendas:   test_checkout_avista, test_checkout_fiado_bloqueado, test_webhook_pix
# financeiro: test_pagamento_parcial, test_quitacao, test_job_vencimento
# notificacoes: test_retry, test_deduplicacao
```

---

## pgAdmin — Configuração Automática Completa

### Adicionar ao docker-compose.yml

```yaml
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: erp-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@runas.local}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin123}
      PGADMIN_CONFIG_SERVER_MODE: 'True'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
      PGADMIN_SERVER_JSON_FILE: /pgadmin4/servers.json
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
      - ./pgadmin/servers.json:/pgadmin4/servers.json:ro
      - ./pgadmin/pgpass:/pgpass:ro
    depends_on:
      - db-clientes
      - db-produtos
      - db-estoque
      - db-vendas
      - db-financeiro
      - db-notificacoes
    networks:
      - erp-network
    restart: unless-stopped
    entrypoint: >
      /bin/sh -c "
        chmod 600 /pgpass &&
        /entrypoint.sh
      "
```

### Gerar arquivo `pgadmin/servers.json`

```json
{
  "Servers": {
    "1": {
      "Name": "Runas · Clientes",
      "Group": "Runas",
      "Host": "db-clientes",
      "Port": 5432,
      "MaintenanceDB": "clientes",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Clientes"
    },
    "2": {
      "Name": "Runas · Produtos",
      "Group": "Runas",
      "Host": "db-produtos",
      "Port": 5432,
      "MaintenanceDB": "produtos",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Produtos e Catálogo"
    },
    "3": {
      "Name": "Runas · Estoque",
      "Group": "Runas",
      "Host": "db-estoque",
      "Port": 5432,
      "MaintenanceDB": "estoque",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Estoque e Movimentações"
    },
    "4": {
      "Name": "Runas · Vendas",
      "Group": "Runas",
      "Host": "db-vendas",
      "Port": 5432,
      "MaintenanceDB": "vendas",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Vendas, Pedidos e Carrinho"
    },
    "5": {
      "Name": "Runas · Financeiro",
      "Group": "Runas",
      "Host": "db-financeiro",
      "Port": 5432,
      "MaintenanceDB": "financeiro",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço Financeiro e Contas a Receber"
    },
    "6": {
      "Name": "Runas · Notificações",
      "Group": "Runas",
      "Host": "db-notificacoes",
      "Port": 5432,
      "MaintenanceDB": "notificacoes",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Notificações WhatsApp"
    },
    "7": {
      "Name": "Runas · Evolution API",
      "Group": "Runas",
      "Host": "db-evolution",
      "Port": 5432,
      "MaintenanceDB": "evolution",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco interno da Evolution API (WhatsApp)"
    }
  }
}
```

### Gerar arquivo `pgadmin/pgpass`

```
# formato: hostname:port:database:username:password
db-clientes:5432:clientes:erp:erp
db-produtos:5432:produtos:erp:erp
db-estoque:5432:estoque:erp:erp
db-vendas:5432:vendas:erp:erp
db-financeiro:5432:financeiro:erp:erp
db-notificacoes:5432:notificacoes:erp:erp
db-evolution:5432:evolution:erp:erp
```

**Acesso após `docker-compose up`:**
- URL: `http://localhost:5050`
- Email: valor de `PGADMIN_EMAIL`
- Senha: valor de `PGADMIN_PASSWORD`
- Todos os 7 bancos já aparecem conectados no grupo **"Runas"** sem nenhuma ação manual

---

## Automação de Migrations e Inicialização

### Estratégia: Migration Runner como Serviço de Inicialização

Gerar um serviço `migrate` no docker-compose que roda **antes** de todos os serviços da aplicação, executa `alembic upgrade head` em cada banco, e encerra. Os serviços dependem dele via `depends_on` com `condition: service_completed_successfully`.

```yaml
  # docker-compose.yml — adicionar serviço de migrations
  migrate:
    build:
      context: .
      dockerfile: ./scripts/migrate.Dockerfile
    environment:
      - DATABASE_URL_CLIENTES=${DATABASE_URL_CLIENTES}
      - DATABASE_URL_PRODUTOS=${DATABASE_URL_PRODUTOS}
      - DATABASE_URL_ESTOQUE=${DATABASE_URL_ESTOQUE}
      - DATABASE_URL_VENDAS=${DATABASE_URL_VENDAS}
      - DATABASE_URL_FINANCEIRO=${DATABASE_URL_FINANCEIRO}
      - DATABASE_URL_NOTIFICACOES=${DATABASE_URL_NOTIFICACOES}
    volumes:
      - ./services/clientes/alembic:/app/clientes/alembic
      - ./services/clientes/alembic.ini:/app/clientes/alembic.ini
      - ./services/produtos/alembic:/app/produtos/alembic
      - ./services/produtos/alembic.ini:/app/produtos/alembic.ini
      - ./services/estoque/alembic:/app/estoque/alembic
      - ./services/estoque/alembic.ini:/app/estoque/alembic.ini
      - ./services/vendas/alembic:/app/vendas/alembic
      - ./services/vendas/alembic.ini:/app/vendas/alembic.ini
      - ./services/financeiro/alembic:/app/financeiro/alembic
      - ./services/financeiro/alembic.ini:/app/financeiro/alembic.ini
      - ./services/notificacoes/alembic:/app/notificacoes/alembic
      - ./services/notificacoes/alembic.ini:/app/notificacoes/alembic.ini
    depends_on:
      db-clientes:    { condition: service_healthy }
      db-produtos:    { condition: service_healthy }
      db-estoque:     { condition: service_healthy }
      db-vendas:      { condition: service_healthy }
      db-financeiro:  { condition: service_healthy }
      db-notificacoes:{ condition: service_healthy }
    networks:
      - erp-network
    restart: "no"   # roda uma vez e encerra
```

### Gerar `scripts/migrate.Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install alembic asyncpg sqlalchemy
COPY scripts/run_migrations.sh /run_migrations.sh
RUN chmod +x /run_migrations.sh
CMD ["/run_migrations.sh"]
```

### Gerar `scripts/run_migrations.sh`

```bash
#!/bin/bash
set -e   # aborta se qualquer migration falhar

echo "🔄 Iniciando migrations do Runas..."

SERVICOS=("clientes" "produtos" "estoque" "vendas" "financeiro" "notificacoes")

for servico in "${SERVICOS[@]}"; do
  echo "📦 Aplicando migrations: $servico"
  cd /app/$servico
  alembic upgrade head
  echo "✅ $servico — migrations aplicadas com sucesso"
done

echo "🎉 Todas as migrations concluídas!"
```

### Dependência dos Serviços no Migrate

```yaml
  clientes:
    depends_on:
      migrate:   { condition: service_completed_successfully }
      rabbitmq:  { condition: service_healthy }
      redis:     { condition: service_healthy }
  # repetir para produtos, estoque, vendas, financeiro, notificacoes
```

---

## Automação de Seed — Dados Iniciais Obrigatórios

### Gerar `scripts/seed.py`

O seed deve criar automaticamente:

```python
# 1. Usuário admin padrão (se não existir)
usuario_admin = {
    "nome": "Administrador",
    "email": "admin@runas.local",   # lido do .env: ADMIN_EMAIL
    "senha": "admin123",                 # lido do .env: ADMIN_PASSWORD
    "role": "ADMIN"
}

# 2. Categorias iniciais de alimentos e bebidas
categorias = [
    "Carnes e Aves", "Hortifruti", "Laticínios", "Padaria",
    "Bebidas", "Mercearia", "Limpeza", "Outros"
]

# 3. Configuração do RabbitMQ — criar exchange e filas automaticamente
# (usando aio_pika no startup do serviço de notificações)
exchanges_e_filas = {
    "exchange": "erp.events",
    "tipo": "topic",
    "filas": [
        {"nome": "notif.pedidos",    "routing_key": "pedido.#"},
        {"nome": "notif.estoque",    "routing_key": "estoque.#"},
        {"nome": "notif.financeiro", "routing_key": "cobranca.# conta.#"},
    ]
}
```

---

## Automação de Infraestrutura

Gerar um arquivo `scripts/init_infra.py` executado como parte do startup do serviço de notificações que:

```python
# 1. Declara o exchange e todas as filas do RabbitMQ
#    → nunca deixar o worker tentar consumir de fila que não existe

# 2. Verifica conexão com Evolution API e loga se está offline
#    → não abortar, apenas alertar (a API pode demorar para subir)

# 3. Cria índices no Redis para deduplicação de notificações
#    → TTL padrão de 1h

# ORDEM DE EXECUÇÃO GARANTIDA via depends_on + health checks:
# postgres (healthy) → migrate (completed) → rabbitmq (healthy) → redis (healthy) → serviços
```

### Health Checks Obrigatórios

**Para todos os bancos:**

```yaml
  db-clientes:
    image: postgres:15
    environment:
      POSTGRES_DB: clientes
      POSTGRES_USER: erp
      POSTGRES_PASSWORD: erp
    volumes:
      - pgdata-clientes:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erp -d clientes"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
    networks:
      - erp-network
  # repetir o mesmo padrão para todos os outros bancos
```

**Para RabbitMQ e Redis:**

```yaml
  rabbitmq:
    image: rabbitmq:3.12-management
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 20s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
```

---

## Makefile — Versão Completa

```makefile
.PHONY: up down logs migrate seed shell test lint reset

# Sobe tudo (migrations rodam automaticamente antes dos serviços)
up:
	docker-compose up -d
	@echo "✅ Runas rodando"
	@echo "   API Gateway:  http://localhost:8000"
	@echo "   pgAdmin:      http://localhost:5050"
	@echo "   RabbitMQ:     http://localhost:15672"
	@echo "   Swagger docs: http://localhost:8000/docs"

# Derruba tudo mas mantém volumes (dados preservados)
down:
	docker-compose down

# Derruba tudo e apaga todos os volumes (reset total)
reset:
	docker-compose down -v
	@echo "⚠️  Todos os dados foram apagados"

# Logs de todos os serviços
logs:
	docker-compose logs -f

# Logs de um serviço específico: make logs-s s=clientes
logs-s:
	docker-compose logs -f $(s)

# Roda migrations manualmente (útil após criar nova migration)
migrate:
	docker-compose run --rm migrate

# Gera nova migration em um serviço: make migration s=clientes m="add_coluna_x"
migration:
	docker-compose exec $(s) alembic revision --autogenerate -m "$(m)"

# Popula banco com dados iniciais
seed:
	docker-compose exec api-gateway python scripts/seed.py

# Abre shell em um serviço: make shell s=clientes
shell:
	docker-compose exec $(s) /bin/bash

# Testes com coverage em todos os serviços
test:
	@for s in clientes produtos estoque vendas financeiro notificacoes; do \
		echo "🧪 Testando: $$s"; \
		docker-compose exec $$s pytest tests/ -v --cov=. --cov-report=term-missing; \
	done

# Lint e type check em todos os serviços
lint:
	@for s in clientes produtos estoque vendas financeiro notificacoes; do \
		echo "🔍 Lint: $$s"; \
		docker-compose exec $$s ruff check . && mypy .; \
	done

# Rebuild de um serviço sem cache: make rebuild s=clientes
rebuild:
	docker-compose build --no-cache $(s)
	docker-compose up -d $(s)
```

---

## Restrições e Observações Finais

1. **Não usar `async def` em funções que não são realmente assíncronas** — manter consistência
2. **Todas as datas em UTC** — usar `datetime.now(timezone.utc)`, nunca `datetime.utcnow()`
3. **UUIDs gerados no Python**, não pelo banco — usar `uuid.uuid4()` como default
4. **Nunca expor o erro interno direto na API** — logar e retornar mensagem genérica para 500
5. **Comunicação entre serviços via HTTP** (httpx async) — nunca importar código de outro serviço
6. **Paginação padrão**: `?page=1&size=20` em todos os endpoints de listagem
7. **Soft delete padrão**: nunca deletar fisicamente clientes, produtos, pedidos
8. **Migrations**: rodam automaticamente via serviço `migrate` antes de qualquer serviço subir
9. **Health check**: cada serviço expõe `GET /health → {"status": "ok", "service": "clientes"}`
10. **CORS**: configurar no gateway para aceitar domínio do catálogo em produção
11. **Variáveis de ambiente**: todas via `pydantic-settings` com `BaseSettings` — nunca hardcoded
12. **pgAdmin**: conexões pré-configuradas via `servers.json` — nunca configurar manualmente
13. **Ordem de boot garantida**: postgres → migrate → rabbitmq/redis → serviços — via `depends_on` + `condition: service_healthy` e `condition: service_completed_successfully`
14. **Seed automático**: admin padrão e categorias criadas na primeira execução via `make seed`
15. **Exchange e filas RabbitMQ**: declarados automaticamente no startup do serviço de notificações — nunca configurar pelo painel manualmente

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
