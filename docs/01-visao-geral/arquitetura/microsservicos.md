# Detalhamento dos Microsserviços - Runas

> **Especificação completa de cada microsserviço:** modelos, endpoints e regras de negócio

**Última atualização**: 26 de Junho de 2026  
**Sistema atual**: 8 serviços (1 Gateway + 7 microsserviços)

---

## 1. API Gateway (`api-gateway/` — porta 8000)

### Responsabilidades
- Receber todas as requisições externas
- Autenticação JWT e OAuth2 (Google, Microsoft)
- Rotear para o serviço correto via HTTP interno
- Rate limiting por IP
- Log estruturado de todas as requisições (JSON)
- Gestão de usuários admin e clientes OAuth

### Endpoints de Autenticação

**Admin**:
```
POST /auth/login          → OAuth2 password flow → retorna access_token + refresh_token
POST /auth/refresh        → renova access_token via refresh_token
POST /auth/logout         → invalida refresh_token (Redis blacklist)
POST /auth/register       → registro de novos usuários admin
POST /auth/password-reset → recuperação de senha
```

**Cliente (OAuth)**:
```
GET  /auth/google         → inicia fluxo OAuth Google
GET  /auth/microsoft      → inicia fluxo OAuth Microsoft  
GET  /auth/callback       → callback OAuth providers
POST /auth/cliente/logout → logout de cliente OAuth
```

### Regras de JWT
- `access_token`: expira em 30 minutos
- `refresh_token`: expira em 7 dias, salvo no Redis
- Payload do token deve conter: `sub` (user_id), `role` (ADMIN|OPERADOR), `exp`, `iat`
- Algoritmo: HS256

### Modelos de Usuário

```python
class Usuario(Base):
    id: UUID
    nome: str
    email: str          # unique
    senha_hash: str     # bcrypt via passlib
    role: Enum(ADMIN, GERENTE, VENDEDOR, OPERADOR)
    empresa_id: UUID    # FK para empresas
    ativo: bool
    criado_em: datetime

class ClienteAuth(Base):
    id: UUID
    email: str          # unique
    nome: str
    provider: Enum(GOOGLE, MICROSOFT)
    provider_user_id: str
    ativo: bool
    criado_em: datetime
```

---

## 2. Serviço de Empresas (`services/empresas/` — porta 8001)

### Responsabilidades
- **Multi-tenancy**: Gestão de empresas/tenants
- CRUD de empresas
- Isolamento de dados por empresa_id
- Configurações por empresa
- Slug único por empresa (usado em URLs públicas)

### Modelo

```python
class Empresa(Base):
    id: UUID (PK)
    razao_social: str
    nome_fantasia: str
    cnpj: str (UK, validado)
    slug: str (UK)              # ex: "loja-do-joao"
    telefone: str
    email: str
    logo_url: Optional[str]
    ativo: bool (default=True)
    criado_em: datetime
```

### Endpoints

```
POST   /empresas                      → criar empresa (valida CNPJ único)
GET    /empresas                      → listar empresas
GET    /empresas/{id}                 → buscar por ID
GET    /empresas/slug/{slug}          → buscar por slug (usado na loja online)
PATCH  /empresas/{id}                 → atualizar dados
DELETE /empresas/{id}                 → soft delete (ativo=False)
```

### Regras de Negócio

1. CNPJ validado matematicamente (algoritmo dos dígitos verificadores)
2. Slug deve ser único e lowercase, sem espaços (ex: "loja-do-joao")
3. Ao criar empresa, criar automaticamente schemas PostgreSQL para cada serviço
4. Empresas desativadas não podem ter usuários ativos
5. Verificar dependências antes de desativar (usuários, clientes, produtos, etc)

---

## 3. Serviço de Clientes (`services/clientes/` — porta 8002)

### Modelos

```python
class Cliente(Base):
    id: UUID (PK)
    empresa_id: UUID (NOT NULL)        # Multi-tenancy
    cpf: str (NOT NULL, validado)
    nome: str
    telefone: str (NOT NULL)
    email: Optional[str]
    data_nasc: Optional[date]
    limite_credito: Decimal (default=0.00)
    credito_disponivel: Decimal (default=0.00)
    dia_vencimento: Optional[int]  # 1-28
    bloqueado: bool (default=False)
    ativo: bool (default=True)
    criado_em: datetime
    UNIQUE(empresa_id, cpf)            # CPF único por empresa

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

### Endpoints

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

### Regras de Negócio

1. CPF deve ser validado matematicamente (algoritmo dos dígitos verificadores)
2. Ao definir `limite_credito`, `credito_disponivel` = `limite_credito` − `saldo_devedor_atual`
3. `credito_disponivel` nunca pode ser negativo
4. `bloqueado=True` quando saldo vencido E `credito_disponivel == 0`
5. `dia_vencimento` aceita apenas valores entre 1 e 28
6. Telefone deve estar no formato E.164 (ex: +5511999999999) — validar e normalizar
7. Ao desativar (soft delete), verificar se cliente tem pedidos em aberto ou contas pendentes — se sim, impedir e retornar erro 409

---

## 4. Serviço de Produtos (`services/produtos/` — porta 8003)

### Modelos

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

### Endpoints

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

### Regras de Negócio

1. `preco_venda = preco_custo * (1 + markup_pct / 100)` — calculado e salvo sempre que custo ou markup mudar
2. SKU deve ser único globalmente (não apenas por produto)
3. Ao criar produto, `CatalogoConfig` é criada automaticamente com `visivel=False`
4. Apenas 1 `FornecedorProduto` pode ter `principal=True` por produto — ao marcar um como principal, os demais são desmarcados automaticamente
5. CNPJ validado matematicamente (algoritmo dos dígitos verificadores)
6. Endpoint `/catalogo` público deve cruzar com o serviço de estoque (via HTTP interno ao `services/estoque`) para mostrar apenas variantes com `quantidade > 0`

---

## 5. Serviço de Estoque (`services/estoque/` — porta 8004)

### Modelos

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

### Endpoints

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

### Regras de Negócio

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

## 6. Serviço de Vendas (`services/vendas/` — porta 8007)

### Modelos

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
    valor_recebido: Optional[Decimal]          # apenas para DINHEIRO
    troco: Optional[Decimal]                   # calculado: valor_recebido - total
```

### Endpoints

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
PATCH  /pedidos/{id}/frete            → ADMIN: define valor do frete (apenas status PENDENTE)
DELETE /pedidos/{id}/cancelar         → cancelar pedido (com motivo)

# Pagamentos
POST   /pagamentos/webhook/mercadopago → webhook público do MP (valida assinatura HMAC)
PATCH  /pagamentos/{pedido_id}/confirmar → ADMIN: confirmar pagamento manual (dinheiro/cartão)
```

### Regras de Negócio

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

8. **Desconto:**
   - Não existe desconto no MVP
   - Campo `desconto` sempre persistido como `0.00`
   - Nenhum endpoint aceita desconto no body

9. **Frete:**
   - Definido manualmente pelo admin por pedido
   - No checkout, `frete` nasce como `0.00`
   - Admin ajusta via `PATCH /pedidos/{id}/frete` (apenas status PENDENTE)
   - `total` recalculado automaticamente: `total = subtotal + frete`

10. **Troco (pagamento em dinheiro):**
    - No checkout com `metodo=DINHEIRO`, body deve incluir `valor_recebido`
    - Regra: `valor_recebido >= total` (retornar 422 se menor)
    - Sistema calcula e retorna `troco = valor_recebido - total`
    - Troco nunca é negativo

---

## 7. Serviço Financeiro (`services/financeiro/` — porta 8005)

### Modelos

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

### Endpoints

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

### Regras de Negócio

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

## 8. Serviço de Notificações (`services/notificacoes/` — porta 8006)

### Modelo

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

### Consumer Events (RabbitMQ)

**Exchange:** `erp.events` (tipo: topic)

| Routing key | Ação |
|---|---|
| `pedido.confirmado` | WPP pro comprador: "Seu pedido #X foi confirmado!" |
| `pedido.cancelado` | WPP pro comprador: "Seu pedido #X foi cancelado." |
| `estoque.minimo` | WPP pro responsável (TELEFONE_RESPONSAVEL do .env): alerta |
| `cobranca.lembrete` | WPP pro cliente: "Olá! Seu pagamento de R$X vence em 3 dias." |
| `cobranca.vencida` | WPP pro cliente: "Seu pagamento de R$X está vencido." |
| `conta.quitada` | WPP pro cliente: confirmação de quitação |

### Regras de Negócio

1. Retry automático: máximo 5 tentativas com backoff de 30s, 60s, 120s, 300s, 600s
2. Após 5 falhas: status → `FALHOU`, não tenta mais
3. Deduplicação: usar Redis com TTL de 1h para evitar reenvio duplicado (key: `notif:{tipo}:{referencia_id}`)
4. Salvar histórico de toda notificação tentada (sucesso ou falha) no PostgreSQL

### Endpoint

```
GET    /notificacoes                   → listar histórico (filtro: status, tipo, destinatario)
POST   /notificacoes/{id}/reenviar     → ADMIN: forçar reenvio de uma notificação falha
```

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Junho de 2026  
**Versão:** 2.0.0  
**Status**: 8 serviços operacionais (Gateway + Empresas + Clientes + Produtos + Estoque + Vendas + Financeiro + Notificações)
