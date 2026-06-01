# 🔧 Troubleshooting - Problemas com OAuth

Este guia consolida todas as soluções para problemas relacionados à autenticação OAuth (Google e Microsoft).

## 📋 Índice

1. [Erro: redirect_uri_mismatch](#1-erro-redirect_uri_mismatch)
2. [Infinite Page Reload](#2-infinite-page-reload)
3. [Página em Branco Após Callback](#3-página-em-branco-após-callback)
4. [Cookies Não Estão Sendo Setados](#4-cookies-não-estão-sendo-setados)
5. [401 Unauthorized ao Acessar /auth/me](#5-401-unauthorized-ao-acessar-authme)
6. [Invalid State Error](#6-invalid-state-error)
7. [ngrok URL Muda Após Reinicialização](#7-ngrok-url-muda-após-reinicialização)
8. [Frontend Não Consegue Conectar com Backend](#8-frontend-não-consegue-conectar-com-backend)
9. [CORS Error](#9-cors-error)
10. [Usuário Não Está Sendo Criado](#10-usuário-não-está-sendo-criado)

---

## 1. Erro: redirect_uri_mismatch

### Sintoma
Ao clicar em "Google", você vê:
```
You can't sign in because this app sent an invalid request.
Error 400: redirect_uri_mismatch
```

### Causa
A URL registrada no Google Console não corresponde à URL enviada pelo frontend.

### Solução

#### Passo 1: Obter URL atual do ngrok
```powershell
curl http://localhost:4040/api/tunnels 2>$null | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Select-Object -ExpandProperty public_url
```

Exemplo de saída:
```
https://pretty-dissuade-brunette.ngrok-free.dev
```

#### Passo 2: Atualizar Google Console

1. Ir para [Google Cloud Console](https://console.cloud.google.com/)
2. Selecionar seu projeto
3. **APIs & Services** → **Credentials**
4. Clicar no seu OAuth 2.0 Client ID
5. Em **Authorized redirect URIs**, verificar se existe:
   ```
   https://pretty-dissuade-brunette.ngrok-free.dev/auth/callback
   ```
6. Se não existir, adicionar e clicar em **Save**

#### Passo 3: Atualizar .env.development

Editar `frontend/.env.development`:
```env
VITE_OAUTH_REDIRECT_URI=https://pretty-dissuade-brunette.ngrok-free.dev/auth/callback
```

#### Passo 4: Reconstruir Frontend

```powershell
docker-compose down
docker-compose up -d --build erp-frontend-dev
```

#### Passo 5: Fazer o mesmo para Microsoft Azure

1. Ir para [Azure Portal](https://portal.azure.com/)
2. **Azure Active Directory** → **App registrations**
3. Selecionar sua aplicação
4. **Authentication**
5. Em **Redirect URIs**, adicionar:
   ```
   https://pretty-dissuade-brunette.ngrok-free.dev/auth/callback
   ```
6. Clicar em **Save**

---

## 2. Infinite Page Reload

### Sintoma
Ao acessar `/login`, a página fica recarregando infinitamente.

### Causa
O `AuthContext` estava executando `getCurrentUser()` múltiplas vezes, causando um loop.

### Solução

✅ **Já foi corrigido!** Verifique se você tem a versão mais recente:

```typescript
// frontend/src/contexts/AuthContext.tsx
const initAuthRef = React.useRef(false);

useEffect(() => {
  if (initAuthRef.current) {
    return;
  }
  initAuthRef.current = true;
  // ... resto do código
}, []);
```

Se ainda estiver com problema, limpar cache:
```powershell
docker-compose down -v
docker-compose up -d --build
```

---

## 3. Página em Branco Após Callback

### Sintoma
Você autoriza no Google, mas a página fica em branco.

### Causa
Erro no processamento do callback.

### Solução

#### Passo 1: Verificar Console do Navegador
1. Abrir DevTools (F12)
2. Ir para **Console** e procurar por erros

#### Passo 2: Verificar Logs do Backend
```bash
docker logs -f erp-api-gateway-dev
```

Procurar por:
- `oauth.google.callback.invalid_state` → State expirou
- `oauth.google.token_error` → Erro ao trocar code por token
- `oauth.google.userinfo_error` → Erro ao buscar dados do usuário

#### Passo 3: Soluções Específicas

**Se o erro for "Invalid state":**
- Tentar novamente (state expira em 10 minutos)

**Se o erro for "token_error":**
- Verificar se `GOOGLE_CLIENT_SECRET` está correto no backend

**Se o erro for "userinfo_error":**
- Verificar se o token do Google é válido
- Verificar se as permissões estão corretas

---

## 4. Cookies Não Estão Sendo Setados

### Sintoma
Você faz login, mas os cookies não aparecem no DevTools.

### Causa
Cookies HTTP-only não estão sendo definidos pelo backend.

### Solução

#### Passo 1: Verificar Logs do Backend
```bash
docker logs -f erp-api-gateway-dev | grep -i cookie
```

#### Passo 2: Testar Requisição de Login
```powershell
curl -i -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=test@example.com&password=password"
```

Procurar por `Set-Cookie` nos headers da resposta.

#### Passo 3: Verificar Configuração do Backend

```python
# backend/routers/auth.py
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,  # ← Deve ser True
    secure=True,    # ← Deve ser True para ngrok (HTTPS)
    samesite="lax",
    max_age=30 * 60,
    path="/"
)
```

---

## 5. 401 Unauthorized ao Acessar /auth/me

### Sintoma
Ao fazer login, você vê `GET /api/auth/me 401 Unauthorized` nos logs.

### Causa
Os cookies não estão sendo enviados ou não estão sendo validados.

### Solução

#### Passo 1: Verificar se os Cookies Existem
1. Abrir DevTools (F12)
2. Ir para **Application** → **Cookies**
3. Procurar por `access_token` e `refresh_token`

#### Passo 2: Se os Cookies Não Estiverem Lá
- Ver solução [#4 - Cookies Não Estão Sendo Setados](#4-cookies-não-estão-sendo-setados)

#### Passo 3: Se os Cookies Estiverem Lá
- Verificar se o backend está validando corretamente
- Verificar logs do backend:
```bash
docker logs -f erp-api-gateway-dev | grep -i "401\|unauthorized"
```

#### Passo 4: Verificar se o Token Expirou
- Tokens de acesso expiram em 30 minutos
- Se expirou, o backend deve usar o refresh_token para gerar um novo

---

## 6. Invalid State Error

### Sintoma
Ao fazer login, você vê:
```
Error: State inválido ou expirado
```

### Causa
O state expirou (mais de 10 minutos) ou não foi salvo no Redis.

### Solução

#### Passo 1: Verificar se o Redis Está Rodando
```bash
docker ps | grep redis
```

#### Passo 2: Se Não Estiver, Iniciar
```powershell
docker-compose up -d erp-redis-dev
```

#### Passo 3: Verificar se o State Foi Salvo
```bash
docker exec erp-redis-dev redis-cli keys "oauth:state:*"
```

#### Passo 4: Tentar Novamente
- Fazer login de novo (o state expira em 10 minutos)

#### Passo 5: Se o Problema Persistir
- Verificar logs do backend:
```bash
docker logs -f erp-api-gateway-dev | grep -i "oauth"
```

---

## 7. ngrok URL Muda Após Reinicialização

### Sintoma
Você reinicia os containers e a URL do ngrok muda.

### Causa
ngrok gera uma nova URL a cada reinicialização (sem plano pago).

### Solução

#### Opção 1: Atualizar Manualmente (Gratuito)

1. Obter a nova URL:
```powershell
curl http://localhost:4040/api/tunnels 2>$null | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Select-Object -ExpandProperty public_url
```

2. Atualizar Google Console com a nova URL
3. Atualizar Azure Portal com a nova URL
4. Atualizar `frontend/.env.development` com a nova URL
5. Reconstruir frontend:
```powershell
docker-compose down
docker-compose up -d --build
```

#### Opção 2: Usar URL Fixa (Pago)

1. Ir para [ngrok Dashboard](https://dashboard.ngrok.com/)
2. Configurar um **Static Domain**
3. Usar essa URL em todos os lugares
4. Nunca mais precisar atualizar!

---

## 8. Frontend Não Consegue Conectar com Backend

### Sintoma
Você vê erros de conexão nos logs do frontend.

### Causa
A URL da API está incorreta ou o backend não está acessível.

### Solução

#### Passo 1: Verificar se o Backend Está Rodando
```bash
docker ps | grep api-gateway
```

#### Passo 2: Verificar se a URL da API Está Correta
1. Abrir DevTools (F12)
2. Ir para **Console**
3. Digitar: `console.log(window.location.href)`
4. Verificar se a URL é a do ngrok

#### Passo 3: Verificar se o Backend Está Respondendo
```powershell
curl http://localhost:8000/docs
```

#### Passo 4: Se Não Estiver Respondendo
- Verificar logs:
```bash
docker logs -f erp-api-gateway-dev
```

#### Passo 5: Se o Backend Estiver Rodando mas Não Respondendo
- Pode ser um problema de rede
- Tentar reconstruir:
```powershell
docker-compose down
docker-compose up -d --build
```

---

## 9. CORS Error

### Sintoma
Você vê erro de CORS no console do navegador.

### Causa
O backend não está configurado para aceitar requisições do frontend.

### Solução

#### Passo 1: Verificar Configuração do Backend

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← Deve permitir a origem do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Passo 2: Se Não Estiver, Adicionar a Configuração

#### Passo 3: Reconstruir Backend
```powershell
docker-compose down
docker-compose up -d --build erp-api-gateway-dev
```

---

## 10. Usuário Não Está Sendo Criado

### Sintoma
Você faz login com Google, mas o usuário não aparece no banco de dados.

### Causa
Erro ao criar o usuário ou ao buscar dados do Google.

### Solução

#### Passo 1: Verificar Logs do Backend
```bash
docker logs -f erp-api-gateway-dev | grep -i "user_created\|user_login"
```

#### Passo 2: Se Não Houver Nenhuma Mensagem
- O backend não está processando o callback

#### Passo 3: Verificar se Há Erro
```bash
docker logs -f erp-api-gateway-dev | grep -i "error\|exception"
```

#### Passo 4: Se o Erro For "Email já cadastrado"
- O usuário já existe no banco de dados
- Tentar fazer login novamente

#### Passo 5: Se o Erro For Outro
- Verificar se o banco de dados está rodando:
```bash
docker ps | grep postgres
```

#### Passo 6: Se Não Estiver, Iniciar
```powershell
docker-compose up -d erp-db-gateway-dev
```

---

## 📋 Checklist de Verificação

Quando algo der errado, verificar nesta ordem:

- [ ] ngrok está rodando?
  ```bash
  docker ps | grep ngrok
  ```

- [ ] Frontend está rodando?
  ```bash
  docker ps | grep frontend
  ```

- [ ] Backend está rodando?
  ```bash
  docker ps | grep api-gateway
  ```

- [ ] Redis está rodando?
  ```bash
  docker ps | grep redis
  ```

- [ ] PostgreSQL está rodando?
  ```bash
  docker ps | grep postgres
  ```

- [ ] URL do ngrok está correta?
  ```powershell
  curl http://localhost:4040/api/tunnels
  ```

- [ ] URL está registrada no Google Console?
  - Verificar Authorized redirect URIs

- [ ] URL está registrada no Azure Portal?
  - Verificar Redirect URIs

- [ ] `.env.development` está atualizado?
  - Verificar `VITE_OAUTH_REDIRECT_URI`

- [ ] Frontend foi reconstruído?
  ```powershell
  docker-compose down
  docker-compose up -d --build
  ```

---

## 🔍 Comandos Úteis

```bash
# Ver todos os containers
docker ps

# Ver logs de um container
docker logs -f [container-name]

# Entrar em um container
docker exec -it [container-name] bash

# Verificar URL do ngrok
curl http://localhost:4040/api/tunnels

# Verificar se a API está respondendo
curl http://localhost:8000/docs

# Verificar cookies no Redis
docker exec erp-redis-dev redis-cli keys "oauth:state:*"

# Limpar tudo e reconstruir
docker-compose down -v
docker-compose up -d --build

# Ver logs de todos os containers
docker-compose logs -f
```

---

## 📞 Quando Pedir Ajuda

Se nenhuma solução funcionar, forneça:

1. **Erro exato** que você está vendo
2. **Logs** do frontend, backend e ngrok
3. **URL do ngrok** atual
4. **Passos** que você fez para reproduzir o erro
5. **Configuração** do Google Console e Azure Portal

### Exemplo de Relatório de Erro

```
Erro: Error 400: redirect_uri_mismatch

URL do ngrok: https://pretty-dissuade-brunette.ngrok-free.dev

Google Console:
- Authorized redirect URIs: https://pretty-dissuade-brunette.ngrok-free.dev/auth/callback

Frontend .env.development:
- VITE_OAUTH_REDIRECT_URI=https://pretty-dissuade-brunette.ngrok-free.dev/auth/callback

Logs do backend:
[aqui os logs]

Passos para reproduzir:
1. Acessar https://pretty-dissuade-brunette.ngrok-free.dev/login
2. Clicar em "Google"
3. Ver erro 400
```

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0 (MVP)
