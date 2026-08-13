# Configuração de Provedores OAuth2 (Google Cloud e Microsoft Azure)

## 📋 Visão Geral

Este documento detalha como configurar corretamente as URIs de redirecionamento nos consoles do Google Cloud Platform e Microsoft Azure para autenticação OAuth2 no sistema ERP.

## 🔑 Informações Importantes

### URLs do Sistema

#### 🌐 Produção (Cloudflare Tunnel)
- **Base URL**: `https://runaserp.com.br`
- **Base URL (www)**: `https://www.runaserp.com.br`
- **Callback Google**: `https://runaserp.com.br/oauth/google/callback`
- **Callback Microsoft**: `https://runaserp.com.br/oauth/microsoft/callback`

#### 💻 Desenvolvimento Local
- **Base URL**: `http://localhost:3000`
- **Callback Google**: `http://localhost:3000/oauth/google/callback`
- **Callback Microsoft**: `http://localhost:3000/oauth/microsoft/callback`

### Rotas do Backend (API Gateway)

As rotas do backend que processam os callbacks OAuth2 são:
- **Google Init**: `POST /auth/cliente/oauth/google/init`
- **Google Callback**: `POST /auth/cliente/oauth/google/callback`
- **Microsoft Init**: `POST /auth/cliente/oauth/microsoft/init`
- **Microsoft Callback**: `POST /auth/cliente/oauth/microsoft/callback`

> **⚠️ ATENÇÃO**: As rotas `/auth/oauth/*` (sem `/cliente`) estão **deprecated** e serão removidas. Use sempre as rotas `/auth/cliente/oauth/*`.

---

## 🟦 Google Cloud Platform (GCP)

### 1. Acesse o Console do Google Cloud

1. Vá para [Google Cloud Console](https://console.cloud.google.com/)
2. Selecione seu projeto ou crie um novo
3. No menu lateral, vá em **APIs e Serviços** → **Credenciais**

### 2. Criar Credenciais OAuth 2.0

1. Clique em **+ CRIAR CREDENCIAIS** → **ID do cliente OAuth**
2. Tipo de aplicativo: **Aplicativo da Web**
3. Nome: `Runas ERP - OAuth Cliente`

### 3. Configurar URIs Autorizadas

#### **Origens JavaScript autorizadas**
Adicione as seguintes URLs:

```
https://runaserp.com.br
https://www.runaserp.com.br
http://localhost:3000
```

#### **URIs de redirecionamento autorizadas**
Adicione as seguintes URLs:

```
https://runaserp.com.br/oauth/google/callback
https://www.runaserp.com.br/oauth/google/callback
http://localhost:3000/oauth/google/callback
```

### 4. Obter Credenciais

Após salvar, você receberá:
- **Client ID**: `SEU_GOOGLE_CLIENT_ID.apps.googleusercontent.com`
- **Client Secret**: `SEU_GOOGLE_CLIENT_SECRET`

### 5. Configurar Tela de Consentimento OAuth

1. Vá em **APIs e Serviços** → **Tela de consentimento OAuth**
2. Tipo de usuário: **Externo** (para permitir qualquer usuário do Google)
3. Preencha as informações:
   - **Nome do app**: Runas ERP
   - **E-mail de suporte do usuário**: seu-email@dominio.com
   - **Domínios autorizados**: `runaserp.com.br`
   - **E-mail do desenvolvedor**: seu-email@dominio.com

4. **Escopos** (Adicionar os seguintes escopos):
   - `openid`
   - `email`
   - `profile`

5. Salve e continue

### 6. Adicionar Usuários de Teste (Modo Teste)

Se o app estiver em **modo de teste**, você precisa adicionar os emails que poderão fazer login:
1. Vá em **Tela de consentimento OAuth** → **Usuários de teste**
2. Clique em **+ ADD USERS**
3. Adicione os e-mails dos testadores

> **💡 Dica**: Para liberar para qualquer usuário do Google, publique o app (precisa de revisão do Google para apps em produção).

### 7. Variáveis de Ambiente

Adicione no arquivo `.env`:

```env
# OAuth Google
GOOGLE_CLIENT_ID=SEU_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=SEU_GOOGLE_CLIENT_SECRET
```

---

## 🟦 Microsoft Azure (Azure AD / Entra ID)

### 1. Acesse o Portal do Azure

1. Vá para [Azure Portal](https://portal.azure.com/)
2. No menu lateral, vá em **Microsoft Entra ID** (antigo Azure Active Directory)
3. Clique em **Registros de aplicativo**

### 2. Criar Novo Registro de Aplicativo

1. Clique em **+ Novo registro**
2. Preencha as informações:
   - **Nome**: `Runas ERP - OAuth Cliente`
   - **Tipos de conta com suporte**: Contas em qualquer diretório organizacional e contas pessoais da Microsoft
   - **URI de redirecionamento**: (configurar na próxima etapa)

3. Clique em **Registrar**

### 3. Configurar URIs de Redirecionamento

1. No menu lateral do app, clique em **Autenticação**
2. Clique em **+ Adicionar uma plataforma** → **Web**
3. Adicione as seguintes URIs de redirecionamento:

```
https://runaserp.com.br/oauth/microsoft/callback
https://www.runaserp.com.br/oauth/microsoft/callback
http://localhost:3000/oauth/microsoft/callback
```

4. Em **Concessão implícita e fluxos híbridos**, marque:
   - ✅ **Tokens de ID** (usados para OpenID Connect)

5. Em **Tipos de conta com suporte**, certifique-se de que está marcado:
   - ✅ **Contas em qualquer diretório organizacional (Qualquer diretório do Azure AD - Multilocatário) e contas pessoais da Microsoft (por exemplo, Skype, Xbox)**

6. Clique em **Salvar**

### 4. Obter Credenciais

1. No menu lateral, clique em **Visão geral**
2. Copie os seguintes valores:
   - **ID do aplicativo (cliente)**: `SEU_MICROSOFT_CLIENT_ID`
   - **ID do diretório (locatário)**: `SEU_MICROSOFT_TENANT_ID`

3. No menu lateral, clique em **Certificados e segredos**
4. Clique em **+ Novo segredo do cliente**
5. Descrição: `Runas ERP OAuth Secret`
6. Validade: **24 meses** (recomendado)
7. Clique em **Adicionar**
8. **⚠️ IMPORTANTE**: Copie o **Valor** imediatamente (não será exibido novamente)

### 5. Configurar Permissões da API

1. No menu lateral, clique em **Permissões de API**
2. Verifique se as seguintes permissões do **Microsoft Graph** estão adicionadas:
   - ✅ `openid` (Sign users in)
   - ✅ `email` (View users' email address)
   - ✅ `profile` (View users' basic profile)
   - ✅ `User.Read` (Sign in and read user profile)

3. Se não estiverem, clique em **+ Adicionar uma permissão** → **Microsoft Graph** → **Permissões delegadas**
4. Adicione as permissões acima
5. Clique em **Adicionar permissões**

### 6. Variáveis de Ambiente

Adicione no arquivo `.env`:

```env
# OAuth Microsoft
MICROSOFT_CLIENT_ID=SEU_MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET=SEU_MICROSOFT_CLIENT_SECRET
MICROSOFT_TENANT_ID=common
```

> **💡 Nota**: Use `MICROSOFT_TENANT_ID=common` para permitir contas pessoais e organizacionais. Use um Tenant ID específico para restringir a um diretório Azure AD.

---

## 🔄 Fluxo de Autenticação OAuth2

### Diagrama do Fluxo

```
┌─────────┐          ┌──────────┐          ┌─────────────┐          ┌──────────┐
│ Cliente │          │ Frontend │          │ API Gateway │          │ Provider │
│ (User)  │          │ (React)  │          │  (FastAPI)  │          │(G/MS)    │
└────┬────┘          └─────┬────┘          └──────┬──────┘          └────┬─────┘
     │                     │                       │                      │
     │ 1. Clica "Login"    │                       │                      │
     │────────────────────>│                       │                      │
     │                     │                       │                      │
     │                     │ 2. POST /oauth/google/init                  │
     │                     │      {redirect_uri}   │                      │
     │                     │──────────────────────>│                      │
     │                     │                       │                      │
     │                     │ 3. {auth_url, state}  │                      │
     │                     │<──────────────────────│                      │
     │                     │                       │                      │
     │ 4. Redireciona para auth_url                                       │
     │────────────────────────────────────────────────────────────────────>│
     │                     │                       │                      │
     │ 5. Usuário autoriza │                       │                      │
     │<────────────────────────────────────────────────────────────────────│
     │                     │                       │                      │
     │ 6. Callback: /oauth/google/callback?code=XXX&state=YYY             │
     │────────────────────>│                       │                      │
     │                     │                       │                      │
     │                     │ 7. POST /oauth/google/callback               │
     │                     │      {code, state}    │                      │
     │                     │──────────────────────>│                      │
     │                     │                       │                      │
     │                     │                       │ 8. Exchange code     │
     │                     │                       │    for token         │
     │                     │                       │─────────────────────>│
     │                     │                       │                      │
     │                     │                       │ 9. Access token      │
     │                     │                       │<─────────────────────│
     │                     │                       │                      │
     │                     │                       │ 10. Get user info    │
     │                     │                       │─────────────────────>│
     │                     │                       │                      │
     │                     │                       │ 11. User data        │
     │                     │                       │<─────────────────────│
     │                     │                       │                      │
     │                     │ 12. {access_token,    │                      │
     │                     │      refresh_token,   │                      │
     │                     │      user}            │                      │
     │                     │<──────────────────────│                      │
     │                     │                       │                      │
     │ 13. Authenticated   │                       │                      │
     │<────────────────────│                       │                      │
```

### Explicação do Fluxo

1. **Frontend** solicita URL de autorização ao backend
2. **Backend** gera `state` (CSRF token), salva no Redis e retorna URL
3. **Frontend** redireciona usuário para o provedor OAuth (Google/Microsoft)
4. Usuário autoriza o app no provedor
5. **Provedor** redireciona de volta com `code` e `state`
6. **Frontend** envia `code` e `state` para o backend
7. **Backend** valida `state`, troca `code` por `access_token`
8. **Backend** usa `access_token` para obter dados do usuário
9. **Backend** cria/atualiza usuário no banco e retorna JWT tokens
10. **Frontend** armazena tokens e autentica usuário

---

## 🧪 Testando a Configuração

### 1. Verificar Variáveis de Ambiente

```powershell
# Verifique se as variáveis estão configuradas no .env
Get-Content .env | Select-String "GOOGLE_CLIENT_ID|MICROSOFT_CLIENT_ID"
```

### 2. Reiniciar o API Gateway

```powershell
# Parar containers
docker-compose -f docker-compose.dev.yml down api-gateway

# Subir novamente
docker-compose -f docker-compose.dev.yml up -d api-gateway

# Verificar logs
docker logs erp-api-gateway-dev -f
```

### 3. Iniciar Cloudflare Tunnel (se ainda não estiver rodando)

```powershell
# Verificar se o tunnel está rodando
docker ps | findstr cloudflared

# Se não estiver, iniciar com docker-compose
docker-compose -f docker-compose.cloudflare.yml up -d

# Verificar logs
docker logs erp-cloudflared -f
```

### 4. Testar o Fluxo OAuth (Google)

```powershell
# 1. Iniciar OAuth flow
$prodUrl = "https://runaserp.com.br"
$initResponse = Invoke-WebRequest -Uri "$prodUrl/auth/cliente/oauth/google/init" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"redirect_uri":"https://runaserp.com.br/oauth/google/callback"}' `
    -UseBasicParsing | ConvertFrom-Json

Write-Output "Auth URL: $($initResponse.auth_url)"
Write-Output "State: $($initResponse.state)"

# 2. Abrir URL no navegador
Start-Process $initResponse.auth_url
```

### 5. Testar o Fluxo OAuth (Microsoft)

```powershell
# 1. Iniciar OAuth flow
$prodUrl = "https://runaserp.com.br"
$initResponse = Invoke-WebRequest -Uri "$prodUrl/auth/cliente/oauth/microsoft/init" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"redirect_uri":"https://runaserp.com.br/oauth/microsoft/callback"}' `
    -UseBasicParsing | ConvertFrom-Json

Write-Output "Auth URL: $($initResponse.auth_url)"
Write-Output "State: $($initResponse.state)"

# 2. Abrir URL no navegador
Start-Process $initResponse.auth_url
```

---

## 🛠️ Troubleshooting

### Erro: "redirect_uri_mismatch" (Google)

**Causa**: A URI de redirecionamento não está registrada no Google Cloud Console.

**Solução**:
1. Verifique se a URL está **exatamente igual** no console (incluindo `http://` ou `https://`)
2. Certifique-se de não ter espaços em branco antes/depois da URL
3. Aguarde alguns minutos após adicionar a URI (propagação)
4. Teste com ambas as variantes: `https://runaserp.com.br` e `https://www.runaserp.com.br`

### Erro: "AADSTS50011: Invalid reply URL" (Microsoft)

**Causa**: A URI de redirecionamento não está registrada no Azure.

**Solução**:
1. Verifique em **Autenticação** → **Web** se a URL está correta
2. Certifique-se de que está usando o protocolo correto (`https://` para produção)
3. Verifique se marcou **Tokens de ID** em **Concessão implícita**
4. Teste com ambas as variantes: `https://runaserp.com.br` e `https://www.runaserp.com.br`

### Erro: "State inválido ou expirado"

**Causa**: O `state` expirou no Redis (tempo > 10 minutos) ou não existe.

**Solução**:
1. Verifique se o Redis está rodando: `docker ps | grep redis`
2. Reduza o tempo entre iniciar o flow e fazer o callback
3. Verifique logs do backend: `docker logs erp-api-gateway-dev -f`

### Erro: "OAuth Google/Microsoft não configurado"

**Causa**: Variáveis de ambiente não estão definidas.

**Solução**:
1. Verifique se o `.env` contém `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, etc.
2. Reinicie o container do API Gateway
3. Verifique logs: `docker logs erp-api-gateway-dev`

### Erro: "Access blocked: This app's request is invalid" (Google)

**Causa**: O app está em modo de teste e o usuário não está na lista de testadores.

**Solução**:
1. Vá no Google Cloud Console → **Tela de consentimento OAuth** → **Usuários de teste**
2. Adicione o e-mail do usuário testador
3. OU publique o app para produção (requer revisão do Google)

---

## 📚 Referências

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform OAuth 2.0](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [RFC 6749: OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

---

---

## 📝 Resumo Rápido - URLs para Configurar

### Google Cloud Platform

**Console**: https://console.cloud.google.com/apis/credentials

**Origens JavaScript autorizadas:**
```
https://runaserp.com.br
https://www.runaserp.com.br
http://localhost:3000
```

**URIs de redirecionamento:**
```
https://runaserp.com.br/oauth/google/callback
https://www.runaserp.com.br/oauth/google/callback
http://localhost:3000/oauth/google/callback
```

### Microsoft Azure

**Console**: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade

**URIs de redirecionamento (Web):**
```
https://runaserp.com.br/oauth/microsoft/callback
https://www.runaserp.com.br/oauth/microsoft/callback
http://localhost:3000/oauth/microsoft/callback
```

**Permissões necessárias:**
- openid
- email
- profile
- User.Read

---

## ✅ Checklist de Configuração

### Google Cloud Platform
- [ ] Projeto criado no Google Cloud Console
- [ ] Credenciais OAuth 2.0 criadas (Aplicativo da Web)
- [ ] Origens JavaScript autorizadas configuradas
- [ ] URIs de redirecionamento autorizadas configuradas
- [ ] Tela de consentimento OAuth configurada
- [ ] Escopos adicionados (openid, email, profile)
- [ ] Usuários de teste adicionados (se em modo teste)
- [ ] Client ID e Secret adicionados no `.env`

### Microsoft Azure
- [ ] Aplicativo registrado no Azure AD / Entra ID
- [ ] URIs de redirecionamento configuradas (Web)
- [ ] Tokens de ID habilitados
- [ ] Tipos de conta multilocatário configurados
- [ ] Segredo do cliente criado
- [ ] Permissões da API configuradas (openid, email, profile, User.Read)
- [ ] Client ID, Secret e Tenant ID adicionados no `.env`

### Backend (API Gateway)
- [ ] Variáveis de ambiente configuradas no `.env`
- [ ] Container do API Gateway reiniciado
- [ ] Cloudflare Tunnel rodando (para acesso HTTPS em produção)
- [ ] Rotas `/auth/cliente/oauth/*` funcionando

### Frontend
- [ ] Componente de login OAuth implementado
- [ ] Callbacks `/oauth/google/callback` e `/oauth/microsoft/callback` configurados
- [ ] Armazenamento de tokens implementado (cookies ou localStorage)

---

**Última atualização**: 24 de junho de 2026
**Autor**: Equipe Runas ERP
