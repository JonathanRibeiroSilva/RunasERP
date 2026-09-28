# Resumo da Implementação OAuth

> **Escopo:** OAuth (Google e Microsoft) existe **só para o cliente comprador da loja online**. O login do painel (`frontend/src/pages/Login/LoginPage.tsx`, rota `/login`) é só e-mail/senha, sem login social. Nenhum outro provedor está implementado.
>
> Fluxo detalhado: [OAUTH_FLUXO_COMPLETO.md](../../02-desenvolvimento/OAUTH_FLUXO_COMPLETO.md). Configuração dos consoles: [OAUTH_PROVIDERS_CONFIG.md](../../02-desenvolvimento/OAUTH_PROVIDERS_CONFIG.md).

## ✅ O que está implementado

### Backend (API Gateway, FastAPI)

1. **`api-gateway/routers/auth_cliente.py`** (router `prefix="/auth/cliente"`)
   - `POST /auth/cliente/oauth/google/init` - Inicia fluxo OAuth Google
   - `POST /auth/cliente/oauth/google/callback` - Processa callback Google
   - `POST /auth/cliente/oauth/microsoft/init` - Inicia fluxo OAuth Microsoft
   - `POST /auth/cliente/oauth/microsoft/callback` - Processa callback Microsoft
   - Validação de `state` via Redis (proteção CSRF, TTL de 600 s, uso único)
   - Criação idempotente do cliente por e-mail (`POST /clientes/oauth` no serviço de clientes)
   - Geração de JWT (`user_type="cliente"`, `role="CLIENTE"`) e cookies HTTP-only

2. **`api-gateway/config.py`**
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (opcionais, default `None`)
   - `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` (opcionais, default `None`)
   - `MICROSOFT_TENANT_ID` (default `"common"`)

3. **`api-gateway/models/cliente_auth.py`** + **`repositories/cliente_auth_repository.py`**
   - `ClienteAuth` com `email` único; contas OAuth são criadas com senha vazia

4. **`services/clientes/routers/clientes.py`**
   - `POST /clientes/oauth` (`criar_cliente_oauth`): cria ou devolve o cliente existente, sem CPF/telefone

`api-gateway/routers/auth.py` (login do painel) **não** tem rotas OAuth. `schemas/usuario.py` e `repositories/usuario_repository.py` aceitam senha vazia "para OAuth", mas nenhum fluxo cria usuário do painel via OAuth.

### Frontend (React + TypeScript + Vite)

1. **`frontend/src/pages/LojaOnlinePublico/CheckoutPage.tsx`**
   - Botões "Entrar com Google" e "Entrar com Microsoft" na tela de login do checkout
   - `fazerLoginGoogle()` / `fazerLoginMicrosoft()`: chamam o `init` e gravam `oauth_state`, `oauth_empresa_slug` e `oauth_return_url` no `sessionStorage`
   - Ao voltar, detecta a flag `reload_cart_after_oauth` e recarrega carrinho e `/clientes/me`

2. **`frontend/src/pages/LojaOnlinePublico/ClienteLoginPage.tsx`** (rota `/c/:empresaSlug/login`)
   - Botões Google e Microsoft (`handleOAuthGoogle` / `handleOAuthMicrosoft`)
   - Grava só `oauth_return_url` — ver problema conhecido no Troubleshooting

3. **`frontend/src/pages/Auth/GoogleCallback.tsx`** e **`MicrosoftCallback.tsx`**
   - Validam `code`, `state` (contra o `sessionStorage`) e `oauth_empresa_slug`
   - Chamam o `callback` do gateway com `withCredentials: true`
   - Limpam o `sessionStorage`, setam `reload_cart_after_oauth` e navegam para `oauth_return_url`
   - Em erro, voltam para `/c/{empresaSlug}/checkout` após 3 segundos

4. **`frontend/src/App.tsx`**
   - Rotas `/auth/callback/google` e `/auth/callback/microsoft`

5. **`frontend/src/config/env.ts`**
   - Lê `VITE_GOOGLE_CLIENT_ID`, `VITE_MICROSOFT_CLIENT_ID`, `VITE_MICROSOFT_TENANT_ID` e `VITE_OAUTH_REDIRECT_URI` em `config.oauth`, mas nenhum código usa `config.oauth`: os botões aparecem sempre, configurado ou não

## 🔐 Fluxo OAuth Implementado

### 1. Iniciação (Frontend)

```
Cliente clica "Entrar com Google" no checkout
    ↓
Frontend busca empresa_id: GET /api/empresas/publico/{empresaSlug}
    ↓
Frontend chama: POST /api/auth/cliente/oauth/google/init
                { redirect_uri, empresa_id }
    ↓
Gateway gera state aleatório
    ↓
Gateway salva state + redirect_uri + empresa_id no Redis (10 min)
    ↓
Gateway retorna { auth_url, state }
    ↓
Frontend salva state, slug e return URL no sessionStorage
    ↓
Frontend redireciona para o Google
```

### 2. Autorização (Google)

```
Cliente autoriza no Google
    ↓
Google redireciona para: {origem}/auth/callback/google?code=...&state=...
```

`{origem}` é `window.location.origin` (`http://localhost:3000` em dev, `https://app.runaserp.com.br` em produção).

### 3. Callback (Frontend + Backend)

```
GoogleCallback recebe code e state
    ↓
Frontend compara state com o sessionStorage
    ↓
Frontend chama: POST /api/auth/cliente/oauth/google/callback { code, state }
    ↓
Gateway valida e apaga o state no Redis
    ↓
Gateway troca code por access_token (Google)
    ↓
Gateway busca e-mail e nome (userinfo do Google)
    ↓
Gateway busca/cria o cliente (idempotente por e-mail)
    ↓
Gateway gera JWT, grava refresh no Redis e seta cookies HTTP-only
    ↓
Gateway retorna: { access_token, refresh_token, token_type, user_type, cliente }
    ↓
Frontend limpa sessionStorage e navega para oauth_return_url
(normalmente /c/{empresaSlug}/checkout)
```

## 🔒 Segurança Implementada

- ✅ **CSRF Protection**: `state` aleatório (`secrets.token_urlsafe(32)`) validado no frontend e no Redis
- ✅ **State de uso único**: expira em 10 minutos e é apagado no primeiro callback
- ✅ **JWT**: cookie `access_token` com 30 min e `refresh_token` com 7 dias (`max_age` em `set_auth_cookies`); `ACCESS_TOKEN_EXPIRE_MINUTES=30` e `REFRESH_TOKEN_EXPIRE_DAYS=7` são os defaults de `config.py`
- ✅ **Cookies HTTP-only**: `samesite="lax"`, `secure` quando `FRONTEND_URL` é `https://`; o frontend não guarda token em `localStorage`
- ✅ **Client Secret**: fica só no gateway
- ✅ **Senha vazia**: contas OAuth não têm senha local
- ✅ **Session Cleanup**: dados OAuth do `sessionStorage` removidos após o callback

## 📊 Estrutura de Dados

### ClienteAuth (gateway)

```python
{
    "id": "uuid",
    "email": "cliente@gmail.com",   # único no gateway, não por loja
    "senha_hash": "",               # vazio para conta OAuth (ClienteAuthRepository.criar)
    "cliente_id": "uuid",           # cliente no serviço de clientes
    "empresa_id": 1,
    "ativo": True
}
```

### Response do Callback (`ClienteLoginResponse`)

```json
{
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "user_type": "cliente",
    "cliente": {
        "id": "uuid",
        "empresa_id": 1,
        "nome": "Nome",
        "email": "cliente@gmail.com",
        "cpf": null,
        "telefone": null,
        "ativo": true
    }
}
```

`cliente` é o `ClienteResponse` completo do serviço de clientes (também traz `data_nasc`, `limite_credito`, `credito_disponivel`, `dia_vencimento`, `bloqueado`, `criado_em`).

## 🧪 Como Testar

### Desenvolvimento

1. **Configurar** `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` (e/ou os da Microsoft) no `.env` — ver [OAUTH_PROVIDERS_CONFIG.md](../../02-desenvolvimento/OAUTH_PROVIDERS_CONFIG.md)

2. **Subir containers:**
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

3. **Acessar a loja:**
   ```
   http://localhost:3000/c/distribuidora-central
   ```

4. **Testar Google OAuth:**
   - Adicionar um produto e ir ao checkout
   - Clicar em "Entrar com Google"
   - Autorizar no Google
   - Verificar o toast "Bem-vindo, {nome}!" e o retorno ao checkout com o carrinho

5. **Testar Microsoft OAuth:** mesmo roteiro com "Entrar com Microsoft"

### Produção

As variáveis ficam no ambiente do Coolify e o deploy usa `docker-compose.prod.yml` (imagens puxadas do registry). A loja fica em `https://app.runaserp.com.br/c/{slug}`. A CONFIRMAR: procedimento de deploy no Coolify — ver `docs/06-operacao/deploy.md`.

## 🐛 Troubleshooting

### Erro: "State inválido - possível ataque CSRF" / "Sessão expirada"

**Causa:** `oauth_state` ou `oauth_empresa_slug` ausente no `sessionStorage`.

**Problema conhecido:** o `ClienteLoginPage` não grava esses dois itens antes de redirecionar, então o login OAuth iniciado em `/c/{slug}/login` falha no callback. Pelo checkout funciona.

### Erro: "State inválido ou expirado" (gateway, 400)

**Causas:**
- State expirou (> 10 minutos)
- State já usado (é apagado no Redis no primeiro callback; recarregar a página do callback depois de uma falha reenvia o mesmo state — depois de um sucesso o `sessionStorage` já foi limpo e o erro é o do frontend)
- Redis fora do ar

**Solução:**
- Verificar o Redis: `docker ps --filter "name=redis"`
- Iniciar o login de novo

### Erro: "Erro ao obter token do Google" / "da Microsoft"

**Causa:** credenciais ausentes/erradas no gateway ou `redirect_uri` diferente do registrado no console.

**Solução:**
- Logs: `docker logs erp-api-gateway-dev` (eventos `oauth.cliente.*.token_error`)
- Conferir as variáveis e recriar o container: `docker compose -f docker-compose.dev.yml up -d --force-recreate api-gateway`

### Erro: 404 nas rotas OAuth

**Causa:** chamada sem o prefixo certo. Pelo navegador a rota é `/api/auth/cliente/oauth/...`; direto no gateway (porta 8000) é `/auth/cliente/oauth/...`. Não existe `/auth/oauth/...`.

## 📈 Próximas Melhorias

Ideias, nada disso está implementado:

- [ ] Gravar `oauth_state`/`oauth_empresa_slug` no `ClienteLoginPage`
- [ ] Esconder os botões quando o provedor não estiver configurado
- [ ] Vincular OAuth a uma conta existente de outra loja (hoje o e-mail é único globalmente)
- [ ] Rate limit nas rotas OAuth (em `auth_cliente.py`, hoje só `register` e `login` usam `@limiter.limit`)

## 📚 Referências

- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform](https://learn.microsoft.com/en-us/entra/identity-platform/)
