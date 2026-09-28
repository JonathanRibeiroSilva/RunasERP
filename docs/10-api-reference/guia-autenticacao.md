# Guia de Autenticação - Runas API

> **Como autenticar** e usar tokens JWT na API do Runas

---

## 🔐 Visão Geral

A API do Runas usa **OAuth2 com JWT** (JSON Web Tokens) para autenticação.

**Fluxo:**
1. Login com email/senha → Recebe `access_token` + `refresh_token` + dados do usuário (`user`). Os mesmos tokens também são gravados como cookies HTTP-only.
2. Usa o `access_token` em todas as requisições (cookie `access_token` ou header `Authorization: Bearer`; o cookie tem prioridade)
3. Quando expirar, renova com `refresh_token`
4. Logout apaga o `refresh_token` do Redis e limpa os cookies (o `access_token` já emitido continua válido até expirar; o gateway não o coloca em blacklist)

> **URL base:** os exemplos usam `http://localhost:8000` (gateway direto, `docker-compose.dev.yml`). Pelo frontend/nginx (e em produção, atrás do Cloudflare) as mesmas rotas ficam sob `/api` (ex.: `/api/auth/login`); o nginx remove o prefixo antes de repassar ao gateway (`frontend/nginx.conf`).
> Estas rotas são de **usuários do sistema** (`Usuario`). Clientes da loja online usam `/auth/cliente/*` (login, registro, OAuth Google/Microsoft), fora do escopo deste guia.

---

## 🚀 Quick Start

### 1. Fazer Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=SEU_EMAIL&password=SUA_SENHA"
```

O usuário admin inicial é criado no startup pelo `api-gateway/seed.py` a partir de `ADMIN_EMAIL` / `ADMIN_PASSWORD` (padrões do código: `admin@runas.com` / `Admin@123`; use os valores do seu `.env`). Limite: **10 requisições/minuto** (429 ao exceder).

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-do-usuario",
    "nome": "...",
    "email": "...",
    "role": "ADMIN",
    "ativo": true,
    "empresa_id": 1,
    "empresa_slug": "...",
    "criado_em": "..."
  }
}
```

Não há campo `expires_in`: a validade do access token é o `exp` do JWT (30 minutos por padrão).

### 2. Usar o Token

```bash
curl -X GET "http://localhost:8000/clientes" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Renovar Token (quando expirar)

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

Retorna `access_token`, o **mesmo** `refresh_token` enviado (não há rotação) e `token_type`.

### 4. Logout

```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Responde `204 No Content`.

### 5. Esqueci / redefinir senha

- `POST /auth/forgot-password` com `{"email": "..."}`: limite 5/min; sempre responde 200 com a mesma mensagem (evita enumeração). Se o usuário existe e está ativo, gera token (1 hora, no Redis) e envia e-mail.
- `POST /auth/reset-password` com `{"token": "...", "nova_senha": "..."}` (8 a 20 caracteres, mais a validação de força de ): limite 10/min; token de uso único (400 se inválido/expirado); apaga o refresh token do usuário (força novo login).
- `POST /auth/alterar-senha` (autenticado) com `senha_atual` e `nova_senha`; também apaga o refresh token.
- `GET /auth/me` (autenticado): dados do usuário logado.

Os demais endpoints têm o limite padrão de 300 requisições/minuto por IP (`api-gateway/middleware/rate_limit.py`).

---

## 📋 Detalhes dos Tokens

### Access Token
- **Duração**: 30 minutos (padrão de `ACCESS_TOKEN_EXPIRE_MINUTES`, configurável por env)
- **Uso**: Todas as requisições autenticadas
- **Formato**: JWT assinado com HS256
- **Cookie**: `access_token`, HTTP-only, `SameSite=lax`, `Secure` só quando `FRONTEND_URL` é https
- **Payload** (`auth/jwt.py`):
  ```json
  {
    "sub": "uuid-do-usuario",
    "role": "ADMIN",
    "user_type": "usuario",
    "exp": 1716724800,
    "iat": 1716723000
  }
  ```

### Refresh Token
- **Duração**: 7 dias (padrão de `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Uso**: Renovar access_token (o payload tem `type: "refresh"`, não tem `role`)
- **Armazenamento**: Redis, chave `refresh:{id_do_usuario}`; logout, reset e alteração de senha apagam a chave
- **Único por usuário**: Login novo sobrescreve a chave e invalida o anterior

---

## 👥 Roles e Permissões

`RoleEnum` (`api-gateway/models/usuario.py`): `SUPER_ADMIN`, `ADMIN`, `OPERADOR`.

A autorização por role é feita **no gateway** (`auth/oauth2.py`, `routers/proxy.py`). Os serviços não validam o JWT: confiam em `X-Empresa-Id` injetado pelo gateway (que descarta o header vindo do cliente) e checam `X-Servico-Interno-Token`, este último fail-open enquanto `SERVICO_INTERNO_TOKEN` estiver vazio (ver `CLAUDE.md`). Por isso, chamar a porta de um serviço direto, sem passar pelo gateway, não é um fluxo suportado.

| Role | Escopo |
|------|--------|
| `SUPER_ADMIN` | Dono da plataforma, sem tenant (`empresa_id` nulo). Papel disjunto de ADMIN, sem herança: só passa em rotas `require_super_admin` (plataforma). |
| `ADMIN` | Passa em `require_admin` e `require_admin_or_operador`. |
| `OPERADOR` | Passa só em `require_admin_or_operador`. |

Exigência por rota proxied (`routers/proxy.py`):

- Qualquer usuário ativo autenticado: `/clientes`, `/produtos`, `/categorias`, `/variantes`, `/fornecedores`, `/loja-online/*` (autenticado), `/pagamentos/*`
- ADMIN ou OPERADOR: `/estoque`
- Somente ADMIN: `/contas`, `/notificacoes`, `/integracoes`, `/empresas`, `/auth/admin/usuarios`

A CONFIRMAR: restrições finas por verbo (ex.: OPERADOR editar cliente/produto, ajustar crédito, configurar catálogo) e a rota de pedidos/vendas. O gateway não aplica role nessas rotas e os serviços não recebem o role; a lista de permissões da versão anterior deste guia não tinha respaldo no código.

---

## 💻 Exemplos de Código

### JavaScript/TypeScript

```typescript
class RunasAPI {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private baseURL = 'http://localhost:8000';

  async login(email: string, password: string) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: email,
        password: password,
      }),
    });

    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;

    // Salvar no localStorage (o navegador também recebe os cookies HTTP-only)
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  }

  async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    // Se 401, tentar renovar token
    if (response.status === 401) {
      await this.refreshAccessToken();
      // Tentar novamente
      return this.request(endpoint, options);
    }

    return response.json();
  }

  async refreshAccessToken() {
    const response = await fetch(`${this.baseURL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: this.refreshToken,
      }),
    });

    const data = await response.json();
    this.accessToken = data.access_token;
    localStorage.setItem('access_token', data.access_token);
  }

  async logout() {
    await fetch(`${this.baseURL}/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
      },
    });

    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

// Uso
const api = new RunasAPI();
await api.login('seu@email.com', 'sua-senha');
const clientes = await api.request('/clientes');
```

---

### Python

```python
import requests

class RunasAPI:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    def login(self, email: str, password: str):
        response = requests.post(
            f'{self.base_url}/auth/login',
            data={
                'username': email,
                'password': password
            }
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']

        return data

    def request(self, method: str, endpoint: str, **kwargs):
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers

        response = requests.request(
            method,
            f'{self.base_url}{endpoint}',
            **kwargs
        )

        # Se 401, tentar renovar
        if response.status_code == 401:
            self.refresh_access_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.request(method, f'{self.base_url}{endpoint}', **kwargs)

        return response.json()

    def refresh_access_token(self):
        response = requests.post(
            f'{self.base_url}/auth/refresh',
            json={'refresh_token': self.refresh_token}
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data['access_token']

    def logout(self):
        requests.post(
            f'{self.base_url}/auth/logout',
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        self.access_token = None
        self.refresh_token = None

# Uso
api = RunasAPI()
api.login('seu@email.com', 'sua-senha')
clientes = api.request('GET', '/clientes')
```

---

## 🚨 Erros Comuns

### 401 Unauthorized

**Causa**: Token inválido, expirado, na blacklist ou não enviado (`detail`: "Token não fornecido" ou "Credenciais inválidas"). No login, credenciais erradas retornam 401 com "Email ou senha incorretos"

**Solução**:
```bash
# Verificar se token está sendo enviado
curl -v -X GET "http://localhost:8000/clientes" \
  -H "Authorization: Bearer <token>"

# Renovar token
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

### 403 Forbidden

**Causa**: Role insuficiente (ex.: OPERADOR em rota `require_admin`: "Acesso negado: apenas administradores") ou usuário inativo ("Usuário inativo")

**Solução**: Fazer login com usuário ADMIN

---

### Token Expirado

**Sintoma**: `401` com
```json
{
  "detail": "Credenciais inválidas"
}
```
O gateway não distingue token expirado de token inválido.

**Solução**: Renovar com refresh_token

---

## 🔒 Boas Práticas

### 1. Armazenamento Seguro

**❌ NÃO FAZER:**
```javascript
// Nunca armazenar em variáveis globais
window.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
```

**✅ FAZER:**
```javascript
// httpOnly Cookie (mais seguro): o gateway já grava os cookies no login e o
// frontend usa axios com withCredentials: true; o token nunca passa pelo JS.

// localStorage (só para clientes não-navegador ou protótipos; legível por XSS)
localStorage.setItem('access_token', token);
```

---

### 2. Renovação Automática

```typescript
// Renovar automaticamente antes de expirar
setInterval(async () => {
  const token = localStorage.getItem('access_token');
  if (!token) return;
  // O login não devolve expires_in: ler o `exp` (segundos) do payload do JWT
  const exp = JSON.parse(atob(token.split('.')[1])).exp * 1000;

  // Renovar 5 minutos antes de expirar
  if (Date.now() >= exp - 300000) {
    await api.refreshAccessToken();
  }
}, 60000); // Verificar a cada minuto
```

---

### 3. Interceptors (Axios)

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Request interceptor - adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - renovar token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');

      try {
        const { data } = await axios.post(`${api.defaults.baseURL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        localStorage.setItem('access_token', data.access_token);

        // Tentar requisição novamente
        error.config.headers.Authorization = `Bearer ${data.access_token}`;
        return axios(error.config);
      } catch {
        // Refresh falhou, fazer logout
        localStorage.clear();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);
```

---

## 📚 Documentação Relacionada

- [OpenAPI Specification](./openapi.yaml)
- [Troubleshooting](../06-operacao/troubleshooting.md)
- [FAQ](../01-visao-geral/faq.md)

---

**Projeto:** Runas
**Equipe:** Equipe DenebCorp
**Data:** 26 de Maio de 2026
**Versão:** 1.0.0
