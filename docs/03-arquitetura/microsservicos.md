# Detalhamento dos Microsserviços - Runas

> **Resumo de cada serviço: porta, modelos, endpoints e regras que o código de fato implementa**

**Verificado contra o código em 2026-09-26.** Sistema: 8 serviços de aplicação (1 Gateway + 7
microsserviços). Fontes: `services/*/routers/`, `services/*/models/`, `api-gateway/`.
Onde o código não permite afirmar, o texto diz `A CONFIRMAR`.

Contratos completos de request/response não estão aqui: use o OpenAPI de cada serviço
(`/docs`, quando habilitado) ou os schemas em `services/*/schemas/`.

## Portas

Fonte: `EXPOSE` e `CMD uvicorn --port` em `services/*/Dockerfile` e `api-gateway/Dockerfile`;
o `docker-compose.dev.yml` usa as mesmas nos `command:`. O healthcheck do
`docker-compose.prod.yml` bate nas mesmas portas.

| Serviço | Porta | Estado |
|---|---|---|
| api-gateway | 8000 | implementado |
| clientes | 8001 | implementado |
| produtos | 8002 | implementado |
| estoque | 8003 | implementado |
| vendas | 8004 | implementado |
| financeiro | 8005 | esqueleto (só `/health`) |
| notificacoes | 8006 | esqueleto (só `/health`) |
| empresas | 8007 | implementado |

## Convenções comuns aos serviços

- **IDs**: `empresas.id` é inteiro (autoincrement); demais tabelas usam UUID. `empresa_id` é
  sempre inteiro.
- **Tenant**: os serviços não validam JWT. Confiam no header `X-Empresa-Id` injetado pelo
  gateway (ver `comunicacao.md`); sem o header a rota é rejeitada (400 em `empresas`).
- **Origem interna**: `X-Servico-Interno-Token` validado em `services/*/interno.py`
  (fail-open enquanto o segredo não estiver em todos os containers).
- **Banco**: um PostgreSQL, um schema por serviço; isolamento entre tenants por coluna
  `empresa_id` (`UniqueConstraint` costuma incluir `empresa_id`).
- **Eventos RabbitMQ**: cada serviço tem `events/publisher.py`, mas nenhum código publica ou
  consome (ver `comunicacao.md`). Onde este documento antes descrevia "publicar evento X",
  isso **não acontece**.
- **Jobs**: não há Celery em uso. O único agendamento no código são dois loops asyncio dentro
  do processo do serviço vendas (ver seção 5).

---

## 1. API Gateway (`api-gateway/` — porta 8000)

### Responsabilidades
- Único ponto de entrada externo; roteia por prefixo (`ServiceProxy.SERVICE_URLS` em
  `api-gateway/proxy/service_proxy.py`)
- Autenticação JWT de usuários (admin/operador) e de compradores (login próprio e OAuth
  Google/Microsoft)
- RBAC (`require_admin`, `require_super_admin`, `require_admin_or_operador` em `auth/oauth2.py`)
- Injeta `X-Empresa-Id`/`X-Cliente-Id` e descarta os mesmos headers vindos do cliente
- Rate limiting por IP: 300/min por padrão, limite mais apertado em login/registro/reset
  (`middleware/rate_limit.py`)
- Log estruturado (`logging_middleware.py`), auditoria de escritas
  (`auditoria_middleware.py`) e 402 na escrita de tenant inadimplente
  (`inadimplencia_middleware.py`)
- Idempotência por `Idempotency-Key` (`proxy/idempotency.py`)

### Prefixos roteados

`/clientes`, `/produtos`, `/categorias`, `/variantes`, `/fornecedores`, `/loja-online`,
`/estoque`, `/loja`, `/carrinho`, `/pagamentos`, `/integracoes`, `/contas`,
`/notificacoes`, `/empresas`. **Não há prefixo `/vendas` nem `/admin/entrega`** no proxy
externo: essas rotas do serviço vendas (seção 5) só são alcançadas direto no serviço.
`A CONFIRMAR`: como o frontend chega em `/vendas` (o `Sidebar.tsx` aponta para `/vendas`,
mas é rota de tela, não prova de rota de API).

### Endpoints de autenticação

**Usuários** (`routers/auth.py`, prefixo `/auth`):
```
GET  /auth/me
POST /auth/login             → OAuth2 password flow; retorna access_token + refresh_token e seta cookies HTTP-only
POST /auth/refresh           → novo access_token a partir do refresh_token
POST /auth/logout            → blacklist do access token, apaga refresh:{user_id}, limpa cookies
POST /auth/forgot-password   → limite 5/min
POST /auth/reset-password
POST /auth/alterar-senha
```

**Administração de usuários da empresa** (`routers/auth_admin.py`, prefixo `/auth/admin`):
```
GET    /auth/admin/usuarios
POST   /auth/admin/usuarios
PUT    /auth/admin/usuarios/{user_id}
DELETE /auth/admin/usuarios/{user_id}
```

**Compradores** (`routers/auth_cliente.py`, prefixo `/auth/cliente`):
```
POST /auth/cliente/register
POST /auth/cliente/login
POST /auth/cliente/logout
POST /auth/cliente/oauth/google/init        e  /oauth/google/callback
POST /auth/cliente/oauth/microsoft/init     e  /oauth/microsoft/callback
POST /auth/cliente/registrar-interno        → uso interno (vendas), protegido por REGISTRO_INTERNO_TOKEN
```

O OAuth Google/Microsoft existe **apenas para compradores**. Não há `POST /auth/register`,
`GET /auth/google` nem `GET /auth/callback`.

**Plataforma** (`routers/plataforma.py`, prefixo `/plataforma`, só `SUPER_ADMIN`):
`GET|POST /tenants`, `PATCH /tenants/{id}/suspender|reativar|plano`,
`GET /tenants/{id}/auditoria|exportar|dumps`, `POST|DELETE /tenants/{id}/assinatura`,
`POST /auditoria/{registro_id}/reverter`. Públicos (sem JWT): `POST /plataforma/webhook/mercadopago`
e `POST /plataforma/jobs/regua` (protegido por `PLATAFORMA_JOB_TOKEN`).
Detalhe em [`plataforma.md`](plataforma.md).

### Regras de JWT (`auth/jwt.py`, `config.py`)
- `access_token`: expira em `ACCESS_TOKEN_EXPIRE_MINUTES` (padrão **30**)
- `refresh_token`: expira em `REFRESH_TOKEN_EXPIRE_DAYS` (padrão **7**); o logout apaga a chave
  `refresh:{user_id}` no Redis
- Payload do access token: `sub`, `role`, `user_type`, `exp`, `iat`; para compradores, também
  `empresa_id` e `cliente_id`
- Algoritmo: `HS256` (padrão em `ALGORITHM`)
- Roles (`RoleEnum`): `SUPER_ADMIN`, `ADMIN`, `OPERADOR`. Comprador usa `role = "CLIENTE"`.

### Modelos (schema `gateway`)

```python
class Usuario(Base):            # gateway.usuarios
    id: UUID
    nome: str
    email: str                  # unique
    senha_hash: str             # bcrypt via passlib
    role: Enum(SUPER_ADMIN, ADMIN, OPERADOR)
    ativo: bool
    empresa_id: int | None      # None = SUPER_ADMIN, sem tenant
    criado_em: datetime

class ClienteAuth(Base):        # gateway.clientes_auth
    id: UUID
    email: str                  # unique
    senha_hash: str             # vazio para OAuth
    cliente_id: UUID            # unique; id do cliente no serviço clientes
    empresa_id: int             # loja onde se cadastrou
    ativo: bool
    criado_em: datetime
```

---

## 2. Serviço de Empresas (`services/empresas/` — porta 8007)

Pivô do multi-tenant: cada empresa é um tenant. Detalhe do contrato de plataforma em
[`plataforma.md`](plataforma.md) e [`comunicacao.md`](comunicacao.md).

### Responsabilidades
- Cadastro de empresas/tenants (CNPJ e slug únicos)
- Configuração por empresa: catálogo público, tema (cores/logo), plano e limites

### Modelo (`empresas.empresas`, resumo)

```python
class Empresa(Base):
    id: int (PK, autoincrement)
    slug: str (UK, max 100)            # URL pública da loja
    razao_social: str
    nome_fantasia: str
    tipo: Enum(MATRIZ, FILIAL)         # default MATRIZ
    status: Enum(ATIVA, INATIVA, SUSPENSA)
    cnpj: str (UK, formatado XX.XXX.XXX/XXXX-XX)
    inscricao_estadual, inscricao_municipal: Optional[str]
    regime_tributario: Enum(SIMPLES_NACIONAL, LUCRO_PRESUMIDO, LUCRO_REAL, MEI)
    cep, logradouro, numero, complemento, bairro, cidade, uf   # endereço
    telefone, celular, email, site: Optional[str]
    logo_url, cor_primaria, cor_secundaria: Optional[str]
    catalogo_ativo: bool; catalogo_titulo, catalogo_descricao, catalogo_whatsapp
    plano: str (default "BASICO"); max_usuarios: int (default 5)
    max_produtos: Optional[int]; max_lojas: int (default 1)
    empresa_matriz_id: Optional[int]
    ativo: bool (default True); criado_em, atualizado_em; criado_por, atualizado_por
```

### Endpoints (`routers/empresas.py`, prefixo `/empresas`)

```
POST   /empresas                    → criar empresa            [plataforma]
GET    /empresas                    → lista só a empresa do chamador (paginação skip/limit; filtros busca, tipo, status, uf)   [tenant]
GET    /empresas/{id}               → buscar por ID (só a própria empresa; senão 403)   [tenant]
GET    /empresas/slug/{slug}        → buscar por slug (só a própria empresa)   [tenant]
GET    /empresas/publico/{slug}     → info pública para o catálogo (sem X-Empresa-Id)
PUT    /empresas/{id}               → atualizar dados (só a própria empresa)   [tenant]
DELETE /empresas/{id}               → soft delete (ativo=False; retorna a empresa)   [tenant]
PATCH  /empresas/{id}/plano         → plano, limites e status   [plataforma]
GET    /empresas/plataforma/todas   → lista todos os tenants    [plataforma]
```

`[tenant]` exige `X-Empresa-Id` (400 sem ele). `[plataforma]` exige `X-Plataforma: 1` e
`X-Plataforma-Token` (só o router `/plataforma` do gateway injeta). Não existe `PATCH /empresas/{id}`
genérico: a atualização é `PUT`.

### Regras de negócio (`services/empresa_service.py`)

1. CNPJ validado por dígitos verificadores (`validate-docbr`) e único; CNPJ de empresa
   **inativa** já cadastrada reativa o registro em vez de falhar.
2. Slug em kebab-case minúsculo (`schemas/empresa.py`); se omitido na criação, é gerado a
   partir do `nome_fantasia` com sufixo numérico em caso de conflito; slug duplicado → 409.
3. Filial exige `empresa_matriz_id` de uma matriz existente e respeita `max_lojas` da matriz.
   `A CONFIRMAR`: se filiais são usadas de fato; o docstring de `listar_empresas` diz
   "cada empresa tem uma única loja (sem matriz/filial)".
4. Desativar **não** verifica dependências: o serviço tem `TODO: Validar se não tem dados
   dependentes` e desativa direto. Também não há checagem de usuários ativos.
5. Criar empresa **não** cria schemas de outros serviços: os schemas nascem em
   `postgres/init-schemas.sql` (dev) e no `db-init` do `docker-compose.prod.yml`.

---

## 3. Serviço de Clientes (`services/clientes/` — porta 8001)

### Modelos (schema `clientes`)

```python
class Cliente(Base):
    id: UUID (PK)
    empresa_id: int (NOT NULL)          # multi-tenancy
    cpf: str | None                     # opcional (clientes OAuth)
    nome: str
    telefone: str | None
    email: str | None
    data_nasc: date | None
    limite_credito: Decimal (default 0.00)
    credito_disponivel: Decimal (default 0.00)
    dia_vencimento: int | None
    bloqueado: bool (default False)
    ativo: bool (default True)
    criado_em: datetime
    UNIQUE(empresa_id, cpf)

class Endereco(Base):
    id: UUID (PK)
    cliente_id: UUID (FK → clientes.clientes.id, ON DELETE CASCADE)
    cep, logradouro, numero, complemento, bairro, cidade, uf (2 chars), principal: bool
```

### Endpoints (`routers/clientes.py`, `routers/enderecos.py`)

```
POST   /clientes                          → criar (CPF duplicado ativo → 409; inativo → reativa)
POST   /clientes/oauth                    → criar/obter cliente vindo de login OAuth
GET    /clientes                          → listar
GET    /clientes/{id}                     → buscar por id
GET    /clientes/{id}/completo            → cliente com endereços
GET    /clientes/cpf/{cpf}                → buscar por CPF
PATCH  /clientes/{id}                     → atualizar parcialmente
DELETE /clientes/{id}                     → soft delete (ativo=False)
POST   /clientes/{id}/ativar              → reativar

POST   /clientes/{id}/enderecos           → adicionar endereço
GET    /clientes/{id}/enderecos           → listar
PATCH  /clientes/{id}/enderecos/{eid}     → atualizar
DELETE /clientes/{id}/enderecos/{eid}     → remover

PUT    /clientes/{id}/credito             → define limite_credito e dia_vencimento
POST   /clientes/{id}/credito/ajustar     → ajusta credito_disponivel por delta
POST   /clientes/{id}/bloquear
POST   /clientes/{id}/desbloquear
```

O gateway ainda expõe `GET|PATCH /clientes/me` (comprador autenticado).
**Não existe** `GET /clientes/{id}/historico-credito`.

### Regras de negócio

1. CPF validado por dígitos verificadores (`validate-docbr`) e único por empresa.
2. Telefone normalizado para E.164 no schema.
3. `dia_vencimento` aceita 1 a 28 (`Field(ge=1, le=28)`).
4. `credito_disponivel` nunca fica negativo: `POST /credito/ajustar` responde 400 quando o
   delta o tornaria negativo.
5. **Definir crédito ainda não considera dívida**: `credito_disponivel` recebe o
   `limite_credito` inteiro (`saldo_devedor` fixo em 0; `TODO: Buscar saldo devedor do serviço
   financeiro`).
6. **Não há bloqueio automático por inadimplência**: `bloqueado` só muda pelos endpoints
   `bloquear`/`desbloquear`.
7. Desativar **não** verifica pedidos em aberto nem contas pendentes (`TODO` no serviço) e não
   retorna 409 por isso.

---

## 4. Serviço de Produtos (`services/produtos/` — porta 8002)

### Modelos (schema `produtos`, resumo)

```python
class Categoria:  id UUID, empresa_id int, nome (UK por empresa), descricao
class Produto:    id UUID, empresa_id, categoria_id, nome, descricao, codigo_barras (UK por empresa),
                  sku, unidade_medida ("UN"), preco, custo, preco_promocional, promocao_fim,
                  estoque_minimo, estoque_maximo, peso_bruto, peso_liquido, ativo, criado_em, deletado_em
class Variante:   id UUID, empresa_id, produto_id (FK, CASCADE), sku (UK por empresa),
                  preco_custo (> 0), markup_pct (>= 0), preco_venda (calculado e gravado), ativo
class AtributoVariante: id, variante_id (FK), chave, valor
class Fornecedor: id UUID, empresa_id, nome, cnpj (UK por empresa), email, telefone, endereco, cidade, uf, ativo
class FornecedorProduto: id, fornecedor_id, produto_id, codigo_fornecedor, preco_fornecedor,
                  prazo_entrega_dias, quantidade_minima, ativo
class LojaOnlineConfig: id, produto_id, visivel (default False), destaque, ordem_exibicao, descricao_publica
class LojaOnlineFoto:   id, produto_id, url, ordem
```

### Endpoints (`routers/produtos.py`)

```
# Categorias — /categorias
POST /categorias    GET /categorias    GET /categorias/{id}    PUT /categorias/{id}    DELETE /categorias/{id}

# Produtos — /produtos
POST /produtos    GET /produtos    GET /produtos/{id}    PUT /produtos/{id}    DELETE /produtos/{id}
GET  /produtos/categoria/{categoria_id}    GET /produtos/buscar/nome    PATCH /produtos/{id}/restaurar

# Variantes — /variantes
POST /variantes    GET /variantes/{id}    GET /variantes/produto/{produto_id}
PUT  /variantes/{id}    DELETE /variantes/{id}

# Loja online (admin) — /loja-online
POST /loja-online/config    GET /loja-online/config/{produto_id}    PUT /loja-online/config/{config_id}
GET  /loja-online/produtos    PUT /loja-online/produtos/{produto_id}/publicar
POST /loja-online/fotos    GET /loja-online/fotos/{produto_id}
PUT  /loja-online/fotos/{foto_id}    DELETE /loja-online/fotos/{foto_id}

# Público (sem auth) — /loja-online/publico e /catalogo-publico
GET /loja-online/publico/produtos    GET /loja-online/publico/categorias
GET /loja-online/publico/produto/{produto_id}    GET /catalogo-publico/produto/{produto_id}

# Fornecedores — /fornecedores e /fornecedor-produtos
POST /fornecedores    GET /fornecedores    GET /fornecedores/{id}    PUT /fornecedores/{id}    DELETE /fornecedores/{id}
POST /fornecedor-produtos    GET /fornecedor-produtos/{vinculo_id}
GET  /fornecedor-produtos/produto/{produto_id}    GET /fornecedor-produtos/fornecedor/{fornecedor_id}
PUT  /fornecedor-produtos/{vinculo_id}    DELETE /fornecedor-produtos/{vinculo_id}
```

Variantes são criadas em `POST /variantes` (com `produto_id` no corpo), **não** em
`/produtos/{id}/variantes`; o catálogo é `/loja-online`, não `/catalogo`. Não há `PATCH` de
produto, categoria ou fornecedor: a atualização é `PUT`.

### Regras de negócio

1. `preco_venda = preco_custo * (1 + markup_pct / 100)`, calculado no repositório
   (`Variante.calcular_preco_venda()`); `preco_venda` enviado no corpo é ignorado.
2. SKU é único **por empresa** (`uq_variantes_empresa_sku`), não globalmente.
3. Produto tem soft delete (`deletado_em`) e rota de restauração.
4. `criar_produto` **não** cria `LojaOnlineConfig`: a config é criada à parte, em
   `POST /loja-online/config` (default `visivel=False` no modelo).
5. **Não existe** "fornecedor principal": `FornecedorProduto` não tem campo `principal`
   (tem `codigo_fornecedor`, `preco_fornecedor`, `prazo_entrega_dias`, `quantidade_minima`, `ativo`).
6. Produtos **não chama** o estoque (não há `httpx` no serviço): o catálogo público não filtra
   por saldo. A chamada existente é **estoque → produtos** (`/produtos/{id}`, `/variantes/{id}`).

---

## 5. Serviço de Estoque (`services/estoque/` — porta 8003)

### Modelos (schema `estoque`, resumo)

```python
class Estoque:      # UNIQUE(empresa_id, produto_id, variante_id); CHECK quantidades >= 0
    id UUID, empresa_id, produto_id UUID, variante_id UUID | None
    quantidade, quantidade_reservada, quantidade_disponivel: float
    estoque_minimo: float, estoque_maximo: float | None, localizacao, ativo, created_at, updated_at

class Movimentacao:
    id UUID, estoque_id, lote_id, tipo (ENTRADA|SAIDA|AJUSTE|DEVOLUCAO|PERDA|TRANSFERENCIA),
    quantidade, quantidade_anterior, quantidade_posterior, motivo, observacao,
    documento, usuario_id, custo_unitario, custo_total, created_at

class Lote:         # UNIQUE(empresa_id, codigo); status ATIVO|VENCIDO|BLOQUEADO
class BaixaVendaProcessada / EstornoVendaProcessado:   # ledgers de idempotência, UNIQUE(empresa_id, documento)
class Inventario / ItemInventario:
```

Estoque é por `produto_id` (+ `variante_id` opcional), identificado por `estoque_id`;
**não** por `variante_id` como chave única.

### Endpoints (`routers/estoque.py`, prefixo `/estoque`)

```
POST /estoque                          → criar registro de estoque
GET  /estoque                          → listar (com alerta)
GET  /estoque/baixo                    → abaixo do mínimo
GET  /estoque/zerado
GET  /estoque/disponibilidade          → ?produto_id=&variante_id=
GET  /estoque/{estoque_id}    PUT /estoque/{estoque_id}
GET  /estoque/{estoque_id}/movimentacoes
GET  /estoque/{estoque_id}/lotes       GET /estoque/lotes/vencendo

POST /estoque/entrada    POST /estoque/saida    POST /estoque/ajuste
POST /estoque/reservar   POST /estoque/liberar-reserva
POST /estoque/baixar-venda    POST /estoque/estornar-venda      (idempotentes por documento)

GET  /estoque/relatorios/geral    GET /estoque/relatorios/movimentacoes
```

Não há `/estoque/{variante_id}/entrada|saida|ajuste|devolucao` nem `/estoque/alertas/minimo`;
o corpo carrega `produto_id`/`variante_id`.

### Regras de negócio

1. `quantidade`, `quantidade_reservada` e `quantidade_disponivel` não podem ser negativas:
   `CHECK ck_estoque_quantidades_nao_negativas` no banco. Saída acima do saldo é recusada pelo
   serviço com `ValueError` → **HTTP 400** (não 422).
2. Movimentações não têm endpoint de edição nem de exclusão (histórico só cresce).
3. Body com `empresa_id` diferente de `X-Empresa-Id` → 403.
4. `baixar-venda` e `estornar-venda` usam `documento` (= `numero_venda`) como chave de
   idempotência: repetir a chamada não baixa/devolve em duplicidade.
5. **Não há evento `estoque.minimo`**: o serviço não publica nada. O "abaixo do mínimo" é
   consulta (`/estoque/baixo`, `estoque.quantidade <= estoque_minimo`).
6. Chama o serviço produtos por HTTP (`services/estoque/services/estoque_service.py`).

---

## 6. Serviço de Vendas (`services/vendas/` — porta 8004)

### Modelos (schema `vendas`, resumo — `models/venda.py`)

```python
class Venda:         # UNIQUE(empresa_id, numero_venda)
    id UUID, empresa_id, numero_venda ("V-2026-00001"), cliente_id UUID | None,
    subtotal, desconto_tipo (PERCENTUAL|VALOR_FIXO), desconto_valor, valor_frete, valor_total,
    status, tipo_entrega (RETIRADA|DELIVERY),
    mercadopago_preference_id, mercadopago_payment_id, sessao_carrinho_id,
    cliente_convidado_* (nome, telefone, email, cpf), endereco_* (entrega),
    data_pedido/confirmacao/separacao/entregue/finalizada/cancelada, motivo_cancelamento,
    reconciliacao_estoque_pendente, observacao
class ItemVenda:            # snapshot do produto: descricao_produto, preco_unitario, subtotal
class PagamentoVenda:       # forma_pagamento (DINHEIRO|PIX|DEBITO|CREDITO|FIADO), valor_pago,
                            # valor_recebido, valor_troco, gera_conta_receber, conta_receber_id
class ReservaEstoqueVenda / ReservaTemporaria       # reserva de estoque (temporária: 15 min)
class WebhookProcessado                             # idempotência do webhook
class ConfiguracaoPagamento / ConfiguracaoIntegracao / FaixaEntrega / ConfiguracaoLoja
```

`StatusVenda`: `PEDIDO`, `PENDENTE_PAGAMENTO`, `CONFIRMADA`, `SEPARADA`, `EM_ENTREGA`,
`ENTREGUE`, `FINALIZADA`, `CANCELADA`, `REEMBOLSADA`.

**O carrinho não é tabela**: fica no Redis (`services/carrinho_service.py`, TTL de 7 dias). Não há
modelos `Carrinho`, `Pedido`, `EnderecoEntrega` nem `Pagamento` com esses nomes.

### Endpoints

```
# Vendas (balcão/admin) — /vendas
POST /vendas    GET /vendas    GET /vendas/{id}    PUT /vendas/{id}
POST /vendas/{id}/confirmar|separar|entregar|finalizar|cancelar
GET  /vendas/{id}/pagamentos    POST /vendas/{id}/pagamentos
GET  /vendas/relatorios/resumo

# Loja online — /loja (carrinho e checkout no serviço; slug/tenant resolvido em utils/tenant.py)
GET    /loja/carrinho    POST /loja/carrinho/itens
PUT    /loja/carrinho/itens/{produto_id}    DELETE /loja/carrinho/itens/{produto_id}
DELETE /loja/carrinho
POST   /loja/checkout
GET    /loja/meus-pedidos    GET /loja/rastrear/{numero_venda}
POST   /loja/pedidos/{numero_venda}/retry-payment
POST   /loja/pedidos/{numero_venda}/recuperar-carrinho

# Webhook Mercado Pago
POST /loja/{empresa_slug}/webhook/mercadopago      GET /loja/{empresa_slug}/webhook/mercadopago/test

# Configuração por empresa (admin)
GET|PUT  /admin/entrega/configuracao       GET|POST /admin/entrega/faixas
GET|PUT|DELETE /admin/entrega/faixas/{faixa_id}    GET /admin/entrega/simular/{cep}
GET /pagamentos/admin/status    GET|POST|PUT|DELETE /pagamentos/admin/configuracao
PATCH /pagamentos/admin/configuracao/ativar|desativar
GET|PUT|DELETE /integracoes                 # WhatsApp (Evolution) e SMTP por empresa
```

Não há `/pedidos`, `PATCH /pedidos/{id}/status`, `PATCH /pedidos/{id}/frete` nem
`PATCH /pagamentos/{pedido_id}/confirmar`. O gateway já tem um proxy
`POST /pagamentos/webhook/mercadopago` que encaminha ao vendas; `A CONFIRMAR` qual rota do vendas
o recebe (o serviço expõe `/loja/{empresa_slug}/webhook/mercadopago`).

### Regras de negócio

1. **Reserva de estoque**: chamadas HTTP a `ESTOQUE_URL` — `/estoque/reservar`,
   `/estoque/liberar-reserva`, `/estoque/saida` (`services/venda_service.py`), e
   `/estoque/baixar-venda`, `/estoque/estornar-venda` (ver `comunicacao.md` para linhas).
   A porta do estoque é **8003**.
2. **Webhook Mercado Pago**: valida `x-signature` com segredo por empresa
   (`mercadopago_webhook_secret`); notificação sem o cabeçalho cai no IPN legado (`?topic=`).
   Idempotência por `WebhookProcessado`.
3. **Pagamento online**: cria preferência de checkout no Mercado Pago
   (`services/mercadopago_service.py`); não há geração de QR code PIX própria no serviço.
4. **Desconto existe**: `desconto_tipo`/`desconto_valor` na venda (não é "sempre 0.00").
5. **Frete**: `valor_frete`, calculado por faixas de CEP (`FaixaEntrega`,
   `/admin/entrega/simular/{cep}`), não por `PATCH` manual.
6. **Troco**: `PagamentoVenda.valor_recebido` e `valor_troco` (só DINHEIRO).
7. **Loops periódicos no processo** (`main.py`, `lifespan`): `verificar_pagamentos_pendentes`
   a cada 60 s e `reconciliar_estoque_vendas` a cada 120 s. Os demais arquivos em `jobs/`
   (`limpar_reservas`, `limpar_carrinhos_abandonados`, `verificar_timeouts_separacao`) **não são
   agendados por nenhum código**; `A CONFIRMAR` se algum cron externo os executa.
8. **Fiado**: `PagamentoVenda.gera_conta_receber`/`conta_receber_id` existem, mas o serviço
   financeiro é esqueleto (sem rotas). `A CONFIRMAR` o que acontece de fato no fiado.

---

## 7. Serviço Financeiro (`services/financeiro/` — porta 8005) — ESQUELETO

- `main.py` só expõe `GET /health` (mais o middleware de origem interna).
- `models/`, `routers/`, `schemas/`, `repositories/` e `services/` contêm apenas `__init__.py`
  vazio; `seed.py` tem 16 linhas.
- O gateway roteia `/contas/*` para este serviço (`SERVICE_URLS`), mas **não há rota `/contas`
  implementada**: qualquer chamada resulta em 404 do serviço. Chamada direta sem o
  `X-Servico-Interno-Token` leva 403 (fail-closed desde 2026-10-06; só `/health` é isento).
- **Vazio de propósito** (decisão de 2026-10-05, C5): ver o roadmap antes de implementar.
- **Não existem**: contas a receber, pagamentos de fiado, jobs de vencimento, evento
  `cobranca.*`. O que antes era descrito aqui era especificação, não código.

---

## 8. Serviço de Notificações (`services/notificacoes/` — porta 8006) — ESQUELETO

- `main.py` só expõe `GET /health`.
- Sem modelos, routers ou consumidor RabbitMQ. O gateway roteia `/notificacoes/*` para cá, mas
  não há rota implementada.
- **Não existem**: histórico de notificações, retry com backoff, deduplicação, consumo de
  `erp.events`. Envio de WhatsApp (Evolution) e e-mail hoje é configurado no serviço vendas
  (`configuracoes_integracao`). `A CONFIRMAR`: quem de fato envia mensagens ao comprador.
- Chamada direta sem o `X-Servico-Interno-Token` leva 403 (fail-closed desde 2026-10-06; só `/health`
  é isento).
- **Vazio de propósito** (decisão de 2026-10-05, G3): ver o roadmap antes de implementar.

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Última verificação contra o código:** 2026-09-26
