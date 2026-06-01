# Prompt de Criação — MVP Backend ERP Runas

---

## Contexto geral

Você é um engenheiro sênior Python especializado em arquiteturas de microsserviços. Sua tarefa é gerar o código completo e funcional do backend MVP de um ERP para comércio de alimentos e bebidas chamado **Runas**, seguindo rigorosamente as especificações abaixo. O código deve ser production-ready para MVP: limpo, sem gambiarras, com tratamento de erros, logs e tipagem completa.

---

## Stack obrigatória

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

## Arquitetura de microsserviços

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

### Estrutura interna de cada serviço (padrão obrigatório):

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

## Detalhamento de cada microsserviço

---

### 1. API Gateway (`api-gateway/` — porta 8000)

**Responsabilidades:**
- Receber todas as requisições externas
- Validar JWT em todas as rotas protegidas
- Rotear para o serviço correto via HTTP interno
- Rate limiting por IP (100 req/min anônimo, 500 req/min autenticado)
- Log estruturado de todas as requisições (JSON)

**Endpoints de autenticação (implementar no gateway):**

```
POST /auth/login          → OAuth2 password flow → retorna access_token + refresh_token
POST /auth/refresh        → renova access_token via refresh_token
POST /auth/logout         → invalida refresh_token (Redis blacklist)
```

**Regras de JWT:**
- `access_token`: expira em 30 minutos
- `refresh_token`: expira em 7 dias, salvo no Redis
- Payload do token deve conter: `sub` (user_id), `role` (ADMIN|OPERADOR), `exp`, `iat`
- Algoritmo: HS256

**Roles:**
- `ADMIN` → acesso total a todos os endpoints
- `OPERADOR` → acesso somente a leitura de produtos, criação de pedidos, consulta de clientes

**Modelo de usuário (no gateway):**

```python
class Usuario(Base):
    id: UUID
    nome: str
    email: str          # unique
    senha_hash: str     # bcrypt via passlib
    role: Enum(ADMIN, OPERADOR)
    ativo: bool
    criado_em: datetime
```

---

### 2. Serviço de Clientes (`services/clientes/` — porta 8001)

**Modelos:**

```python
class Cliente(Base):
    id: UUID (PK)
    cpf: str (UK, NOT NULL, validado com algoritmo CPF)
    nome: str
    telefone: str (NOT NULL — usado para WhatsApp)
    email: Optional[str]
    data_nasc: Optional[date]
    limite_credito: Decimal (default=0.00)
    credito_disponivel: Decimal (default=0.00)
    dia_vencimento: Optional[int]  # 1-28
    bloqueado: bool (default=False)
    ativo: bool (default=True)
    criado_em: datetime

class Endereco(Base):
    id: UUID (PK)
    cliente_id: UUID (FK → clientes.id, ON DELETE CASCADE)
    cep: str
    logradouro: str
    numero: str
    complemento: Optional[str]
    bairro: str
    cidade: str
    uf: str (2 chars)
    principal: bool (default=False)
```

**Endpoints:**

```
POST   /clientes                      → criar cliente (valida CPF único + formato)
GET    /clientes                      → listar (paginado, filtro por nome/cpf/bloqueado)
GET    /clientes/{id}                 → buscar por id
GET    /clientes/cpf/{cpf}            → buscar por CPF (usado no checkout)
PATCH  /clientes/{id}                 → atualizar dados parcialmente
DELETE /clientes/{id}                 → soft delete (ativo=False)

POST   /clientes/{id}/enderecos       → adicionar endereço
GET    /clientes/{id}/enderecos       → listar endereços
PATCH  /clientes/{id}/enderecos/{eid} → atualizar endereço
DELETE /clientes/{id}/enderecos/{eid} → remover endereço

PATCH  /clientes/{id}/credito         → ADMIN: define/ajusta limite_credito e dia_vencimento
PATCH  /clientes/{id}/bloquear        → ADMIN: bloquear cliente manualmente
PATCH  /clientes/{id}/desbloquear     → ADMIN: desbloquear cliente manualmente
GET    /clientes/{id}/historico-credito → extrato de movimentações de crédito
```

**Regras de negócio (implementar no ClienteService):**

1. CPF deve ser validado matematicamente (algoritmo dos dígitos verificadores)
2. Ao definir `limite_credito`, `credito_disponivel` = `limite_credito` − `saldo_devedor_atual`
3. `credito_disponivel` nunca pode ser negativo
4. `bloqueado=True` quando saldo vencido E `credito_disponivel == 0`
5. `dia_vencimento` aceita apenas valores entre 1 e 28
6. Telefone deve estar no formato E.164 (ex: +5511999999999) — validar e normalizar
7. Ao desativar (soft delete), verificar se cliente tem pedidos em aberto ou contas pendentes — se sim, impedir e retornar erro 409

---

### 3. Serviço de Produtos (`services/produtos/` — porta 8002)

**Modelos:**

```python
class Categoria(Base):
    id: UUID (PK)
    nome: str (UK)
    descricao: Optional[str]

class Produto(Base):
    id: UUID (PK)
    categoria_id: UUID (FK → categorias.id)
    nome: str
    descricao: Optional[str]
    ativo: bool (default=True)
    criado_em: datetime

class Variante(Base):
    id: UUID (PK)
    produto_id: UUID (FK → produtos.id, ON DELETE CASCADE)
    sku: str (UK, NOT NULL)
    preco_custo: Decimal (NOT NULL, > 0)
    markup_pct: Decimal (NOT NULL, >= 0)
    preco_venda: Decimal (calculado e armazenado)
    ativo: bool (default=True)

class AtributoVariante(Base):
    id: UUID (PK)
    variante_id: UUID (FK → variantes.id, ON DELETE CASCADE)
    chave: str  # ex: "cor", "tamanho"
    valor: str  # ex: "vermelho", "G"

class CatalogoConfig(Base):
    id: UUID (PK)
    produto_id: UUID (FK UK → produtos.id)
    visivel: bool (default=False)
    destaque: bool (default=False)
    ordem_exibicao: int (default=0)
    descricao_publica: Optional[str]
    atualizado_em: datetime

class CatalogoFoto(Base):
    id: UUID (PK)
    produto_id: UUID (FK → produtos.id, ON DELETE CASCADE)
    url: str
    ordem: int (default=0)

class Fornecedor(Base):
    id: UUID (PK)
    cnpj: str (UK, validado)
    razao_social: str
    nome_fantasia: Optional[str]
    telefone: str
    email: Optional[str]
    prazo_entrega_dias: Optional[int]
    ativo: bool (default=True)

class FornecedorProduto(Base):
    id: UUID (PK)
    fornecedor_id: UUID (FK → fornecedores.id)
    produto_id: UUID (FK → produtos.id)
    preco_custo: Decimal
    cod_fornecedor: Optional[str]
    principal: bool (default=False)
    UNIQUE(fornecedor_id, produto_id)
```

**Endpoints:**

```
# Categorias
POST   /categorias                    → criar
GET    /categorias                    → listar
PATCH  /categorias/{id}               → atualizar
DELETE /categorias/{id}               → deletar (impedir se tiver produtos vinculados)

# Produtos
POST   /produtos                      → criar produto + CatalogoConfig automática (visivel=False)
GET    /produtos                      → listar (filtro: categoria, ativo, nome)
GET    /produtos/{id}                 → buscar com variantes e config de catálogo
PATCH  /produtos/{id}                 → atualizar dados do produto
DELETE /produtos/{id}                 → soft delete

# Variantes
POST   /produtos/{id}/variantes       → adicionar variante (calcula preco_venda automaticamente)
PATCH  /produtos/{id}/variantes/{vid} → atualizar variante (recalcula preco_venda)
DELETE /produtos/{id}/variantes/{vid} → desativar variante

# Catálogo (admin)
PATCH  /produtos/{id}/catalogo        → publicar/ocultar, destaque, ordem, descrição pública
POST   /produtos/{id}/catalogo/fotos  → adicionar foto (url)
DELETE /produtos/{id}/catalogo/fotos/{fid} → remover foto

# Catálogo (público — sem auth)
GET    /catalogo                      → listar produtos visíveis com estoque disponível (paginado)
GET    /catalogo/{id}                 → detalhe público do produto com variantes disponíveis

# Fornecedores
POST   /fornecedores                  → criar (valida CNPJ)
GET    /fornecedores                  → listar
PATCH  /fornecedores/{id}             → atualizar
POST   /fornecedores/{id}/produtos    → vincular produto com preço de custo
DELETE /fornecedores/{id}/produtos/{pid} → desvincular
```

**Regras de negócio:**

1. `preco_venda = preco_custo * (1 + markup_pct / 100)` — calculado e salvo sempre que custo ou markup mudar
2. SKU deve ser único globalmente (não apenas por produto)
3. Ao criar produto, `CatalogoConfig` é criada automaticamente com `visivel=False`
4. Apenas 1 `FornecedorProduto` pode ter `principal=True` por produto — ao marcar um como principal, os demais são desmarcados automaticamente
5. CNPJ validado matematicamente (algoritmo dos dígitos verificadores)
6. Endpoint `/catalogo` público deve cruzar com o serviço de estoque (via HTTP interno ao `services/estoque`) para mostrar apenas variantes com `quantidade > 0`

---

### 4. Serviço de Estoque (`services/estoque/` — porta 8003)

**Modelos:**

```python
class Estoque(Base):
    id: UUID (PK)
    variante_id: UUID (UK, NOT NULL)  # referência externa — sem FK entre serviços
    quantidade: int (default=0, >= 0)
    quantidade_minima: int (default=0)
    atualizado_em: datetime

class Movimentacao(Base):
    id: UUID (PK)
    variante_id: UUID (NOT NULL)
    tipo: Enum(ENTRADA, SAIDA, AJUSTE, DEVOLUCAO)
    quantidade: int (NOT NULL, != 0)
    motivo: str
    referencia_id: Optional[UUID]     # id do pedido, ajuste manual, etc.
    criado_em: datetime (readonly — nunca editável)
```

**Endpoints:**

```
POST   /estoque                       → criar registro de estoque para variante
GET    /estoque                       → listar (filtro: variante_id, abaixo_minimo)
GET    /estoque/{variante_id}         → consultar estoque de uma variante
POST   /estoque/{variante_id}/entrada → registrar entrada de mercadoria
POST   /estoque/{variante_id}/saida   → registrar saída manual
POST   /estoque/{variante_id}/ajuste  → corrigir quantidade (inventário)
POST   /estoque/{variante_id}/devolucao → devolução de pedido
GET    /estoque/{variante_id}/movimentacoes → histórico de movimentações (paginado)
GET    /estoque/alertas/minimo        → listar variantes abaixo do mínimo
```

**Regras de negócio:**

1. `quantidade` nunca pode ser negativa — retornar 422 se `saida > quantidade_atual`
2. Toda movimentação é **imutável** após criação — nenhum endpoint de PATCH/DELETE em movimentações
3. Ao registrar entrada de produto novo via `POST /estoque`, criar registro de `Estoque` com `quantidade=0` primeiro
4. Ao dar saída (via pedido confirmado), o `referencia_id` deve ser o `pedido_id`
5. Ao atingir `quantidade <= quantidade_minima`, publicar evento `estoque.minimo` no RabbitMQ com payload:
   ```json
   {
     "variante_id": "uuid",
     "sku": "string",
     "quantidade_atual": 5,
     "quantidade_minima": 10
   }
   ```
6. Operações de entrada/saída/ajuste devem ser **transacionais** (tudo ou nada com a movimentação)

---

### 5. Serviço de Vendas (`services/vendas/` — porta 8004)

**Modelos:**

```python
class Carrinho(Base):
    id: UUID (PK, usado como token anônimo)
    cliente_id: Optional[UUID]         # null = visitante anônimo
    status: Enum(ATIVO, FINALIZADO, ABANDONADO, EXPIRADO)
    criado_em: datetime
    expira_em: datetime                # criado_em + 24h

class ItemCarrinho(Base):
    id: UUID (PK)
    carrinho_id: UUID (FK → carrinhos.id, ON DELETE CASCADE)
    variante_id: UUID (NOT NULL)       # referência externa
    quantidade: int (> 0)
    preco_unitario: Decimal            # snapshot do preço no momento

class Pedido(Base):
    id: UUID (PK)
    cliente_id: Optional[UUID]         # null = visitante anônimo
    origem: Enum(CATALOGO, BALCAO)
    nome_comprador: str                # obrigatório para anônimos
    telefone_comprador: str            # obrigatório para notificação
    modalidade_pagto: Enum(A_VISTA, FIADO)
    modalidade_entrega: Enum(RETIRADA, ENTREGA)
    status: Enum(PENDENTE, CONFIRMADO, SEPARANDO, ENVIADO, ENTREGUE, CANCELADO)
    subtotal: Decimal
    desconto: Decimal (default=0.00)
    frete: Decimal (default=0.00)
    total: Decimal
    observacao: Optional[str]
    criado_em: datetime
    atualizado_em: datetime

class ItemPedido(Base):
    id: UUID (PK)
    pedido_id: UUID (FK → pedidos.id, ON DELETE CASCADE)
    variante_id: UUID (NOT NULL)
    quantidade: int
    preco_unitario: Decimal            # snapshot imutável
    subtotal: Decimal

class EnderecoEntrega(Base):
    id: UUID (PK)
    pedido_id: UUID (FK UK → pedidos.id)
    logradouro: str
    numero: str
    complemento: Optional[str]
    bairro: str
    cidade: str
    uf: str
    cep: str

class Pagamento(Base):
    id: UUID (PK)
    pedido_id: UUID (FK UK → pedidos.id)
    metodo: Enum(DINHEIRO, PIX, CARTAO, FIADO)
    subtipo: Optional[Enum(DEBITO, CREDITO)]   # apenas para CARTAO
    valor: Decimal
    status_confirmacao: Enum(PENDENTE, CONFIRMADO, RECUSADO)
    mp_payment_id: Optional[str]               # ID retornado pelo Mercado Pago
    confirmado_em: Optional[datetime]
```

**Endpoints:**

```
# Carrinho (público — sem auth)
POST   /carrinho                      → criar carrinho → retorna {id, token}
GET    /carrinho/{token}              → consultar carrinho
POST   /carrinho/{token}/itens        → adicionar item (verifica estoque via HTTP)
PATCH  /carrinho/{token}/itens/{id}   → alterar quantidade
DELETE /carrinho/{token}/itens/{id}   → remover item
DELETE /carrinho/{token}              → abandonar carrinho

# Checkout (público)
POST   /carrinho/{token}/checkout     → finalizar compra → gera Pedido

# Pedidos (protegido)
GET    /pedidos                       → listar (filtro: status, origem, cliente_id, data)
GET    /pedidos/{id}                  → detalhe completo
PATCH  /pedidos/{id}/status           → ADMIN: avançar status manualmente
DELETE /pedidos/{id}/cancelar         → cancelar pedido (com motivo)

# Pagamentos
POST   /pagamentos/webhook/mercadopago → webhook público do MP (valida assinatura HMAC)
PATCH  /pagamentos/{pedido_id}/confirmar → ADMIN: confirmar pagamento manual (dinheiro/cartão)
```

**Regras de negócio (implementar no VendasService):**

1. **Carrinho expira em 24h** — job Celery Beat roda a cada hora verificando carrinhos expirados
2. **Adição de item ao carrinho**: verificar disponibilidade em estoque via `GET http://estoque:8003/estoque/{variante_id}` — retornar 422 se indisponível
3. **Snapshot de preço**: ao adicionar ao carrinho, salvar `preco_unitario` atual — não atualizar se o preço mudar depois
4. **Checkout — fluxo completo:**
   a. Validar carrinho (`ATIVO`, não expirado, mínimo 1 item)
   b. Se `modalidade_pagto=FIADO`:
      - Verificar `cliente_id` não é null (obrigatório)
      - Consultar cliente via HTTP: verificar `bloqueado=False` e `credito_disponivel >= total`
   c. Se `modalidade_entrega=ENTREGA`: endereço de entrega obrigatório no body
   d. Criar `Pedido` com `status=PENDENTE`
   e. Se `metodo=PIX`: chamar API do Mercado Pago → salvar `mp_payment_id` → retornar `qr_code` e `qr_code_base64` para o frontend exibir
   f. Se `metodo=DINHEIRO` ou `CARTAO`: `status_confirmacao=PENDENTE` (admin confirma)
   g. Se `metodo=FIADO`: debitar crédito do cliente via HTTP → `status_confirmacao=CONFIRMADO` → publicar evento `pedido.confirmado`
   h. Marcar carrinho como `FINALIZADO`

5. **Webhook Mercado Pago:**
   - Validar assinatura HMAC-SHA256 no header `x-signature`
   - Consultar payment status na API do MP para confirmar
   - Se `status=approved`: setar `status_confirmacao=CONFIRMADO` → publicar `pedido.confirmado` → dar baixa no estoque via HTTP
   - Se `status=rejected`: setar `status_confirmacao=RECUSADO` → cancelar pedido → publicar `pedido.cancelado`

6. **Ao confirmar pedido** (`pedido.confirmado`):
   - Dar baixa no estoque: `POST http://estoque:8003/estoque/{variante_id}/saida` para cada item
   - Se qualquer baixa falhar → rollback do pedido → retornar estoque

7. **Cancelamento:**
   - Se pedido já confirmado → devolver estoque: `POST http://estoque:8003/estoque/{variante_id}/devolucao`
   - Se modalidade era FIADO → creditar de volta no cliente via HTTP
   - Status não pode voltar atrás: ENTREGUE e CANCELADO são estados finais

---

### 6. Serviço Financeiro (`services/financeiro/` — porta 8005)

**Modelos:**

```python
class ContaReceber(Base):
    id: UUID (PK)
    cliente_id: UUID (NOT NULL)
    pedido_id: UUID (UK)               # 1 conta por pedido
    valor_original: Decimal
    valor_pago: Decimal (default=0.00)
    saldo_devedor: Decimal             # calculado: valor_original - valor_pago
    data_vencimento: date              # calculada a partir do dia_vencimento do cliente
    status: Enum(ABERTO, PARCIAL, QUITADO, VENCIDO)
    criado_em: datetime
    quitado_em: Optional[datetime]

class PagamentoFiado(Base):
    id: UUID (PK)
    conta_id: UUID (FK → contas_receber.id)
    valor: Decimal (> 0)
    forma: Enum(DINHEIRO, PIX, CARTAO)
    observacao: Optional[str]
    pago_em: datetime
```

**Endpoints:**

```
POST   /contas                         → criar conta (chamado internamente pelo serviço de vendas)
GET    /contas                         → listar (filtro: cliente_id, status, vencimento)
GET    /contas/{id}                    → detalhe com histórico de pagamentos
GET    /contas/cliente/{cliente_id}    → todas as contas de um cliente
POST   /contas/{id}/pagamentos         → registrar pagamento parcial ou total
GET    /contas/vencer                  → contas que vencem nos próximos N dias (param)
GET    /contas/vencidas                → contas com status VENCIDO
PATCH  /contas/{id}/marcar-vencida    → (chamado pelo job Celery Beat)
```

**Regras de negócio:**

1. `data_vencimento` calculada assim: se `dia_vencimento=10` e pedido criado em 15/01, vencimento = 10/02
2. `saldo_devedor = valor_original - valor_pago` — recalcular a cada pagamento
3. Ao registrar pagamento:
   - Se `valor >= saldo_devedor`: status → `QUITADO`, `quitado_em = now()`
   - Senão: status → `PARCIAL`
   - Creditar no cliente via HTTP: `PATCH http://clientes:8001/clientes/{id}/credito` com `delta = valor_pago`
4. **Job Celery Beat diário (00:00):**
   - Buscar contas com `data_vencimento < hoje` e `status IN (ABERTO, PARCIAL)` → marcar como `VENCIDO`
   - Verificar cada cliente: se `credito_disponivel == 0` E tem conta `VENCIDO` → `bloquear=True` via HTTP
   - Publicar evento `cobranca.vencida` para cada conta vencida com `{conta_id, cliente_id, cliente_telefone, saldo_devedor}`
5. **Job Celery Beat (3 dias antes do vencimento):**
   - Buscar contas que vencem em exatamente 3 dias → publicar evento `cobranca.lembrete`

---

### 7. Serviço de Notificações (`services/notificacoes/` — porta 8006)

**Modelo:**

```python
class Notificacao(Base):
    id: UUID (PK)
    tipo: Enum(PEDIDO_CONFIRMADO, PEDIDO_CANCELADO, ESTOQUE_MINIMO,
               COBRANCA_LEMBRETE, COBRANCA_VENCIDA, CONTA_QUITADA)
    destinatario: str                  # número telefone E.164
    mensagem: str
    status: Enum(PENDENTE, ENVIADO, FALHOU)
    tentativas: int (default=0)
    criado_em: datetime
```

**Consumer events (RabbitMQ — exchange: `erp.events`, tipo: topic):**

| Routing key | Ação |
|---|---|
| `pedido.confirmado` | WPP pro comprador: "Seu pedido #X foi confirmado!" |
| `pedido.cancelado` | WPP pro comprador: "Seu pedido #X foi cancelado." |
| `estoque.minimo` | WPP pro responsável (TELEFONE_RESPONSAVEL do .env): alerta |
| `cobranca.lembrete` | WPP pro cliente: "Olá! Seu pagamento de R$X vence em 3 dias." |
| `cobranca.vencida` | WPP pro cliente: "Seu pagamento de R$X está vencido." |
| `conta.quitada` | WPP pro cliente: confirmação de quitação |

**Regras:**
1. Retry automático: máximo 5 tentativas com backoff de 30s, 60s, 120s, 300s, 600s
2. Após 5 falhas: status → `FALHOU`, não tenta mais
3. Deduplicação: usar Redis com TTL de 1h para evitar reenvio duplicado (key: `notif:{tipo}:{referencia_id}`)
4. Salvar histórico de toda notificação tentada (sucesso ou falha) no PostgreSQL

**Endpoint:**
```
GET    /notificacoes                   → listar histórico (filtro: status, tipo, destinatario)
POST   /notificacoes/{id}/reenviar     → ADMIN: forçar reenvio de uma notificação falha
```

---

## Docker Compose — gerar completo

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

## .env.example — gerar completo

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
```

---

## Padrões de código obrigatórios

### database.py (padrão para todos os serviços):
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

### Repository pattern (padrão):
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

### Tratamento de erros (padrão para todos os routers):
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

### Schema de resposta padrão (Pydantic v2):
```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int
```

### Logging estruturado (JSON):
```python
import structlog
log = structlog.get_logger()
# Usar em todo service: log.info("cliente.criado", cliente_id=str(id), cpf_hash=hash)
# NUNCA logar CPF, telefone ou dados pessoais em plain text
```

---

## Testes — padrão pytest

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

## Makefile — gerar com atalhos:

```makefile
up:          docker-compose up -d
down:        docker-compose down
logs:        docker-compose logs -f
migrate:     # roda alembic upgrade head em todos os serviços
test:        # roda pytest em todos os serviços com coverage
lint:        # ruff + mypy em todos os serviços
seed:        # popula banco com dados de teste
```

---

## Regras de negócio complementares — decisões finais de MVP

### Desconto
- **Não existe desconto no MVP.** O campo `desconto` nos modelos deve existir na estrutura (para uso futuro), mas sempre persistido como `0.00`.
- Nenhum endpoint deve aceitar desconto no body — ignorar se enviado.
- O `total` do pedido é sempre `subtotal + frete` (sem desconto).

### Frete
- Frete é **definido manualmente pelo admin por pedido**.
- No checkout (cliente), o campo `frete` não é enviado — nasce como `0.00`.
- O admin ajusta o frete via `PATCH /pedidos/{id}/frete` antes de confirmar o pedido.
- Regra: frete só pode ser alterado enquanto `status = PENDENTE`.
- O `total` é recalculado automaticamente após ajuste do frete: `total = subtotal + frete`.
- Adicionar endpoint no serviço de vendas:
  ```
  PATCH /pedidos/{id}/frete   → ADMIN: define valor do frete (apenas status PENDENTE)
                                body: { "frete": 8.50 }
                                retorna pedido com total recalculado
  ```

### Troco (pagamento em dinheiro)
- No checkout, quando `metodo = DINHEIRO`, o body deve incluir `valor_recebido: Decimal`.
- Regra: `valor_recebido >= total` — retornar 422 se menor.
- O sistema calcula e retorna `troco = valor_recebido - total` na resposta do checkout.
- Salvar `valor_recebido` e `troco` no modelo `Pagamento`:
  ```python
  class Pagamento(Base):
      ...
      valor_recebido: Optional[Decimal]   # apenas para DINHEIRO
      troco: Optional[Decimal]            # calculado: valor_recebido - total
  ```
- O troco nunca é negativo — validar no `PagamentoService`.

### Devolução
- **Não existe fluxo de devolução no MVP.**
- O endpoint `POST /estoque/{variante_id}/devolucao` **não deve ser implementado**.
- Remover referências a devolução nos fluxos de cancelamento — ao cancelar pedido já confirmado, o estoque **não é devolvido automaticamente** no MVP (ajuste manual pelo admin via `POST /estoque/{variante_id}/ajuste`).
- O tipo `DEVOLUCAO` em `TipoMovimento` deve existir no enum para uso futuro, mas sem endpoint que o acione.

---

## pgAdmin — configuração automática completa

### Adicionar ao docker-compose.yml:

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
```

### Gerar arquivo `pgadmin/servers.json` — conexões pré-configuradas:

Este arquivo é montado automaticamente no container do pgAdmin na inicialização, importando todas as conexões sem nenhuma configuração manual.

```json
{
  "Servers": {
    "1": {
      "Name": "ERP · Clientes",
      "Group": "Runas ERP",
      "Host": "db-clientes",
      "Port": 5432,
      "MaintenanceDB": "clientes",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Clientes"
    },
    "2": {
      "Name": "ERP · Produtos",
      "Group": "Runas ERP",
      "Host": "db-produtos",
      "Port": 5432,
      "MaintenanceDB": "produtos",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Produtos e Catálogo"
    },
    "3": {
      "Name": "ERP · Estoque",
      "Group": "Runas ERP",
      "Host": "db-estoque",
      "Port": 5432,
      "MaintenanceDB": "estoque",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Estoque e Movimentações"
    },
    "4": {
      "Name": "ERP · Vendas",
      "Group": "Runas ERP",
      "Host": "db-vendas",
      "Port": 5432,
      "MaintenanceDB": "vendas",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Vendas, Pedidos e Carrinho"
    },
    "5": {
      "Name": "ERP · Financeiro",
      "Group": "Runas ERP",
      "Host": "db-financeiro",
      "Port": 5432,
      "MaintenanceDB": "financeiro",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço Financeiro e Contas a Receber"
    },
    "6": {
      "Name": "ERP · Notificações",
      "Group": "Runas ERP",
      "Host": "db-notificacoes",
      "Port": 5432,
      "MaintenanceDB": "notificacoes",
      "Username": "erp",
      "PassFile": "/pgpass",
      "SSLMode": "prefer",
      "Comment": "Banco do serviço de Notificações WhatsApp"
    },
    "7": {
      "Name": "ERP · Evolution API",
      "Group": "Runas ERP",
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

### Gerar arquivo `pgadmin/pgpass` — senhas automáticas (sem digitar senha no pgAdmin):

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

**IMPORTANTE:** O arquivo `pgpass` deve ter permissão `0600`. Adicionar ao `docker-compose.yml` um entrypoint que corrija isso automaticamente:

```yaml
  pgadmin:
    ...
    entrypoint: >
      /bin/sh -c "
        chmod 600 /pgpass &&
        /entrypoint.sh
      "
```

### Adicionar ao .env.example:

```env
# pgAdmin
PGADMIN_EMAIL=admin@runas.local
PGADMIN_PASSWORD=admin123
```

### Acesso após `docker-compose up`:
- URL: `http://localhost:5050`
- Email: valor de `PGADMIN_EMAIL`
- Senha: valor de `PGADMIN_PASSWORD`
- Todos os 7 bancos já aparecem conectados no grupo **"Runas ERP"** sem nenhuma ação manual

---

## Automação de migrations e inicialização — tudo automático no `docker-compose up`

### Estratégia: Migration Runner como serviço de inicialização

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

### Gerar `scripts/migrate.Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install alembic asyncpg sqlalchemy
COPY scripts/run_migrations.sh /run_migrations.sh
RUN chmod +x /run_migrations.sh
CMD ["/run_migrations.sh"]
```

### Gerar `scripts/run_migrations.sh` — script que roda todas as migrations:

```bash
#!/bin/bash
set -e   # aborta se qualquer migration falhar

echo "🔄 Iniciando migrations do ERP Runas..."

SERVICOS=("clientes" "produtos" "estoque" "vendas" "financeiro" "notificacoes")

for servico in "${SERVICOS[@]}"; do
  echo "📦 Aplicando migrations: $servico"
  cd /app/$servico
  alembic upgrade head
  echo "✅ $servico — migrations aplicadas com sucesso"
done

echo "🎉 Todas as migrations concluídas!"
```

### Dependência dos serviços no migrate (aplicar a todos):

```yaml
  clientes:
    depends_on:
      migrate:   { condition: service_completed_successfully }
      rabbitmq:  { condition: service_healthy }
      redis:     { condition: service_healthy }
  # repetir para produtos, estoque, vendas, financeiro, notificacoes
```

---

## Automação de seed — dados iniciais obrigatórios

### Gerar `scripts/seed.py` — executado via `make seed` ou automaticamente em ambiente dev:

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

### Adicionar ao `.env.example`:

```env
# Seed / Admin inicial
ADMIN_EMAIL=admin@runas.local
ADMIN_PASSWORD=admin123
```

---

## Automação de infraestrutura — o que deve acontecer automaticamente no `docker-compose up`

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

### Health checks obrigatórios para todos os bancos no docker-compose:

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

### Health checks para RabbitMQ e Redis:

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

## Makefile — versão completa atualizada

```makefile
.PHONY: up down logs migrate seed shell test lint reset

# Sobe tudo (migrations rodam automaticamente antes dos serviços)
up:
	docker-compose up -d
	@echo "✅ ERP Runas rodando"
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

## Restrições e observações finais

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

