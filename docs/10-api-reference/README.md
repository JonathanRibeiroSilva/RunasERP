# 📡 Referência de APIs - Runas

Todo o tráfego entra pelo **API Gateway** (`api-gateway/main.py`). Nenhum
microsserviço é exposto ao público: no `docker-compose.dev.yml` as portas dos
sete serviços estão publicadas como `127.0.0.1:800X:800X` — só o gateway
(`8000:8000`) escuta em todas as interfaces.

---

## 📑 Índice

### APIs por serviço

| Doc | Serviço | Estado no código |
|-----|---------|------------------|
| **[API de Clientes](./clientes-api.md)** | `services/clientes` | implementado (`routers/clientes.py`, `routers/enderecos.py`) |
| **[API de Produtos](./produtos-api.md)** | `services/produtos` | implementado (`routers/produtos.py`) |
| **[API de Estoque](./estoque-api.md)** | `services/estoque` | implementado (`routers/estoque.py`) |
| **[API de Vendas](./vendas-api.md)** | `services/vendas` | implementado (`routers/`: `vendas`, `loja`, `webhook`, `admin_pagamento`, `admin_entrega`, `admin_integracao`) |
| **[API da Plataforma](./plataforma-api.md)** | `api-gateway/routers/plataforma.py` | implementado (rotas `/plataforma/*`, super admin + webhook/cron públicos) |
| **[API Financeiro](./financeiro-api.md)** | `services/financeiro` | ⚠️ **NÃO IMPLEMENTADO** — veja o aviso abaixo |

> ⚠️ **`financeiro-api.md` documenta uma API que ainda não existe.**
> `services/financeiro/main.py` expõe apenas `GET /health`; as pastas
> `routers/`, `models/`, `schemas/`, `repositories/` e `services/` contêm só
> um `__init__.py` com docstring (sem código). O gateway *roteia* `/contas/*` para o serviço
> (`ServiceProxy.SERVICE_URLS`), mas o serviço não tem rota para atender.
> Trate o documento como especificação a implementar, não como contrato vigente.

> ⚠️ **Notificações também não está implementado** e por isso não tem doc aqui.
> `services/notificacoes/routers/` só tem `__init__.py`; o serviço responde
> apenas `GET /health`. O prefixo `/notificacoes/*` existe no gateway
> (`api-gateway/routers/proxy.py`) e cai num serviço sem rotas.

### Documentos gerais

- **[Mapeamento de Rotas](./mapeamento-rotas.md)** - Como as rotas são mapeadas do Gateway para os serviços
- **[Guia de Autenticação](./guia-autenticacao.md)** - OAuth2 e JWT com exemplos em JavaScript/TypeScript e Python
- **[Exemplos Práticos](./exemplos-praticos.md)** - Cenários completos com código
- **[openapi.yaml](./openapi.yaml)** - Especificação OpenAPI 3.0 escrita à mão (veja o aviso de dessincronia no fim)

---

## 🎯 Roteamento

Os prefixos abaixo saíram de `ServiceProxy.SERVICE_URLS`
(`api-gateway/proxy/service_proxy.py`) cruzados com as rotas registradas em
`api-gateway/routers/proxy.py`. O casamento é por `path.startswith(prefix)`;
path que não casa nenhum prefixo devolve **404 "Serviço não encontrado"**.

```
Cliente/Frontend
      │  HTTPS
      ▼
API Gateway (:8000)
      │
      ├─ /auth/*            → tratado no próprio gateway (routers/auth.py)
      ├─ /auth/cliente/*    → tratado no próprio gateway (routers/auth_cliente.py)
      ├─ /auth/admin/*      → tratado no próprio gateway (routers/auth_admin.py)
      ├─ /plataforma/*      → tratado no próprio gateway (routers/plataforma.py)
      │
      ├─ /clientes/*        → clientes      (:8001)
      ├─ /produtos/*        → produtos      (:8002)
      ├─ /categorias/*      → produtos      (:8002)
      ├─ /variantes/*       → produtos      (:8002)
      ├─ /fornecedores/*    → produtos      (:8002)
      ├─ /loja-online/*     → produtos      (:8002)
      ├─ /estoque/*         → estoque       (:8003)
      ├─ /loja/*            → vendas        (:8004)
      ├─ /carrinho/*        → vendas        (:8004)
      ├─ /pagamentos/*      → vendas        (:8004)
      ├─ /integracoes/*     → vendas        (:8004)
      ├─ /contas/*          → financeiro    (:8005)  ⚠️ serviço sem rotas
      ├─ /notificacoes/*    → notificações  (:8006)  ⚠️ serviço sem rotas
      └─ /empresas/*        → empresas      (:8007)
```

**Não existem** os prefixos `/vendas/*`, `/pedidos/*`, `/catalogo/*` nem
`/financeiro/*` — versões anteriores deste documento os listavam. Pedidos da
loja ficam sob `/loja/*` (ex.: `/loja/meus-pedidos`,
`/loja/pedidos/{numero_venda}/retry-payment`).

Rotas públicas (sem token): `GET /empresas/publico/*`,
`GET /loja-online/publico/*`, `/carrinho/*` e o catch-all `/loja/*` (exceto
`/loja/meus-pedidos` e `/loja/pedidos/{numero_venda}/...`, que exigem token de
cliente) — as três últimas resolvem o tenant pelo query param `?empresaSlug=`.

### Base URL

- **Desenvolvimento**: `http://localhost:8000`
- **Produção**: `https://app.runaserp.com.br/api` — o `/api` é removido pelo
  `rewrite` do nginx (`frontend/nginx.conf`) antes de chegar ao gateway, então
  o gateway recebe `/auth/login`, não `/api/auth/login`.

Não existe host `api.runas.com.br`: em produção a API sai pelo mesmo domínio do
app (`.env.coolify`, `.env.production.example`).

---

## 🔐 Autenticação

`POST /auth/login` usa `OAuth2PasswordRequestForm` (`routers/auth.py`) — ou
seja, **form-urlencoded com os campos `username` e `password`**, não JSON com
`email`/`password`. O `username` é o email.

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@runas.com&password=SENHA
```

**Resposta** (`LoginResponse`, `api-gateway/schemas/usuario.py`):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { "...": "UsuarioResponse" }
}
```

Não há campo `expires_in`. A validade vem das configurações
`ACCESS_TOKEN_EXPIRE_MINUTES` (padrão 30) e `REFRESH_TOKEN_EXPIRE_DAYS`
(padrão 7) em `api-gateway/config.py`. Os tokens também são gravados como
cookies HTTP-only.

### Usar o token

```http
GET /clientes
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Detalhes de fluxo, refresh e OAuth: **[Guia de Autenticação](./guia-autenticacao.md)**.

---

## 🔁 Idempotência (`Idempotency-Key`)

Implementada uma única vez no gateway (`api-gateway/proxy/idempotency.py`), no
caminho por onde toda requisição passa (`ServiceProxy.proxy_request`). Contrato:

- **Quando vale**: apenas se o header `Idempotency-Key` for enviado **e** o
  método for `POST`, `PUT`, `PATCH` ou `DELETE`. Sem o header, nada muda.
- **Escopo da chave**: `empresa_id` + método + path + valor do header. A mesma
  chave em outro endpoint, outro método ou outro tenant é outra operação.
- **Janela**: `IDEMPOTENCY_TTL_SECONDS`, padrão **86400s (24h)**
  (`api-gateway/config.py`).
- **Replay**: a resposta guardada é devolvida com o header
  **`X-Idempotent-Replay: true`**. O CORS do gateway declara
  `expose_headers=["X-Idempotent-Replay"]`, sem o que o browser não enxergaria
  o marcador.
- **Em voo**: se a mesma chave ainda está sendo processada, a resposta é
  **409 Conflict** com `detail: "Requisição com esta Idempotency-Key ainda está
  em processamento"`. O cliente deve reenviar.
- **Não é guardado** (a reserva é liberada e o cliente pode reenviar):
  status >= 500, status transitório (**408, 425, 429**) ou corpo de resposta
  acima de **256 KB**. Nesse último caso aquela chave perde o replay.
- Esta camada é defesa contra retry de cliente. A garantia final continua sendo
  a constraint `UNIQUE` no banco de cada serviço; as duas se somam.

---

## 🚀 Rate limiting

SlowAPI, com chave por **IP** (`api-gateway/middleware/rate_limit.py`):

- **Limite geral**: **300 requisições/minuto por IP**. O teto é generoso de
  propósito, para não travar um escritório inteiro atrás de um único IP de NAT.
- **Limites apertados por rota** (`@limiter.limit` direto no handler):

| Rota | Limite |
|------|--------|
| `POST /auth/login` | 10/min |
| `POST /auth/forgot-password` | 5/min |
| `POST /auth/reset-password` | 10/min |
| `POST /auth/cliente/login` | 10/min |
| `POST /auth/cliente/register` | 10/min |

- **Isentos**: `GET /health` e `GET /health/ready` (`@limiter.exempt`).
- **Quando excedido**: HTTP **429 Too Many Requests**.

### Por que o SlowAPI é registrado ANTES do CORS

Em `main.py` o `SlowAPIMiddleware` é adicionado **antes** do `CORSMiddleware`, e
isso é deliberado: `add_middleware()` empilha por fora a cada chamada, logo o
último adicionado embrulha o anterior. Com o CORS vindo depois, a resposta 429
do SlowAPI ainda atravessa o `CORSMiddleware` no caminho de volta e sai com os
headers de CORS. Na ordem inversa o browser veria a resposta como falha de CORS
em vez de 429. **Não reordene esses dois `add_middleware`.**

> **A CONFIRMAR: os headers `X-RateLimit-Limit` / `-Remaining` / `-Reset`.**
> O `Limiter` é construído sem `headers_enabled=True`, então esses headers
> (prometidos por versões anteriores deste documento) provavelmente **não** são
> emitidos. O corpo e os headers exatos do 429 precisam ser verificados numa
> resposta real antes de serem documentados aqui.

---

## 📊 Formato de resposta

Os routers devolvem o schema Pydantic direto — **não existe** envelope
`{"data": ..., "message": ...}`.

### Erro

Formato padrão do FastAPI/`HTTPException`, e o mesmo que o handler global de
`main.py` devolve em 500:

```json
{ "detail": "Email ou senha incorretos" }
```

Erro de validação (422) segue o formato do FastAPI, com `detail` como lista de
objetos `{loc, msg, type}`.

### Listagens

A paginação é por **`skip` / `limit`** (`Query`), não `page` / `per_page`. Ex.
em `services/clientes/routers/clientes.py`: `skip` (>=0, padrão 0) e `limit`
(1–100, padrão 100), mais filtros por serviço.

O envelope de listagem **não é padronizado entre os serviços** — o de clientes
devolve `{"clientes": [...], "total", "skip", "limit"}`. Confira o formato na
doc do serviço específico antes de consumir.

---

## 🔢 Códigos HTTP

Confirmados no código do gateway:

| Código | Onde |
|--------|------|
| **200 / 201 / 204** | sucesso conforme a rota (`status_code` em cada router) |
| **401** | token ausente/inválido, credenciais erradas (`routers/auth.py`) |
| **402** | escrita de tenant inadimplente (`middleware/inadimplencia_middleware.py`) |
| **403** | usuário inativo, permissão insuficiente |
| **404** | recurso inexistente; também "Serviço não encontrado" quando o path não casa nenhum prefixo, e "Empresa com slug '...' não encontrada" |
| **409** | `Idempotency-Key` ainda em processamento |
| **422** | validação de payload (FastAPI) |
| **429** | rate limit excedido |
| **500** | `{"detail": "Erro interno do servidor"}` do handler global |
| **503** | `httpx.ConnectError` ao falar com o serviço: "Serviço indisponível" |
| **504** | timeout de 30s no proxy: "Serviço não respondeu a tempo" |

---

## 🔒 Níveis de permissão

`RoleEnum` em `api-gateway/models/usuario.py` tem **três** valores:

| Role | Uso |
|------|-----|
| **SUPER_ADMIN** | operador da plataforma (rotas `/plataforma/*`) |
| **ADMIN** | administrador do tenant |
| **OPERADOR** | operação do dia a dia |

Os papéis `GERENTE` e `VENDEDOR`, listados por versões anteriores deste
documento, **não existem** no código.

---

## 📚 Documentação interativa (vem DESLIGADA)

`DOCS_ENABLED: bool = False` é o padrão em `api-gateway/config.py`, e `main.py`
usa isso assim:

```python
docs_url="/docs" if settings.DOCS_ENABLED else None,
redoc_url="/redoc" if settings.DOCS_ENABLED else None,
openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
```

Consequência: com a configuração padrão — **inclusive em produção** —
`/docs`, `/redoc` e `/openapi.json` respondem **404**. Não é bug: o schema
completo é um mapa da API para quem não deveria tê-lo.

Para habilitar em ambiente local, ponha no `.env`:

```env
DOCS_ENABLED=true
```

e então `http://localhost:8000/docs` e `/redoc` passam a responder.

---

## 🔍 Exemplos de uso

### cURL

```bash
# Login (form-urlencoded, campo "username")
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin@runas.com&password=SENHA'

# Listar clientes
curl -X GET 'http://localhost:8000/clientes?skip=0&limit=50' \
  -H "Authorization: Bearer TOKEN"

# Escrita idempotente
curl -X POST http://localhost:8000/pagamentos/ALGUM_ENDPOINT \
  -H "Authorization: Bearer TOKEN" \
  -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### JavaScript (Axios)

```javascript
// Login: form-urlencoded, não JSON
const { data } = await axios.post(
  'http://localhost:8000/auth/login',
  new URLSearchParams({ username: 'admin@runas.com', password: 'SENHA' })
);

const clientes = await axios.get('http://localhost:8000/clientes', {
  headers: { Authorization: `Bearer ${data.access_token}` },
  params: { skip: 0, limit: 50 }
});
```

### Python (Requests)

```python
import requests

r = requests.post(
    'http://localhost:8000/auth/login',
    data={'username': 'admin@runas.com', 'password': 'SENHA'},  # data, não json
)
token = r.json()['access_token']

clientes = requests.get(
    'http://localhost:8000/clientes',
    params={'skip': 0, 'limit': 50},
    headers={'Authorization': f'Bearer {token}'},
)
```

---

## 📄 Especificação OpenAPI

**[openapi.yaml](./openapi.yaml)** é um arquivo escrito à mão, **não** gerado a
partir do código.

> ⚠️ **Está dessincronizado e congelado** (o próprio arquivo declara isso no
> cabeçalho). Ele documenta paths que não existem no roteamento do gateway
> (`/catalogo`, `/pedidos`, `/carrinho/{token}`...). Enquanto não for regerado, o roteamento real é o de
> `api-gateway/proxy/service_proxy.py` e `api-gateway/routers/proxy.py`, junto
> com o `mapeamento-rotas.md`.

Como `/openapi.json` vem desligado (veja acima), gerar cliente a partir do
schema vivo exige `DOCS_ENABLED=true`. A partir do arquivo estático:

```bash
npm install @openapitools/openapi-generator-cli -g

openapi-generator-cli generate \
  -i docs/10-api-reference/openapi.yaml \
  -g typescript-axios \
  -o frontend/src/api/generated
```

---

## 📚 Documentos relacionados

- [Arquitetura de microsserviços](../03-arquitetura/microsservicos.md)
- [Comunicação entre serviços](../03-arquitetura/comunicacao.md)
- [Plataforma (multi-tenancy e billing)](../03-arquitetura/plataforma.md)
- [Regras de negócio](../11-regras-negocio/README.md)
- [Guia de desenvolvimento](../02-desenvolvimento/README.md)
- [Runbook de produção](../06-operacao/runbook-producao.md)
