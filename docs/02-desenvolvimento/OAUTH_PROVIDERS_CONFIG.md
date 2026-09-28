# Configuração de Provedores OAuth2 (Google Cloud e Microsoft Azure)

## 📋 Visão Geral

Este documento detalha como configurar os consoles do Google Cloud Platform e do Microsoft Azure (Entra ID) para o login social do **cliente comprador da loja online**. O login do painel (`/login`) não usa OAuth. O fluxo ponta a ponta está em [OAUTH_FLUXO_COMPLETO.md](./OAUTH_FLUXO_COMPLETO.md).

## 🔑 Informações Importantes

### URLs do Sistema

O `redirect_uri` é montado no navegador como `${window.location.origin}/auth/callback/{google|microsoft}` (`CheckoutPage.tsx` e `ClienteLoginPage.tsx`) e repassado ao gateway no `init`. Ele precisa estar registrado **exatamente** assim no console de cada provedor, para cada origem de onde a loja é aberta.

#### 🌐 Produção
- **Base URL**: `https://app.runaserp.com.br` (`FRONTEND_URL` em `.env.production.example`; em prod o ingress do tunnel fica no painel Cloudflare Zero Trust, conforme o comentário do serviço `cloudflared` em `docker-compose.prod.yml` — `cloudflared-config.yml` é o tunnel de **dev**, que aponta o mesmo hostname para `frontend-dev:3000`)
- **Callback Google**: `https://app.runaserp.com.br/auth/callback/google`
- **Callback Microsoft**: `https://app.runaserp.com.br/auth/callback/microsoft`

> **⚠️ Atenção**: `runaserp.com.br` (sem `app.`) é a landing no Cloudflare Pages, fora do tunnel — não serve a loja nem o callback.

#### 💻 Desenvolvimento Local
- **Base URL**: `http://localhost:3000`
- **Callback Google**: `http://localhost:3000/auth/callback/google`
- **Callback Microsoft**: `http://localhost:3000/auth/callback/microsoft`

### Rotas do Backend (API Gateway)

Definidas em `api-gateway/routers/auth_cliente.py` (router `prefix="/auth/cliente"`). Pelo navegador ficam atrás do prefixo `/api` (o nginx/Vite o remove antes de chegar ao gateway):
- **Google Init**: `POST /auth/cliente/oauth/google/init`
- **Google Callback**: `POST /auth/cliente/oauth/google/callback`
- **Microsoft Init**: `POST /auth/cliente/oauth/microsoft/init`
- **Microsoft Callback**: `POST /auth/cliente/oauth/microsoft/callback`

Não existem rotas `/auth/oauth/*` (sem `/cliente`) no gateway.

---

## 🟦 Google Cloud Platform (GCP)

### 1. Acesse o Console do Google Cloud

1. Vá para [Google Cloud Console](https://console.cloud.google.com/)
2. Selecione seu projeto ou crie um novo
3. No menu lateral, vá em **APIs e Serviços** → **Credenciais**

### 2. Criar Credenciais OAuth 2.0

1. Clique em **+ CRIAR CREDENCIAIS** → **ID do cliente OAuth**
2. Tipo de aplicativo: **Aplicativo da Web**
3. Nome: livre (ex.: `Runas ERP - OAuth Cliente`)

### 3. Configurar URIs Autorizadas

#### **Origens JavaScript autorizadas**

O fluxo é server-side (authorization code trocado pelo gateway), então o código não depende desta lista. Adicionar as origens não atrapalha:

```
https://app.runaserp.com.br
http://localhost:3000
```

#### **URIs de redirecionamento autorizadas**

```
https://app.runaserp.com.br/auth/callback/google
http://localhost:3000/auth/callback/google
```

Se a loja também for aberta por outra origem (ex.: um túnel ngrok em dev), registre `<origem>/auth/callback/google` dela também.

### 4. Obter Credenciais

Após salvar, você receberá:
- **Client ID**: `SEU_GOOGLE_CLIENT_ID.apps.googleusercontent.com`
- **Client Secret**: `SEU_GOOGLE_CLIENT_SECRET`

### 5. Configurar Tela de Consentimento OAuth

1. Vá em **APIs e Serviços** → **Tela de consentimento OAuth**
2. Tipo de usuário: **Externo** (para permitir qualquer conta Google)
3. Preencha:
   - **Nome do app**: Runas ERP
   - **E-mail de suporte do usuário**: seu-email@dominio.com
   - **Domínios autorizados**: `runaserp.com.br`
   - **E-mail do desenvolvedor**: seu-email@dominio.com

4. **Escopos** — os que o gateway pede em `oauth_google_init_cliente`:
   - `openid`
   - `email`
   - `profile`

5. Salve e continue

### 6. Adicionar Usuários de Teste (Modo Teste)

Se o app estiver em **modo de teste**, só os e-mails cadastrados conseguem logar:
1. Vá em **Tela de consentimento OAuth** → **Usuários de teste**
2. Clique em **+ ADD USERS**
3. Adicione os e-mails dos testadores

> **💡 Dica**: Para liberar para qualquer conta Google, publique o app.

### 7. Variáveis de Ambiente

Lidas por `api-gateway/config.py` e repassadas ao container do gateway em `docker-compose.dev.yml` e `docker-compose.prod.yml`:

```env
# OAuth Google
GOOGLE_CLIENT_ID=SEU_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=SEU_GOOGLE_CLIENT_SECRET
```

---

## 🟦 Microsoft Azure (Entra ID)

### 1. Acesse o Portal do Azure

1. Vá para [Azure Portal](https://portal.azure.com/)
2. No menu lateral, vá em **Microsoft Entra ID** (antigo Azure Active Directory)
3. Clique em **Registros de aplicativo**

### 2. Criar Novo Registro de Aplicativo

1. Clique em **+ Novo registro**
2. Preencha:
   - **Nome**: livre (ex.: `Runas ERP - OAuth Cliente`)
   - **Tipos de conta com suporte**: Contas em qualquer diretório organizacional e contas pessoais da Microsoft (necessário para o tenant `common`, que é o default)
   - **URI de redirecionamento**: (configurar na próxima etapa)

3. Clique em **Registrar**

### 3. Configurar URIs de Redirecionamento

1. No menu lateral do app, clique em **Autenticação**
2. Clique em **+ Adicionar uma plataforma** → **Web** (o segredo do cliente é usado pelo gateway na troca do code)
3. Adicione:

```
https://app.runaserp.com.br/auth/callback/microsoft
http://localhost:3000/auth/callback/microsoft
```

4. **Concessão implícita e fluxos híbridos**: não é necessário marcar nada — o gateway usa `response_type=code` e não lê `id_token`.

5. Clique em **Salvar**

### 4. Obter Credenciais

1. No menu lateral, clique em **Visão geral**
2. Copie:
   - **ID do aplicativo (cliente)**: `SEU_MICROSOFT_CLIENT_ID`
   - **ID do diretório (locatário)**: `SEU_MICROSOFT_TENANT_ID` (só se for restringir a um diretório)

3. No menu lateral, clique em **Certificados e segredos**
4. Clique em **+ Novo segredo do cliente**
5. Descreva e escolha a validade
6. Clique em **Adicionar**
7. **⚠️ IMPORTANTE**: Copie o **Valor** imediatamente (não será exibido novamente)

### 5. Configurar Permissões da API

O gateway pede `scope=openid email profile User.Read` e lê o perfil em `https://graph.microsoft.com/v1.0/me`. Em **Permissões de API** → **Microsoft Graph** → **Permissões delegadas**, confirme:
- ✅ `openid`
- ✅ `email`
- ✅ `profile`
- ✅ `User.Read`

### 6. Variáveis de Ambiente

```env
# OAuth Microsoft
MICROSOFT_CLIENT_ID=SEU_MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET=SEU_MICROSOFT_CLIENT_SECRET
MICROSOFT_TENANT_ID=common
```

> **💡 Nota**: `MICROSOFT_TENANT_ID` tem default `common` em `config.py` (contas pessoais e organizacionais). Um Tenant ID específico restringe o login àquele diretório.

### Variáveis `VITE_*` de OAuth

O `.env.example` também lista `VITE_GOOGLE_CLIENT_ID`, `VITE_MICROSOFT_CLIENT_ID`, `VITE_MICROSOFT_TENANT_ID` e `VITE_OAUTH_REDIRECT_URI`, lidas em `frontend/src/config/env.ts` (`config.oauth`). Nenhum código usa `config.oauth` hoje: o frontend não precisa delas para o login funcionar.

---

## 🔄 Fluxo de Autenticação OAuth2

### Diagrama do Fluxo

```
┌─────────┐          ┌──────────┐          ┌─────────────┐          ┌──────────┐
│ Cliente │          │ Frontend │          │ API Gateway │          │ Provider │
│ (User)  │          │ (React)  │          │  (FastAPI)  │          │(G/MS)    │
└────┬────┘          └─────┬────┘          └──────┬──────┘          └────┬─────┘
     │                     │                       │                      │
     │ 1. Clica "Entrar    │                       │                      │
     │    com Google"      │                       │                      │
     │────────────────────>│                       │                      │
     │                     │                       │                      │
     │                     │ 2. POST /api/auth/cliente/oauth/google/init  │
     │                     │      {redirect_uri, empresa_id}              │
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
     │ 6. /auth/callback/google?code=XXX&state=YYY │                      │
     │────────────────────>│                       │                      │
     │                     │                       │                      │
     │                     │ 7. POST /api/auth/cliente/oauth/google/callback
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
     │                     │ 12. Set-Cookie +      │                      │
     │                     │     {access_token,    │                      │
     │                     │      refresh_token,   │                      │
     │                     │      cliente}         │                      │
     │                     │<──────────────────────│                      │
     │                     │                       │                      │
     │ 13. Autenticado     │                       │                      │
     │<────────────────────│                       │                      │
```

### Explicação do Fluxo

1. **Frontend** pede a URL de autorização ao gateway (`redirect_uri` + `empresa_id` da loja)
2. **Gateway** gera `state` (CSRF token), salva no Redis por 10 minutos junto com `redirect_uri` e `empresa_id` e retorna `auth_url`
3. **Frontend** guarda o `state` no `sessionStorage` e redireciona para o provedor
4. Usuário autoriza o app no provedor
5. **Provedor** redireciona para `/auth/callback/{provider}` com `code` e `state`
6. **Frontend** confere o `state` e envia `code` e `state` ao gateway
7. **Gateway** valida e apaga o `state`, troca o `code` por `access_token`
8. **Gateway** usa o `access_token` para obter e-mail e nome
9. **Gateway** busca/cria o cliente no serviço de clientes, emite os JWT e seta os cookies HTTP-only `access_token`/`refresh_token`
10. **Frontend** volta para a página de origem já autenticado pelo cookie

---

## 🧪 Testando a Configuração

### 1. Verificar Variáveis de Ambiente

```powershell
# Verifique se as variáveis estão no .env (a saída mostra os valores; não cole em lugar público)
Get-Content .env | Select-String "GOOGLE_CLIENT_ID|MICROSOFT_CLIENT_ID"
```

### 2. Recriar o API Gateway (dev)

As variáveis entram no container por `environment:` no compose, então é preciso recriar o container (um `docker restart` não relê o `.env`):

```powershell
docker compose -f docker-compose.dev.yml up -d --force-recreate api-gateway

# Verificar logs
docker logs erp-api-gateway-dev -f
```

Em produção as variáveis vêm do ambiente configurado no Coolify e entram num novo deploy. A CONFIRMAR: procedimento exato no painel do Coolify.

### 3. Cloudflare Tunnel

Em produção o tunnel é o serviço `cloudflared` de `docker-compose.prod.yml` (container `erp-cloudflared-prod`). Para expor o ambiente de dev em `app.runaserp.com.br` existe `docker-compose.cloudflare.yml` (container `erp-cloudflared`), que não é standalone — é uma extensão do compose de dev:

```powershell
docker ps --filter "name=cloudflared"
docker compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
docker logs erp-cloudflared -f
```

### 4. Testar o Init (Google)

O body exige `redirect_uri` **e** `empresa_id` (sem `empresa_id` o FastAPI responde 422). Pelo navegador, as rotas ficam sob `/api`. Em dev dá para chamar o gateway direto na porta 8000:

```powershell
$body = '{"redirect_uri":"http://localhost:3000/auth/callback/google","empresa_id":1}'
$initResponse = Invoke-RestMethod -Uri "http://localhost:8000/auth/cliente/oauth/google/init" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

Write-Output "Auth URL: $($initResponse.auth_url)"
Write-Output "State: $($initResponse.state)"

Start-Process $initResponse.auth_url
```

Troque `empresa_id` por um id existente. Isso só valida o `init` e a tela do provedor: o callback precisa do `state` no `sessionStorage` da aba, então o teste completo é pelo checkout da loja (ver [OAUTH_FLUXO_COMPLETO.md](./OAUTH_FLUXO_COMPLETO.md)).

### 5. Testar o Init (Microsoft)

Mesmo comando, trocando a rota para `/auth/cliente/oauth/microsoft/init` e o `redirect_uri` para `http://localhost:3000/auth/callback/microsoft`.

---

## 🛠️ Troubleshooting

### Erro: "redirect_uri_mismatch" (Google)

**Causa**: o `redirect_uri` enviado (origem da aba + `/auth/callback/google`) não está registrado no Google Cloud Console.

**Solução**:
1. Compare a URL **exatamente** (esquema, host com/sem `app.`, porta, caminho)
2. Sem espaços antes/depois da URL
3. Aguarde alguns minutos após adicionar a URI (propagação)

### Erro: "AADSTS50011" (Microsoft, reply URL não confere)

**Causa**: o `redirect_uri` não está registrado no Azure.

**Solução**:
1. Verifique em **Autenticação** → **Web** se a URL está idêntica
2. `https://` em produção, `http://localhost:3000` em dev

### Erro: "State inválido ou expirado" (gateway, HTTP 400)

**Causa**: o `state` não está mais no Redis — passou de 10 minutos, já foi usado (é apagado no primeiro callback) ou o Redis reiniciou.

**Solução**:
1. Verifique o Redis: `docker ps --filter "name=redis"` (`erp-redis-dev` / `erp-redis-prod`)
2. Inicie o login de novo
3. Logs: `docker logs erp-api-gateway-dev -f` (evento `oauth.cliente.*.invalid_state`)

### Erro: "State inválido - possível ataque CSRF" (frontend)

Ver o problema conhecido do `ClienteLoginPage` em [OAUTH_FLUXO_COMPLETO.md](./OAUTH_FLUXO_COMPLETO.md#-troubleshooting).

### Credenciais ausentes

O gateway **não** valida se `GOOGLE_CLIENT_ID`/`MICROSOFT_CLIENT_ID` estão definidos: com a variável vazia, o `init` responde normalmente e o erro aparece no provedor (client id inválido), ou no callback como "Erro ao obter token do Google" / "Erro ao obter token da Microsoft".

**Solução**:
1. Confira `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` no `.env`
2. Recrie o container do gateway
3. Logs: `docker logs erp-api-gateway-dev` (evento `oauth.cliente.*.token_error`)

### Erro: "Access blocked" (Google)

**Causa**: o app está em modo de teste e o usuário não está na lista de testadores.

**Solução**:
1. Google Cloud Console → **Tela de consentimento OAuth** → **Usuários de teste**
2. Adicione o e-mail
3. OU publique o app

---

## 📚 Referências

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform OAuth 2.0](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)
- [RFC 6749: OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

---

## 📝 Resumo Rápido - URLs para Configurar

### Google Cloud Platform

**Console**: https://console.cloud.google.com/apis/credentials

**URIs de redirecionamento:**
```
https://app.runaserp.com.br/auth/callback/google
http://localhost:3000/auth/callback/google
```

**Escopos:** openid, email, profile

### Microsoft Azure

**Console**: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade

**URIs de redirecionamento (Web):**
```
https://app.runaserp.com.br/auth/callback/microsoft
http://localhost:3000/auth/callback/microsoft
```

**Permissões necessárias:** openid, email, profile, User.Read

---

## ✅ Checklist de Configuração

### Google Cloud Platform
- [ ] Projeto criado no Google Cloud Console
- [ ] Credenciais OAuth 2.0 criadas (Aplicativo da Web)
- [ ] URIs de redirecionamento `/auth/callback/google` configuradas
- [ ] Tela de consentimento OAuth configurada
- [ ] Escopos adicionados (openid, email, profile)
- [ ] Usuários de teste adicionados (se em modo teste)
- [ ] `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no `.env`

### Microsoft Azure
- [ ] Aplicativo registrado no Entra ID
- [ ] URIs de redirecionamento `/auth/callback/microsoft` configuradas (Web)
- [ ] Tipos de conta multilocatário + pessoais (se usar `common`)
- [ ] Segredo do cliente criado
- [ ] Permissões da API configuradas (openid, email, profile, User.Read)
- [ ] `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` (e `MICROSOFT_TENANT_ID`, se não for `common`) no `.env`

### Backend (API Gateway)
- [ ] Variáveis de ambiente no `.env` (dev) ou no Coolify (prod)
- [ ] Container do gateway recriado / novo deploy
- [ ] `POST /auth/cliente/oauth/{provider}/init` devolvendo `auth_url`
