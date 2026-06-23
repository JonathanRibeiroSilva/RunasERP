# Separação de Autenticação: Operadores vs Clientes

**Data**: 2026-06-12  
**Versão**: 2.0.0 (Breaking Changes)

## 🎯 Objetivo

Separar completamente os fluxos de autenticação:
- **Usuários Operadores** (ADMIN/OPERADOR): Login via email/senha no sistema
- **Clientes Compradores**: Login via OAuth (Google/Microsoft) ou registro público

## 📋 Mudanças Implementadas

### Backend (API Gateway)

#### 1. Novo Modelo `ClienteAuth`
- **Arquivo**: `api-gateway/models/cliente_auth.py`
- Armazena credenciais de autenticação de clientes compradores
- Campos principais:
  - `email`: Email do cliente
  - `senha_hash`: Hash da senha (vazio para OAuth)
  - `cliente_id`: UUID do cliente no serviço clientes
  - `empresa_id`: ID da loja onde se cadastrou

#### 2. Novo Repository `ClienteAuthRepository`
- **Arquivo**: `api-gateway/repositories/cliente_auth_repository.py`
- Métodos:
  - `buscar_por_email()`
  - `buscar_por_id()`
  - `criar()`
  - `verificar_senha()`

#### 3. Novos Schemas
- **Arquivo**: `api-gateway/schemas/cliente.py`
- `ClienteRegisterRequest`: Registro de cliente (requer empresa_id)
- `ClienteLoginResponse`: Resposta de login com tipo "cliente"
- `ClienteAuthResponse`: Dados de autenticação do cliente

#### 4. JWT Atualizado
- **Arquivo**: `api-gateway/auth/jwt.py`
- Função `create_access_token()` agora aceita:
  - `user_type`: "usuario" ou "cliente"
  - `empresa_id`: ID da empresa (para clientes)
- Payload do token inclui `user_type` e `empresa_id`

#### 5. Novos Routers

##### 5.1 Router de Cliente (`auth_cliente.py`)
- **Prefix**: `/auth/cliente`
- **Endpoints**:
  - `POST /register`: Registro público de cliente
  - `POST /login`: Login de cliente
  - `POST /oauth/google/init`: Inicia OAuth Google
  - `POST /oauth/google/callback`: Callback OAuth Google
  - `POST /oauth/microsoft/init`: Inicia OAuth Microsoft
  - `POST /oauth/microsoft/callback`: Callback OAuth Microsoft

**Fluxo OAuth para clientes**:
1. Frontend envia `empresa_id` no init (identifica a loja)
2. State salvo no Redis inclui `empresa_id`
3. Callback cria `Cliente` no serviço clientes
4. Cria `ClienteAuth` no gateway
5. Retorna JWT com `user_type: "cliente"`

##### 5.2 Router Admin (`auth_admin.py`)
- **Prefix**: `/auth/admin`
- **Endpoints**:
  - `POST /usuarios`: Cria novo operador (requer ser ADMIN)
- Apenas ADMINs podem criar novos operadores
- Novo operador vinculado à mesma empresa do ADMIN

#### 6. Router Original (`auth.py`)
- **OAuth Deprecated**: Endpoints OAuth marcados como `deprecated=True`
- `/oauth/google` → deprecated
- `/oauth/google/callback` → deprecated
- `/oauth/microsoft` → deprecated
- `/oauth/microsoft/callback` → deprecated
- **Register Deprecated**: `/register` marcado como deprecated
- Usuários devem usar `/auth/admin/usuarios` ou `/auth/cliente/register`

#### 7. Migration
- **Arquivo**: `alembic/versions/20260612_120000_add_cliente_auth.py`
- Cria tabela `gateway.clientes_auth`

#### 8. Main.py Atualizado
- Registra novos routers:
  - `auth.router`
  - `auth_cliente.router`
  - `auth_admin.router`

### Frontend

#### 1. LoginPage Atualizado
- **Arquivo**: `frontend/src/pages/Login/LoginPage.tsx`
- **Removido**:
  - Botões OAuth (Google/Microsoft)
  - Função `handleOAuthLogin()`
  - Imports: `oauthService`, `FcGoogle`, `SiMicrosoft`
  - Lógica de `configuredProviders` e `hasOAuthProviders`
  - Link "Não tem conta? Criar conta"

**Agora**: Login simples com email/senha apenas para operadores

---

## 🔄 Fluxos de Autenticação

### 1. Operador (ADMIN/OPERADOR)

#### Criação:
```
ADMIN logado → POST /auth/admin/usuarios
{
  "email": "operador@loja.com",
  "nome": "João Silva",
  "senha": "Senha123!",
  "role": "OPERADOR",  // ou "ADMIN"
  "empresa_id": 1  // Será forçado para empresa do ADMIN
}
```

#### Login:
```
POST /auth/login
{
  "username": "operador@loja.com",  // OAuth2PasswordRequestForm
  "password": "Senha123!"
}

Response:
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "...",
    "nome": "...",
    "role": "OPERADOR",
    "empresa_id": 1
  }
}

JWT Payload:
{
  "sub": "user_uuid",
  "role": "OPERADOR",
  "user_type": "usuario",  // ← Tipo de usuário
  "exp": ...,
  "iat": ...
}
```

### 2. Cliente Comprador

#### Registro Público:
```
POST /auth/cliente/register
{
  "email": "cliente@gmail.com",
  "senha": "Senha123!",
  "nome": "Maria Santos",
  "cpf": "12345678901",
  "telefone": "11999999999",
  "empresa_id": 1  // ID da loja onde está comprando
}

Fluxo interno:
1. Cria Cliente no serviço clientes (POST /clientes com header X-Empresa-Id)
2. Cria ClienteAuth no gateway
3. Retorna JWT com user_type="cliente"
```

#### Login:
```
POST /auth/cliente/login
{
  "username": "cliente@gmail.com",
  "password": "Senha123!"
}

Response:
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user_type": "cliente",  // ← Identifica tipo
  "cliente": {
    "id": "uuid",
    "cpf": "12345678901",
    "nome": "Maria Santos",
    "email": "...",
    "empresa_id": 1
  }
}

JWT Payload:
{
  "sub": "cliente_auth_uuid",
  "role": "CLIENTE",
  "user_type": "cliente",  // ← Tipo de usuário
  "empresa_id": 1,  // ← ID da loja
  "exp": ...,
  "iat": ...
}
```

#### OAuth Google:
```
1. POST /auth/cliente/oauth/google/init
   {
     "redirect_uri": "http://localhost:3000/oauth/callback",
     "empresa_id": 1  // ← Identifica a loja
   }
   
2. Usuário autoriza no Google

3. POST /auth/cliente/oauth/google/callback
   {
     "code": "...",
     "state": "..."
   }
   
Fluxo interno:
1. Extrai empresa_id do state no Redis
2. Busca ou cria Cliente no serviço clientes (CPF temporário "00000000000")
3. Cria ClienteAuth com senha vazia (OAuth)
4. Retorna JWT com user_type="cliente"
```

#### OAuth Microsoft:
```
Mesmo fluxo do Google, mas com endpoints:
- POST /auth/cliente/oauth/microsoft/init
- POST /auth/cliente/oauth/microsoft/callback
```

---

## 🔐 Segurança

### 1. Isolamento de Dados
- **Usuários Operadores**: Tabela `gateway.usuarios`
- **Clientes Compradores**: Tabela `gateway.clientes_auth`
- Sem conflito de emails entre as duas tabelas

### 2. Controle de Acesso
- **ADMINs**: Podem criar novos operadores via `/auth/admin/usuarios`
- **Operadores**: Não podem criar outros operadores
- **Clientes**: Registro público via `/auth/cliente/register` ou OAuth

### 3. JWT com Tipo
- Payload inclui `user_type`: "usuario" ou "cliente"
- Permite middleware diferenciar permissões:
  - Operadores: Acesso ao sistema administrativo
  - Clientes: Acesso à loja online

### 4. Multi-tenancy
- Clientes vinculados a `empresa_id` (loja onde compraram)
- Operadores vinculados a `empresa_id` (loja onde trabalham)

---

## 📦 Migrações Necessárias

### 1. Rodar Migration
```bash
cd api-gateway
alembic upgrade head
```

Cria tabela `gateway.clientes_auth`.

### 2. Dados Existentes (Opcional)
Se já existem usuários OAuth na tabela `gateway.usuarios`:
1. Identificar quais são clientes (não operadores)
2. Migrar para `gateway.clientes_auth`
3. Criar registros em `clientes.clientes`

**Script de migração** (se necessário):
```sql
-- Identificar OAuth users (senha vazia)
SELECT id, email, nome, empresa_id 
FROM gateway.usuarios 
WHERE senha_hash = '' OR senha_hash IS NULL;

-- Migrar manualmente ou criar script Python
```

---

## 🚀 Deploy

### Ordem de Deploy:
1. **Backend**:
   - Rodar migration: `alembic upgrade head`
   - Deploy do gateway com novos routers
   
2. **Frontend**:
   - Deploy com LoginPage atualizado (sem OAuth)
   - Loja online deve usar `/auth/cliente/oauth/*`

### Verificações Pós-Deploy:
- ✅ Login de operadores funcionando em `/auth/login`
- ✅ Criação de operadores por ADMIN em `/auth/admin/usuarios`
- ✅ OAuth deprecated mas ainda funcional (temporário)
- ✅ Novos endpoints `/auth/cliente/*` acessíveis

---

## ⚠️ Breaking Changes

### 1. OAuth Deprecated
- Endpoints `/oauth/google` e `/oauth/microsoft` marcados como deprecated
- Clientes OAuth devem usar `/auth/cliente/oauth/*`

### 2. Register Deprecated
- Endpoint `/register` marcado como deprecated
- Operadores: Usar `/auth/admin/usuarios`
- Clientes: Usar `/auth/cliente/register`

### 3. JWT Payload Mudou
- Adicionado `user_type`: "usuario" | "cliente"
- Adicionado `empresa_id` (para clientes)

### 4. Frontend Login
- Removidos botões OAuth do login principal
- Operadores fazem login apenas com email/senha

---

## 📝 TODOs Futuros

### 1. Remover OAuth Deprecated (v3.0.0)
- Após migração completa, remover endpoints deprecated de `auth.py`

### 2. Frontend da Loja Online
- Criar página de login de cliente com OAuth
- Implementar registro público de cliente

### 3. Middleware de Autorização
- Criar middleware que verifica `user_type` do JWT
- Proteger rotas administrativas para `user_type="usuario"`
- Proteger rotas de loja para `user_type="cliente"`

### 4. Testes
- Testes unitários para `ClienteAuthRepository`
- Testes de integração dos novos endpoints
- Testes E2E do fluxo OAuth de cliente

---

## 📚 Documentação Adicional

### Arquitetura Atualizada

```
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  OPERADORES (Administração)         CLIENTES (Loja Online)   │
│  ┌───────────────────────┐          ┌────────────────────┐  │
│  │ /auth/login           │          │ /auth/cliente/*    │  │
│  │ /auth/admin/usuarios  │          │ - /register        │  │
│  │                       │          │ - /login           │  │
│  │ Tabela: usuarios      │          │ - /oauth/google/*  │  │
│  │ Role: ADMIN/OPERADOR  │          │ - /oauth/microsoft │  │
│  └───────────────────────┘          │                    │  │
│           │                          │ Tabela: clientes_  │  │
│           ├──────────────────────────┤        auth        │  │
│           │   JWT com user_type      │ Role: CLIENTE      │  │
│           │                          └────────────────────┘  │
│           ↓                                    ↓              │
│  ┌─────────────────────┐          ┌────────────────────────┐│
│  │  Sistema Admin      │          │  Serviço Clientes       ││
│  │  (Dashboard, etc)   │          │  (Dados completos)      ││
│  └─────────────────────┘          └────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Exemplo de Integração Frontend

```typescript
// Login de Operador (sistema)
const loginOperador = async (email: string, senha: string) => {
  const response = await api.post('/auth/login', {
    username: email,  // OAuth2PasswordRequestForm
    password: senha
  });
  
  // response.data.user.role = "ADMIN" ou "OPERADOR"
  // JWT payload: { user_type: "usuario", role: "ADMIN", ... }
};

// Login de Cliente (loja)
const loginCliente = async (email: string, senha: string) => {
  const response = await api.post('/auth/cliente/login', {
    username: email,
    password: senha
  });
  
  // response.data.user_type = "cliente"
  // JWT payload: { user_type: "cliente", role: "CLIENTE", empresa_id: 1 }
};

// OAuth de Cliente
const oauthCliente = async (provider: 'google' | 'microsoft') => {
  const empresaId = 1;  // ID da loja atual
  
  const { data } = await api.post(`/auth/cliente/oauth/${provider}/init`, {
    redirect_uri: window.location.origin + '/oauth/callback',
    empresa_id: empresaId
  });
  
  // Redirecionar para data.auth_url
  window.location.href = data.auth_url;
};
```

---

## ✅ Checklist de Implementação

- [x] Criar modelo `ClienteAuth`
- [x] Criar repository `ClienteAuthRepository`
- [x] Criar schemas de cliente
- [x] Atualizar JWT com `user_type`
- [x] Criar router `auth_cliente.py`
- [x] Criar router `auth_admin.py`
- [x] Deprecar OAuth em `auth.py`
- [x] Criar migration
- [x] Registrar routers em `main.py`
- [x] Atualizar frontend `LoginPage.tsx`
- [ ] Rodar migration no banco
- [ ] Testar criação de operador por ADMIN
- [ ] Testar registro de cliente
- [ ] Testar OAuth de cliente
- [ ] Criar frontend de login de cliente
- [ ] Documentar API no Swagger

---

**Autor**: Kiro AI  
**Revisão**: Pendente  
**Status**: Implementado (aguardando testes)
