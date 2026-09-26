# Guia de Autenticação - Runas API

> **Como autenticar** e usar tokens JWT na API do Runas

---

## 🔐 Visão Geral

A API do Runas usa **OAuth2 com JWT** (JSON Web Tokens) para autenticação.

**Fluxo:**
1. Login com email/senha → Recebe `access_token` + `refresh_token`
2. Usa `access_token` em todas as requisições
3. Quando expirar, renova com `refresh_token`
4. Logout invalida o `refresh_token`

---

## 🚀 Quick Start

### 1. Fazer Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.local&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

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

### 4. Logout

```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 📋 Detalhes dos Tokens

### Access Token
- **Duração**: 30 minutos
- **Uso**: Todas as requisições autenticadas
- **Formato**: JWT assinado com HS256
- **Payload**:
  ```json
  {
    "sub": "uuid-do-usuario",
    "role": "ADMIN",
    "exp": 1716724800,
    "iat": 1716723000
  }
  ```

### Refresh Token
- **Duração**: 7 dias
- **Uso**: Renovar access_token
- **Armazenamento**: Redis (blacklist ao fazer logout)
- **Único por usuário**: Login novo invalida o anterior

---

## 👥 Roles e Permissões

### ADMIN
- ✅ Acesso total a todos os endpoints
- ✅ Criar, editar, deletar qualquer recurso
- ✅ Ajustar crédito de clientes
- ✅ Bloquear/desbloquear clientes
- ✅ Configurar catálogo

### OPERADOR
- ✅ Listar clientes (somente leitura)
- ✅ Listar produtos (somente leitura)
- ✅ Criar pedidos
- ✅ Consultar estoque
- ❌ Editar clientes
- ❌ Editar produtos
- ❌ Ajustar crédito
- ❌ Configurar catálogo

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
    
    // Salvar no localStorage
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
await api.login('admin@runas.local', 'admin123');
const clientes = await api.request('/clientes');
```

---

### Python

```python
import requests
from datetime import datetime, timedelta

class RunasAPI:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

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
        self.token_expires_at = datetime.now() + timedelta(seconds=data['expires_in'])
        
        return data

    def request(self, method: str, endpoint: str, **kwargs):
        # Renovar token se expirado
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            self.refresh_access_token()

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
        self.token_expires_at = datetime.now() + timedelta(seconds=data['expires_in'])

    def logout(self):
        requests.post(
            f'{self.base_url}/auth/logout',
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        self.access_token = None
        self.refresh_token = None

# Uso
api = RunasAPI()
api.login('admin@runas.local', 'admin123')
clientes = api.request('GET', '/clientes')
```

---

## 🚨 Erros Comuns

### 401 Unauthorized

**Causa**: Token inválido, expirado ou não enviado

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

**Causa**: Role insuficiente (OPERADOR tentando acessar endpoint de ADMIN)

**Solução**: Fazer login com usuário ADMIN

---

### Token Expirado

**Sintoma**:
```json
{
  "detail": "Token has expired"
}
```

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
// localStorage (aceitável para MVP)
localStorage.setItem('access_token', token);

// httpOnly Cookie (mais seguro - requer configuração no backend)
// O token vem automaticamente nos cookies
```

---

### 2. Renovação Automática

```typescript
// Renovar automaticamente antes de expirar
setInterval(async () => {
  const expiresAt = localStorage.getItem('token_expires_at');
  const now = Date.now();
  
  // Renovar 5 minutos antes de expirar
  if (expiresAt && now >= (parseInt(expiresAt) - 300000)) {
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
        const { data } = await axios.post('/auth/refresh', {
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
