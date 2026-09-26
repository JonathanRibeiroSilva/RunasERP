# 🔀 Mapeamento de Rotas - Runas

Como as requisições chegam ao API Gateway e como ele decide para qual microsserviço encaminhá-las.

**Última atualização**: 2026-09-26
**Fontes lidas para este documento**: `api-gateway/main.py`, `api-gateway/routers/proxy.py`, `api-gateway/routers/plataforma.py`, `api-gateway/routers/auth.py`, `api-gateway/proxy/service_proxy.py`, `frontend/vite.config.ts`, `frontend/nginx.conf`, `docker-compose.prod.yml`

---

## ⚠️ AVISO: o gateway NÃO tem prefixo `/api`

O FastAPI do gateway expõe as rotas na raiz: `/auth/login`, `/health`, `/health/ready`, `/clientes`, `/plataforma/tenants`. **Não existe `/api` dentro do gateway.**

O `/api` é um detalhe da borda: o frontend chama `/api/...` (mesma origem, sem CORS) e quem estiver na frente remove o prefixo antes de repassar.

| Ambiente | Quem remove o `/api` | Evidência |
|----------|---------------------|-----------|
| Dev | proxy do Vite | `frontend/vite.config.ts` — `rewrite: (path) => path.replace(/^\/api/, '')`, target `http://api-gateway:8000` |
| Produção | nginx da imagem do frontend | `frontend/nginx.conf` — `location /api/ { rewrite ^/api/(.*)$ /$1 break; proxy_pass http://$gateway; }` com `set $gateway api-gateway-prod:8000` |

Consequências práticas:

- Testando o gateway direto (curl no container, port-forward): use **sem** `/api` → `curl http://localhost:8000/auth/login`.
- Testando pela borda (navegador, domínio público): use **com** `/api` → `https://<dominio>/api/auth/login`.
- Em dev o proxy do Vite só existe quando `VITE_USE_PROXY` **não** é `"false"` (`vite.config.ts`). Com `VITE_USE_PROXY=false` espera-se um proxy externo cumprindo o mesmo papel.

---

## 📊 Visão geral do roteamento

```
Navegador → borda (Vite em dev / nginx em prod) → tira /api
          → API Gateway (8000)
              ├─ resolve no próprio gateway: /auth/*, /plataforma/*, /health*
              └─ faz proxy por prefixo → microsserviço (8001..8007)
```

O gateway resolve o destino em `ServiceProxy._get_service_url()` (`api-gateway/proxy/service_proxy.py`): percorre o dicionário `SERVICE_URLS` **na ordem de declaração** e devolve a primeira URL cujo prefixo casa com `path.startswith(prefix)`. Nenhum prefixo casou → `404 {"detail": "Serviço não encontrado"}`.

---

## 🗺️ Mapa real de prefixos → serviço

Copiado de `SERVICE_URLS` em `api-gateway/proxy/service_proxy.py`, na mesma ordem do código (a ordem importa: `/loja-online` precede `/loja`, senão a loja online cairia em vendas).

| Prefixo no gateway | Variável | Serviço | Porta |
|--------------------|----------|---------|-------|
| `/clientes` | `CLIENTES_URL` | clientes | 8001 |
| `/produtos` | `PRODUTOS_URL` | produtos | 8002 |
| `/categorias` | `PRODUTOS_URL` | produtos | 8002 |
| `/variantes` | `PRODUTOS_URL` | produtos | 8002 |
| `/fornecedores` | `PRODUTOS_URL` | produtos | 8002 |
| `/loja-online` | `PRODUTOS_URL` | produtos | 8002 |
| `/estoque` | `ESTOQUE_URL` | estoque | 8003 |
| `/loja` | `VENDAS_URL` | vendas | 8004 |
| `/carrinho` | `VENDAS_URL` | vendas | 8004 |
| `/pagamentos` | `VENDAS_URL` | vendas | 8004 |
| `/integracoes` | `VENDAS_URL` | vendas | 8004 |
| `/contas` | `FINANCEIRO_URL` | financeiro | 8005 |
| `/notificacoes` | `NOTIFICACOES_URL` | notificações | 8006 |
| `/empresas` | `EMPRESAS_URL` | empresas | 8007 |

Portas conferidas nos defaults de `docker-compose.prod.yml` (`http://clientes-prod:8001` … `http://empresas-prod:8007`).

O `ServiceProxy` **não reescreve** o caminho: a URL final é `f"{service_url}{path}"`. `GET /clientes/42` no gateway vira `GET http://clientes-prod:8001/clientes/42`. A única reescrita do repositório acontece antes, no handler de `/clientes/me` (ver abaixo).

### 🚨 `/contas` aponta para um serviço que não tem a rota

`SERVICE_URLS` manda `/contas` para `FINANCEIRO_URL`, mas `services/financeiro/main.py` registra **apenas** `@app.get("/health")` — e `services/financeiro/routers/__init__.py` só tem uma docstring, sem nenhum router incluído.

Portanto **toda** chamada a `/contas/*` é 404 garantido, vindo do FastAPI do financeiro (não do gateway). O gateway autentica, exige ADMIN, encaminha, e o financeiro responde 404. O serviço financeiro tem as pastas `models/`, `repositories/`, `services/` e `schemas/`, mas o `__init__.py` de cada uma só contém uma docstring: não há modelo, repositório, serviço nem schema implementado (`main.py` não inclui nenhum router).

---

## 🔐 Rotas resolvidas no próprio gateway

### Autenticação de usuário — `api-gateway/routers/auth.py` (prefixo `/auth`)

| Método | Rota | Autenticação |
|--------|------|--------------|
| POST | `/auth/login` | ❌ pública |
| POST | `/auth/refresh` | ❌ pública |
| POST | `/auth/forgot-password` | ❌ pública |
| POST | `/auth/reset-password` | ❌ pública |
| GET | `/auth/me` | ✅ token |
| POST | `/auth/logout` | ✅ token |
| POST | `/auth/alterar-senha` | ✅ token |

### Autenticação de cliente final — `api-gateway/routers/auth_cliente.py` (prefixo `/auth/cliente`)

| Método | Rota |
|--------|------|
| POST | `/auth/cliente/register` |
| POST | `/auth/cliente/login` |
| POST | `/auth/cliente/logout` |
| POST | `/auth/cliente/oauth/google/init` |
| POST | `/auth/cliente/oauth/google/callback` |
| POST | `/auth/cliente/oauth/microsoft/init` |
| POST | `/auth/cliente/oauth/microsoft/callback` |
| POST | `/auth/cliente/registrar-interno` |

### Gestão de usuários do tenant — `api-gateway/routers/auth_admin.py` (prefixo `/auth/admin`)

| Método | Rota |
|--------|------|
| GET | `/auth/admin/usuarios` |
| POST | `/auth/admin/usuarios` |
| PUT | `/auth/admin/usuarios/{user_id}` |
| DELETE | `/auth/admin/usuarios/{user_id}` |

### Health — `api-gateway/main.py`

| Método | Rota | O que checa |
|--------|------|-------------|
| GET | `/health` | liveness raso: só prova que o processo responde. É o que o healthcheck do Docker lê |
| GET | `/health/ready` | readiness: Postgres, Redis e os **sete** serviços em paralelo, timeout de 2s cada; 503 nomeando quem caiu |

---

## 🏢 Plano de controle multi-tenant — `/plataforma`

`api-gateway/routers/plataforma.py` tem dois routers, ambos com prefixo `/plataforma` e ambos registrados em `main.py`.

### Router protegido — `dependencies=[Depends(require_super_admin)]`

`require_super_admin` (`api-gateway/auth/oauth2.py`) exige `role == SUPER_ADMIN`; 403 caso contrário. É papel **disjunto** de ADMIN, sem herança, e o super admin não tem tenant (`empresa_id` nulo).

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/plataforma/tenants` | Listar todos os tenants |
| POST | `/plataforma/tenants` | Provisionar tenant (201) |
| PATCH | `/plataforma/tenants/{empresa_id}/suspender` | Suspender tenant |
| PATCH | `/plataforma/tenants/{empresa_id}/reativar` | Reativar tenant |
| PATCH | `/plataforma/tenants/{empresa_id}/plano` | Alterar plano e limites |
| GET | `/plataforma/tenants/{empresa_id}/auditoria` | Trilha de auditoria do tenant |
| POST | `/plataforma/auditoria/{registro_id}/reverter` | Reverter uma escrita auditada |
| GET | `/plataforma/tenants/{empresa_id}/exportar` | Exportar dados do tenant |
| GET | `/plataforma/tenants/{empresa_id}/dumps` | Listar backups do tenant |
| POST | `/plataforma/tenants/{empresa_id}/assinatura` | Gerar link de assinatura |
| DELETE | `/plataforma/tenants/{empresa_id}/assinatura` | Cancelar assinatura |

Essas rotas não passam pelo `ServiceProxy` genérico: falam com o serviço de empresas por um helper interno que carimba `X-Plataforma: 1` (`HEADERS_PLATAFORMA`), o portão do serviço de empresas para operações de plataforma.

### Router público — `router_publico`, sem dependência de auth

| Método | Rota | Proteção |
|--------|------|----------|
| POST | `/plataforma/webhook/mercadopago` | **nenhuma**: o handler não valida assinatura. Idempotência por `evento_id` gravado em `gateway.webhooks_plataforma`; responde 200 até para evento repetido, porque 4xx faria o MP reenviar para sempre |
| POST | `/plataforma/jobs/regua` | header `X-Job-Token` comparado a `settings.PLATAFORMA_JOB_TOKEN`; 403 se o setting estiver vazio ou o header não casar |

`/plataforma/jobs/regua` é chamado pelo **cron do host**, não por um scheduler residente. Aplica a régua de inadimplência e poda a auditoria vencida.

Detalhe do plano de controle e dos contratos de cada rota: [plataforma-api.md](plataforma-api.md) e [../03-arquitetura/plataforma.md](../03-arquitetura/plataforma.md).

---

## 🛒 Rotas de proxy sem autenticação

De `api-gateway/routers/proxy.py`. O Starlette casa na ordem de registro, então cada handler público precisa vir antes do catch-all autenticado do mesmo prefixo (`/empresas/publico`, `/loja-online/publico`, `/carrinho` e `/loja` estão antes de `/empresas/{path}`, `/loja-online/{path}` etc.). **Exceção**: o webhook de `/pagamentos`, ver nota abaixo da tabela.

| Métodos | Rota no gateway | Serviço | Como resolve o tenant |
|---------|-----------------|---------|----------------------|
| GET | `/empresas/publico/{path:path}` | empresas (8007) | **não** recebe `empresaSlug`; o handler só repassa o caminho |
| GET | `/loja-online/publico/{path:path}` | produtos (8002) | query param `empresaSlug` |
| GET POST PATCH DELETE | `/carrinho/{path:path}` | vendas (8004) | query param `empresaSlug` |
| GET POST PUT PATCH DELETE | `/loja/{path:path}` | vendas (8004) | query param `empresaSlug` |
| POST | `/pagamentos/webhook/mercadopago` | vendas (8004) | nenhum (webhook) — **ver aviso abaixo** |

> **Aviso sobre `/pagamentos/webhook/mercadopago`.** Ele é declarado em `proxy.py:498`, **depois** de `/pagamentos/{path:path}` (`proxy.py:452`, guard `get_current_active_user`). Pela ordem de registro, um POST nesse caminho casa primeiro com o catch-all autenticado, então o handler público provavelmente nunca é alcançado. Além disso, o serviço de vendas não tem rota `/pagamentos/webhook/mercadopago`: o webhook do Mercado Pago de vendas é `POST /loja/{empresa_slug}/webhook/mercadopago` (`services/vendas/routers/webhook.py:61`), coberto pelo catch-all público `/loja/{path:path}`. **A CONFIRMAR**: comportamento em runtime (só a leitura do código foi feita) e qual URL está cadastrada no painel do Mercado Pago. O webhook de mensalidade da plataforma é outro: `/plataforma/webhook/mercadopago`, acima.

Quando `empresaSlug` vem preenchido, `ServiceProxy.get_empresa_id_from_slug()` faz `SELECT id FROM empresas.empresas WHERE slug = :slug`; slug inexistente → `404 "Empresa com slug '<x>' não encontrada"`.

---

## 🔒 Rotas de proxy autenticadas

Todas de `api-gateway/routers/proxy.py`. A coluna "Guard" é a dependência FastAPI declarada no handler.

| Métodos | Rota no gateway | Guard | Serviço |
|---------|-----------------|-------|---------|
| GET | `/clientes/me` | `get_current_active_cliente` | clientes (8001) |
| PATCH | `/clientes/me` | `get_current_active_cliente` | clientes (8001) |
| GET | `/loja/meus-pedidos` | `get_current_active_cliente` | vendas (8004) |
| POST | `/loja/pedidos/{numero_venda}/retry-payment` | `get_current_active_cliente` | vendas (8004) |
| POST | `/loja/pedidos/{numero_venda}/recuperar-carrinho` | `get_current_active_cliente` | vendas (8004) |
| GET POST | `/clientes` | `get_current_active_user` | clientes (8001) |
| GET POST PUT PATCH DELETE | `/clientes/{path:path}` | `get_current_active_user` | clientes (8001) |
| GET POST | `/produtos` | `get_current_active_user` | produtos (8002) |
| GET POST PUT PATCH DELETE | `/produtos/{path:path}` | `get_current_active_user` | produtos (8002) |
| GET POST PUT PATCH DELETE | `/loja-online/{path:path}` | `get_current_active_user` | produtos (8002) |
| GET POST | `/categorias` | `get_current_active_user` | produtos (8002) |
| GET POST PUT PATCH DELETE | `/categorias/{path:path}` | `get_current_active_user` | produtos (8002) |
| GET POST | `/variantes` | `get_current_active_user` | produtos (8002) |
| GET POST PUT PATCH DELETE | `/variantes/{path:path}` | `get_current_active_user` | produtos (8002) |
| GET POST | `/fornecedores` | `get_current_active_user` | produtos (8002) |
| GET POST PUT PATCH DELETE | `/fornecedores/{path:path}` | `get_current_active_user` | produtos (8002) |
| GET POST | `/estoque` | `require_admin_or_operador` | estoque (8003) |
| GET POST PUT PATCH DELETE | `/estoque/{path:path}` | `require_admin_or_operador` | estoque (8003) |
| GET POST PATCH | `/pagamentos/{path:path}` | `get_current_active_user` | vendas (8004) |
| GET POST PATCH | `/contas/{path:path}` | `require_admin` | financeiro (8005) — **404, ver aviso acima** |
| GET POST | `/notificacoes/{path:path}` | `require_admin` | notificações (8006) |
| GET PUT DELETE | `/integracoes` | `require_admin` | vendas (8004) |
| GET | `/empresas` | `require_admin` | empresas (8007) |
| GET PUT DELETE | `/empresas/{path:path}` | `require_admin` | empresas (8007) |

Notas de precedência (comentadas no próprio código): `/clientes/me` e `/loja/meus-pedidos` estão declaradas **antes** dos `{path:path}` correspondentes, senão o catch-all as engoliria. `/loja-online/publico/{path}` vem antes de `/loja-online/{path}`.

`/clientes/me` é o único caso em que o gateway reescreve o caminho: ele tira o `cliente_id` do token e encaminha para `/clientes/{cliente_id}` no serviço de clientes.

As rotas de leitura/escrita **dentro** de cada serviço (o que existe abaixo de `/produtos/…`, `/estoque/…`) estão nos documentos por serviço: [clientes-api.md](clientes-api.md), [produtos-api.md](produtos-api.md), [estoque-api.md](estoque-api.md), [vendas-api.md](vendas-api.md), [financeiro-api.md](financeiro-api.md).

---

## 🏷️ Headers de contexto injetados pelo gateway

`ServiceProxy.proxy_request()` é o único lugar que carimba identidade. Os serviços confiam nesses headers como prova de origem interna, e o gateway **remove** qualquer versão vinda do cliente antes de injetar a sua (chaves de `request.headers` chegam minúsculas, então um `x-empresa-id` do cliente sobreviveria ao lado do injetado):

```python
for interno in ("x-empresa-id", "x-cliente-id", "x-plataforma",
                "x-servico-interno-token", "x-plataforma-token"):
    headers.pop(interno, None)
```

Depois, em `_inject_context_headers()`:

| Header | Quando é injetado |
|--------|-------------------|
| `X-Empresa-Id` | slug público resolvido, ou `empresa_id` do usuário/cliente autenticado |
| `X-Cliente-Id` | portador é um cliente autenticado (`cliente_id` presente) |
| `X-Plataforma: 1` | só nas rotas de `/plataforma` (helper próprio, não passa por aqui) |

`auth_interno(headers)` carimba a prova de origem interna em toda chamada proxied.

### Idempotência

Se a requisição traz `Idempotency-Key` e o método está em `idempotency.METODOS`, o gateway reserva a chave no Redis **antes** de encaminhar (`montar_chave(empresa_id, method, path, valor)`, TTL `settings.IDEMPOTENCY_TTL_SECONDS`). Um retry do cliente recebe a resposta guardada em vez de duplicar a venda. Sem o header, nada muda.

---

## 🔄 Fluxo de uma requisição

```
1. Navegador (prod):
   POST https://<dominio>/api/clientes
   Authorization: Bearer {token}

2. nginx do frontend:
   rewrite ^/api/(.*)$ /$1  →  POST /clientes
   proxy_pass http://api-gateway-prod:8000

3. API Gateway — handler proxy_clientes_root:
   a. get_current_active_user valida o JWT
   b. remove x-empresa-id / x-cliente-id / x-plataforma vindos do cliente
   c. auth_interno carimba a prova de origem interna
   d. injeta X-Empresa-Id = current_user.empresa_id
   e. _get_service_url("/clientes") → CLIENTES_URL

4. Proxy HTTP (httpx, timeout 30s):
   POST http://clientes-prod:8001/clientes
   X-Empresa-Id: 7

5. Serviço de clientes processa e responde; o gateway repassa a resposta.
```

---

## 🛡️ Validação de token

`get_current_active_user` (`api-gateway/auth/oauth2.py`):

1. Extrai o token do header `Authorization: Bearer {token}`
2. Valida assinatura e expiração do JWT
3. Consulta a blacklist no Redis
4. Busca o usuário no banco
5. O guard específico confere o papel

| Guard | Papel exigido |
|-------|---------------|
| `get_current_active_user` | qualquer usuário ativo do tenant |
| `require_admin_or_operador` | ADMIN ou OPERADOR |
| `require_admin` | ADMIN |
| `require_super_admin` | SUPER_ADMIN (dono da plataforma, sem tenant) |
| `get_current_active_cliente` | cliente final autenticado (token de cliente, não de usuário) |

---

## 🔧 Configuração

### Variáveis lidas pelo gateway

De `api-gateway/config.py` (todas obrigatórias, sem default):

```env
DATABASE_URL=...
REDIS_URL=...
EMPRESAS_URL=http://empresas-prod:8007
CLIENTES_URL=http://clientes-prod:8001
PRODUTOS_URL=http://produtos-prod:8002
ESTOQUE_URL=http://estoque-prod:8003
VENDAS_URL=http://vendas-prod:8004
FINANCEIRO_URL=http://financeiro-prod:8005
NOTIFICACOES_URL=http://notificacoes-prod:8006
```

Valores acima são os defaults de `docker-compose.prod.yml`; em dev os hostnames não têm o sufixo `-prod` (ver `docker-compose.dev.yml`).

### Timeout

`httpx.AsyncClient(timeout=30.0)` — **hardcoded** em `api-gateway/proxy/service_proxy.py`, não é variável de ambiente. Timeout das sondas de health é separado: `HEALTH_TIMEOUT = 2.0` em `main.py`.

---

## 🧪 Testando o roteamento

Os comandos abaixo batem **direto no gateway**, por isso sem `/api`. Pela borda pública, prefixe `/api`.

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<email>&password=<senha>"

TOKEN="eyJ..."

# Rota pública (loja online de um tenant)
curl "http://localhost:8000/loja-online/publico/produtos?empresaSlug=<slug>"

# Rota autenticada
curl http://localhost:8000/clientes -H "Authorization: Bearer $TOKEN"

# Rota ADMIN/OPERADOR
curl http://localhost:8000/estoque -H "Authorization: Bearer $TOKEN"

# Plano de controle (exige SUPER_ADMIN)
curl http://localhost:8000/plataforma/tenants -H "Authorization: Bearer $TOKEN"

# Health
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

Credenciais de seed: ver [../06-operacao/SEED_DATA_COMPLETO.md](../06-operacao/SEED_DATA_COMPLETO.md).

---

## 📊 Logs do proxy

`ServiceProxy.proxy_request()` loga cada encaminhamento com `structlog`:

```json
{
  "event": "proxy.request",
  "method": "GET",
  "path": "/clientes",
  "target": "http://clientes-prod:8001/clientes",
  "empresa_id": 7
}
```

Eventos relacionados no mesmo módulo: `proxy.response`, `proxy.idempotent_hit`, `proxy.timeout`, `proxy.connection_error`, `proxy.error`. Em `main.py`: `health.check_failed`.

---

## ⚠️ Tratamento de erros

| Situação | Status | Origem |
|----------|--------|--------|
| Nenhum prefixo de `SERVICE_URLS` casou | 404 `"Serviço não encontrado"` | gateway |
| `empresaSlug` inexistente | 404 `"Empresa com slug '<x>' não encontrada"` | gateway |
| Papel insuficiente | 403 | guard do gateway |
| Serviço não respondeu em 30s | 504 `"Serviço não respondeu a tempo"` | gateway (`proxy.timeout`) |
| Conexão recusada (`httpx.ConnectError`) | 503 `"Serviço indisponível"` | gateway (`proxy.connection_error`) |
| Qualquer outra exceção ao falar com o serviço | 500 `"Erro ao comunicar com o serviço"` | gateway (`proxy.error`) |
| Rota não existe no serviço de destino (ex.: qualquer `/contas/*`) | 404 | microsserviço |
| Dependência caída em `/health/ready` | 503 nomeando o check | gateway |

---

## 📎 Relacionados

- [README do api-reference](README.md)
- [Guia de autenticação](guia-autenticacao.md)
- [API do plano de controle](plataforma-api.md)
- [Arquitetura da plataforma multi-tenant](../03-arquitetura/plataforma.md)
- [Comunicação entre serviços](../03-arquitetura/comunicacao.md)
