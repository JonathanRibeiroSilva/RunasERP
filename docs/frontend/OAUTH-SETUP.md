# Configuração OAuth - Google e Microsoft

Este documento explica como configurar o login social com Google e Microsoft no frontend do ERP Runas.

---

## 📋 Visão Geral

O sistema suporta autenticação via:
- ✅ **Google** (Gmail)
- ✅ **Microsoft** (Outlook/Office 365)
- ✅ **Email/Senha** (tradicional)

Os usuários podem escolher qualquer método de login. Todos os métodos criam/atualizam o mesmo usuário no sistema.

---

## 🔐 Fluxo OAuth

1. Usuário clica em "Continuar com Google/Microsoft"
2. Frontend redireciona para o provider (Google/Microsoft)
3. Usuário faz login no provider e autoriza o app
4. Provider redireciona de volta para `/auth/callback` com um `code`
5. Frontend envia o `code` para o backend
6. Backend valida o `code` com o provider
7. Backend cria/atualiza o usuário e retorna tokens JWT
8. Frontend salva os tokens e redireciona para o dashboard

---

## 🔧 Configuração do Google OAuth

### 1. Criar Projeto no Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto ou selecione um existente
3. Nome sugerido: "ERP Runas"

### 2. Habilitar Google+ API

1. No menu lateral, vá em **APIs & Services** > **Library**
2. Procure por "Google+ API"
3. Clique em **Enable**

### 3. Configurar OAuth Consent Screen

1. Vá em **APIs & Services** > **OAuth consent screen**
2. Escolha **External** (para testes) ou **Internal** (se tiver Google Workspace)
3. Preencha:
   - **App name**: ERP Runas
   - **User support email**: seu email
   - **Developer contact**: seu email
4. Em **Scopes**, adicione:
   - `openid`
   - `profile`
   - `email`
5. Salve e continue

### 4. Criar Credenciais OAuth

1. Vá em **APIs & Services** > **Credentials**
2. Clique em **Create Credentials** > **OAuth client ID**
3. Escolha **Web application**
4. Preencha:
   - **Name**: ERP Runas Frontend
   - **Authorized JavaScript origins**:
     - `http://localhost:3000` (desenvolvimento)
     - `https://seu-dominio.com` (produção)
   - **Authorized redirect URIs**:
     - `http://localhost:3000/auth/callback` (desenvolvimento)
     - `https://seu-dominio.com/auth/callback` (produção)
5. Clique em **Create**
6. **Copie o Client ID** (você vai precisar dele)

### 5. Configurar no Frontend

Edite o arquivo `.env.development`:

```env
VITE_GOOGLE_CLIENT_ID=seu-client-id-aqui.apps.googleusercontent.com
VITE_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
```

Para produção (`.env.production`):

```env
VITE_GOOGLE_CLIENT_ID=seu-client-id-aqui.apps.googleusercontent.com
VITE_OAUTH_REDIRECT_URI=https://seu-dominio.com/auth/callback
```

---

## 🔧 Configuração do Microsoft OAuth

### 1. Criar App no Azure Portal

1. Acesse: https://portal.azure.com/
2. Vá em **Azure Active Directory** > **App registrations**
3. Clique em **New registration**
4. Preencha:
   - **Name**: ERP Runas
   - **Supported account types**: 
     - "Accounts in any organizational directory and personal Microsoft accounts" (recomendado)
   - **Redirect URI**: 
     - Platform: **Web**
     - URI: `http://localhost:3000/auth/callback`
5. Clique em **Register**

### 2. Configurar Autenticação

1. No app criado, vá em **Authentication**
2. Em **Platform configurations** > **Web**, adicione:
   - `http://localhost:3000/auth/callback` (desenvolvimento)
   - `https://seu-dominio.com/auth/callback` (produção)
3. Em **Implicit grant and hybrid flows**, marque:
   - ✅ **ID tokens**
4. Salve

### 3. Configurar Permissões

1. Vá em **API permissions**
2. Clique em **Add a permission**
3. Escolha **Microsoft Graph**
4. Escolha **Delegated permissions**
5. Adicione:
   - `openid`
   - `profile`
   - `email`
   - `User.Read`
6. Clique em **Add permissions**
7. Clique em **Grant admin consent** (se for admin)

### 4. Obter Client ID

1. Vá em **Overview**
2. **Copie o Application (client) ID**
3. **Copie o Directory (tenant) ID** (opcional - use "common" para multi-tenant)

### 5. Configurar no Frontend

Edite o arquivo `.env.development`:

```env
VITE_MICROSOFT_CLIENT_ID=seu-client-id-aqui
VITE_MICROSOFT_TENANT_ID=common
VITE_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
```

Para produção (`.env.production`):

```env
VITE_MICROSOFT_CLIENT_ID=seu-client-id-aqui
VITE_MICROSOFT_TENANT_ID=common
VITE_OAUTH_REDIRECT_URI=https://seu-dominio.com/auth/callback
```

**Nota:** Use `common` para aceitar contas pessoais e organizacionais. Use o Tenant ID específico para aceitar apenas contas da sua organização.

---

## 🔧 Configuração do Backend

O backend também precisa ser configurado para processar o OAuth. Adicione no `.env` do API Gateway:

```env
# Google OAuth
GOOGLE_CLIENT_ID=seu-client-id-aqui.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-client-secret-aqui

# Microsoft OAuth
MICROSOFT_CLIENT_ID=seu-client-id-aqui
MICROSOFT_CLIENT_SECRET=seu-client-secret-aqui
MICROSOFT_TENANT_ID=common
```

**⚠️ IMPORTANTE:** O Client Secret é necessário no backend, mas NÃO deve ser exposto no frontend!

---

## 🧪 Testar OAuth

### 1. Iniciar o Frontend

```bash
cd frontend
npm run dev
```

### 2. Acessar a Página de Login

Abra: http://localhost:3000/login

### 3. Testar Login Social

- Clique em "Continuar com Google" ou "Continuar com Microsoft"
- Faça login com sua conta
- Autorize o aplicativo
- Você deve ser redirecionado para o dashboard

### 4. Verificar Tokens

Abra o DevTools (F12) > Application > Local Storage:
- `access_token`: deve estar presente
- `refresh_token`: deve estar presente

---

## 🐛 Troubleshooting

### Erro: "OAuth não está configurado"

**Causa:** Client ID não foi configurado no `.env`

**Solução:** 
1. Verifique se o `.env.development` tem `VITE_GOOGLE_CLIENT_ID` ou `VITE_MICROSOFT_CLIENT_ID`
2. Reinicie o servidor de desenvolvimento (`npm run dev`)

### Erro: "redirect_uri_mismatch"

**Causa:** A URI de redirecionamento não está configurada no provider

**Solução:**
1. Verifique se `http://localhost:3000/auth/callback` está nas URIs autorizadas
2. Certifique-se de que a URI está exatamente igual (incluindo http/https, porta, etc)

### Erro: "Estado OAuth inválido"

**Causa:** Possível ataque CSRF ou problema com sessionStorage

**Solução:**
1. Limpe o sessionStorage do navegador
2. Tente fazer login novamente
3. Verifique se cookies de terceiros estão habilitados

### Erro: "invalid_client"

**Causa:** Client ID ou Client Secret incorretos no backend

**Solução:**
1. Verifique as credenciais no `.env` do backend
2. Certifique-se de que copiou o Client ID e Secret corretos

### Botões OAuth não aparecem

**Causa:** Client IDs não configurados

**Solução:**
1. Configure pelo menos um provider no `.env`
2. Reinicie o frontend
3. Os botões só aparecem se houver providers configurados

---

## 🔒 Segurança

### CSRF Protection

O sistema usa `state` parameter para proteção contra CSRF:
- Um state aleatório é gerado antes do redirect
- O state é salvo no sessionStorage
- Ao retornar, o state é validado

### Token Storage

- Tokens são armazenados no localStorage (MVP)
- Para produção, considere usar httpOnly cookies (mais seguro)

### HTTPS em Produção

⚠️ **IMPORTANTE:** Em produção, SEMPRE use HTTPS:
- OAuth providers exigem HTTPS para redirect URIs
- Tokens devem ser transmitidos apenas via HTTPS

---

## 📚 Referências

### Google OAuth
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)

### Microsoft OAuth
- [Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Azure Portal](https://portal.azure.com/)

---

## ✅ Checklist de Configuração

### Google OAuth
- [ ] Projeto criado no Google Cloud Console
- [ ] Google+ API habilitada
- [ ] OAuth Consent Screen configurado
- [ ] Credenciais OAuth criadas
- [ ] Redirect URIs configuradas
- [ ] Client ID copiado
- [ ] Client ID configurado no frontend `.env`
- [ ] Client ID e Secret configurados no backend `.env`
- [ ] Testado com sucesso

### Microsoft OAuth
- [ ] App registrado no Azure Portal
- [ ] Redirect URIs configuradas
- [ ] Permissões configuradas (openid, profile, email, User.Read)
- [ ] Client ID copiado
- [ ] Client ID configurado no frontend `.env`
- [ ] Client ID e Secret configurados no backend `.env`
- [ ] Testado com sucesso

---

**Última Atualização:** 2026-05-25  
**Versão:** 1.0.0
