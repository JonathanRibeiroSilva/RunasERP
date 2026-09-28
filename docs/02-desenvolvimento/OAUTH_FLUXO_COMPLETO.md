# OAuth - Fluxo Completo de E-commerce

> **Escopo:** login social (Google e Microsoft) existe **só para o cliente comprador da loja online** (`/c/{empresaSlug}/...`). O login do painel (`frontend/src/pages/Login/LoginPage.tsx`, rota `/login`) é só e-mail/senha — não tem botão de Google nem de Microsoft. Nenhum outro provedor está implementado.

## 🎯 Fluxo Implementado

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. CLIENTE ADICIONA PRODUTOS AO CARRINHO                         │
│    → Navega pela loja (/c/{empresaSlug})                         │
│    → Carrinho fica no Redis do serviço de vendas, ligado ao      │
│      cookie HTTP-only cart_session_id (validade de 7 dias)       │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. CLIENTE VAI PARA CHECKOUT                                     │
│    → /c/{empresaSlug}/checkout                                   │
│    → CheckoutPage chama GET /clientes/me; 401 = não autenticado  │
│    → Login é obrigatório: checkout como convidado está           │
│      desabilitado no código                                      │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. TELA DE LOGIN DO CHECKOUT                                     │
│    Opções:                                                       │
│    A) "Entrar com Google"                                        │
│    B) "Entrar com Microsoft"                                     │
│    C) E-mail/senha                                               │
│    D) "Criar conta agora" (cadastro)                             │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. CLIENTE ESCOLHE OAUTH (Google ou Microsoft)                   │
│    → Frontend garante o carrinho (GET /loja/carrinho)            │
│    → Busca empresa_id em GET /empresas/publico/{empresaSlug}     │
│    → POST /auth/cliente/oauth/{provider}/init                    │
│    → Salva no sessionStorage:                                    │
│      • oauth_state (CSRF protection)                             │
│      • oauth_empresa_slug (qual loja)                            │
│      • oauth_return_url = /c/{empresaSlug}/checkout              │
│    → Redireciona para auth_url do Google/Microsoft               │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. AUTORIZAÇÃO NO PROVEDOR OAUTH                                 │
│    → Cliente faz login no Google/Microsoft                       │
│    → Tela de consentimento (o gateway manda prompt=consent)      │
│    → Provedor redireciona de volta com code + state              │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. CALLBACK (/auth/callback/google ou /auth/callback/microsoft)  │
│    → GoogleCallback.tsx / MicrosoftCallback.tsx lê code + state  │
│    → Compara state com oauth_state do sessionStorage            │
│    → POST /auth/cliente/oauth/{provider}/callback               │
│    → Backend (api-gateway/routers/auth_cliente.py):             │
│      1. Valida e apaga o state no Redis                         │
│      2. Troca code por access_token do provedor                 │
│      3. Busca userinfo (email + nome)                           │
│      4. Busca/cria cliente (idempotente por email)              │
│      5. Gera JWT (access + refresh) e seta cookies HTTP-only    │
│      6. Retorna: { access_token, refresh_token, cliente, ... }  │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 7. FRONTEND REDIRECIONA                                          │
│    → Token NÃO é salvo no storage: vale o cookie HTTP-only       │
│    → Lê oauth_return_url e limpa os dados OAuth temporários      │
│    → Seta a flag reload_cart_after_oauth no sessionStorage       │
│    → Toast "Bem-vindo, {nome}!" e navega para oauth_return_url   │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 8. DE VOLTA AO CHECKOUT - AGORA AUTENTICADO                      │
│    → CheckoutPage vê a flag, recarrega carrinho e /clientes/me  │
│    → Carrinho preservado (cookie cart_session_id)               │
│    → Se o carrinho voltar vazio, redireciona para a loja        │
│    → Pode finalizar a compra                                    │
└──────────────────────────────────────────────────────────────────┘
```

## 🔧 Implementação Técnica

Os trechos abaixo são resumos do código real; confira o arquivo antes de copiar.

### Frontend - CheckoutPage.tsx

`frontend/src/pages/LojaOnlinePublico/CheckoutPage.tsx`, funções `fazerLoginGoogle` e `fazerLoginMicrosoft`.

**Iniciando OAuth Google:**

```typescript
const fazerLoginGoogle = async () => {
  setFazendoLogin(true);
  try {
    // 1. Garantir que carrinho existe (cria sessão se não existir)
    await carregarCarrinho();
    // 2. Aguardar um momento para cookie ser setado
    await new Promise(resolve => setTimeout(resolve, 200));

    const empresaResponse = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
    const empresa_id = empresaResponse.data.id;
    const redirect_uri = `${window.location.origin}/auth/callback/google`;

    const response = await apiPublica.post('/auth/cliente/oauth/google/init', {
      redirect_uri,
      empresa_id
    });

    const { auth_url, state } = response.data;
    sessionStorage.setItem('oauth_state', state);
    sessionStorage.setItem('oauth_empresa_slug', empresaSlug);
    sessionStorage.setItem('oauth_return_url', `/c/${empresaSlug}/checkout`);
    window.location.href = auth_url;
  } catch (error: any) {
    Toast.error('Erro ao iniciar login com Google');
    setFazendoLogin(false);
  }
};
```

**Iniciando OAuth Microsoft:** mesma lógica em `fazerLoginMicrosoft`, só muda o endpoint (`/auth/cliente/oauth/microsoft/init`) e o `redirect_uri` (`${window.location.origin}/auth/callback/microsoft`).

`apiPublica` (`frontend/src/services/api/apiPublica.ts`) usa `baseURL: '/api'` e `withCredentials: true`; o nginx (e o Vite em dev) tira o prefixo `/api` antes de repassar ao gateway.

### Frontend - GoogleCallback.tsx

`frontend/src/pages/Auth/GoogleCallback.tsx` (rota `/auth/callback/google` em `App.tsx`). `MicrosoftCallback.tsx` é idêntico, trocando o provedor.

```typescript
const processarCallback = async () => {
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  const savedState = sessionStorage.getItem('oauth_state');
  const empresaSlug = sessionStorage.getItem('oauth_empresa_slug');

  if (!code || !state) { setErro('Parâmetros inválidos'); /* ... */ return; }
  if (state !== savedState) { setErro('State inválido - possível ataque CSRF'); /* ... */ return; }
  if (!empresaSlug) { setErro('Sessão expirada'); /* ... */ return; }

  try {
    const response = await apiPublica.post('/auth/cliente/oauth/google/callback', {
      code,
      state,
    }, {
      withCredentials: true  // permite receber os cookies HTTP-only
    });

    const { cliente } = response.data;
    // Backend setou cookies HTTP-only; nada de token no localStorage

    const returnUrl = sessionStorage.getItem('oauth_return_url') || `/c/${empresaSlug}/checkout`;

    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('oauth_empresa_slug');
    sessionStorage.removeItem('oauth_return_url');

    // Sinaliza ao CheckoutPage para recarregar carrinho e dados do cliente
    sessionStorage.setItem('reload_cart_after_oauth', 'true');

    Toast.success(`Bem-vindo, ${cliente.nome}!`);
    navigate(returnUrl);
  } catch (error) {
    // Mostra o erro e volta para /c/{empresaSlug}/checkout após 3 segundos
  }
};
```

### Backend - auth_cliente.py

`api-gateway/routers/auth_cliente.py`, router com `prefix="/auth/cliente"`:

| Rota | Função | Linha |
|------|--------|-------|
| `POST /auth/cliente/oauth/google/init` | `oauth_google_init_cliente` | 335 |
| `POST /auth/cliente/oauth/google/callback` | `oauth_google_callback_cliente` | 367 |
| `POST /auth/cliente/oauth/microsoft/init` | `oauth_microsoft_init_cliente` | 447 |
| `POST /auth/cliente/oauth/microsoft/callback` | `oauth_microsoft_callback_cliente` | 483 |

**Init** (`OAuthInitRequest`: `redirect_uri: str`, `empresa_id: int`): gera `state = secrets.token_urlsafe(32)`, grava `oauth:cliente:state:{state}` = `"{redirect_uri}|{empresa_id}"` no Redis com TTL de 600 s e devolve `{"auth_url", "state"}`.

- Google: `https://accounts.google.com/o/oauth2/v2/auth`, `scope=openid email profile`, `access_type=offline`, `prompt=consent`.
- Microsoft: `https://login.microsoftonline.com/{MICROSOFT_TENANT_ID ou "common"}/oauth2/v2.0/authorize`, `scope=openid email profile User.Read`, `prompt=consent`.

**Callback Google (resumo):**

```python
@router.post("/oauth/google/callback", response_model=ClienteLoginResponse)
async def oauth_google_callback_cliente(
    response: Response,
    callback: OAuthCallbackRequest,          # code, state
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    # 1. Validar state (CSRF) e apagá-lo do Redis
    state_data = await redis.get(f"oauth:cliente:state:{callback.state}")
    if not state_data:
        raise HTTPException(400, "State inválido ou expirado")
    redirect_uri, empresa_id_str = state_data.split("|")   # após decode
    empresa_id = int(empresa_id_str)
    await redis.delete(f"oauth:cliente:state:{callback.state}")

    # 2. Trocar code por access_token em https://oauth2.googleapis.com/token
    # 3. Userinfo em https://www.googleapis.com/oauth2/v2/userinfo
    email = user_data.get("email")
    nome = user_data.get("name", email.split("@")[0])

    # 4-6. Fluxo comum aos dois provedores
    return await _complete_cliente_oauth(response, redis, repo, empresa_id, email, nome)
```

No callback Microsoft a troca é em `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`, o userinfo vem de `https://graph.microsoft.com/v1.0/me`, o e-mail é `mail` (ou `userPrincipalName`) e o nome é `displayName`.

**`_complete_cliente_oauth`** (comum aos dois):

1. `ClienteAuthRepository.buscar_por_email(email)`.
2. Se não existe: `_upsert_cliente_oauth` faz `POST {CLIENTES_URL}/clientes/oauth` (idempotente por e-mail, sem CPF/telefone) com `X-Empresa-Id` + prova interna (`auth_interno`), e cria o `ClienteAuth` com `senha=""`.
3. Se existe: `_fetch_cliente` faz `GET {CLIENTES_URL}/clientes/{cliente_id}`.
4. `_issue_cliente_session`: `create_access_token(role="CLIENTE", user_type="cliente", empresa_id, cliente_id)`, `create_refresh_token`, grava `refresh:cliente:{id}` no Redis por `REFRESH_TOKEN_EXPIRE_DAYS`, chama `set_auth_cookies` (cookies `access_token` 30 min e `refresh_token` 7 dias, `httponly`, `samesite="lax"`, `secure` só se `FRONTEND_URL` começa com `https://`) e devolve `ClienteLoginResponse`.

## 🎯 Pontos-Chave da Implementação

### 1. **Carrinho Preservado**

O carrinho não fica no navegador: fica no Redis do serviço de vendas (`services/vendas/services/carrinho_service.py`), identificado pelo cookie HTTP-only `cart_session_id` (7 dias, `services/vendas/routers/loja.py`). Por isso:
- ✅ Não é perdido durante o redirect do OAuth
- ✅ Ao voltar, o `CheckoutPage` recarrega o carrinho (flag `reload_cart_after_oauth`)
- ✅ Carrinho vazio no retorno redireciona o cliente para a loja

### 2. **Return URL**

O `CheckoutPage` grava `oauth_return_url = /c/{empresaSlug}/checkout`. O `ClienteLoginPage` (`/c/{empresaSlug}/login`) também inicia OAuth e grava `oauth_return_url` com a página de origem — mas veja o problema conhecido no Troubleshooting.

### 3. **CSRF Protection**

O `state` é um token aleatório que:
- Backend gera e salva no Redis (TTL de 10 minutos)
- Frontend armazena no `sessionStorage`
- Callback do frontend compara com o que voltou na URL
- Backend exige que o state exista no Redis e o apaga (uso único)

### 4. **Dados Opcionais (CPF/Telefone)**

Clientes OAuth são criados sem CPF/telefone (`cpf` e `telefone` são `str | None` em `ClienteResponse`). O checkout pede esses dados quando faltam e atualiza o cadastro do cliente autenticado.

### 5. **Uma conta por e-mail**

`ClienteAuth.email` é `unique=True` no gateway (não é por loja). A mesma conta serve login por senha e por OAuth.

## 🧪 Testando o Fluxo Completo

### Passo a Passo

1. **Acesse a loja**: `http://localhost:3000/c/distribuidora-central` em dev (slug do seed de `services/empresas/seed.py`), ou `https://app.runaserp.com.br/c/{slug}` em produção.

2. **Adicione produtos ao carrinho**.

3. **Vá para checkout**:
   - Abra o carrinho
   - Clique em "Finalizar compra"
   - Vai para `/c/distribuidora-central/checkout`

4. **Faça login com Google**:
   - Clique em "Entrar com Google"
   - Autorize no Google
   - Aguarde o redirecionamento

5. **Verifique o resultado**:
   - ✅ Toast "Bem-vindo, [Seu Nome]!"
   - ✅ Volta para a página de checkout
   - ✅ Carrinho com os produtos adicionados
   - ✅ Pode finalizar a compra

### Verificação Técnica (DevTools)

**Application → Cookies deve conter** (HTTP-only):
- `access_token` e `refresh_token` (setados pelo gateway no callback)
- `cart_session_id` (setado pelo serviço de vendas)

**Session Storage NÃO deve conter** (dados temporários limpos):
```javascript
{
  "oauth_state": "...",          // ❌ Deve ser removido
  "oauth_empresa_slug": "...",   // ❌ Deve ser removido
  "oauth_return_url": "..."      // ❌ Deve ser removido
}
```
(`reload_cart_after_oauth` some assim que o `CheckoutPage` o processa.)

**Network → Response do callback** (`ClienteLoginResponse`; `cliente` é o `ClienteResponse` do serviço de clientes):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_type": "cliente",
  "cliente": {
    "id": "uuid",
    "empresa_id": 1,
    "nome": "Seu Nome",
    "cpf": null,
    "telefone": null,
    "email": "seu@email.com",
    "data_nasc": null,
    "limite_credito": "0.00",
    "credito_disponivel": "0.00",
    "dia_vencimento": null,
    "bloqueado": false,
    "ativo": true,
    "criado_em": "..."
  }
}
```
Valores ilustrativos. Cliente criado via OAuth não recebe `limite_credito`/`credito_disponivel` no payload, então vale o default `0.00` do modelo (`services/clientes/models/cliente.py`).

## 🐛 Troubleshooting

### Problema: "State inválido - possível ataque CSRF" (frontend)

**Causa**: o `state` da URL não bate com `oauth_state` do `sessionStorage` (aba diferente, storage limpo, ou o fluxo não gravou o state).

**Problema conhecido**: o `ClienteLoginPage` (`/c/{empresaSlug}/login`) não grava `oauth_state` nem `oauth_empresa_slug` antes de redirecionar, então o callback falha nessa verificação. O caminho que funciona é o do checkout.

**Solução**:
```javascript
sessionStorage.removeItem('oauth_state');
sessionStorage.removeItem('oauth_empresa_slug');
sessionStorage.removeItem('oauth_return_url');
// Tentar novamente pelo checkout
```

### Problema: "State inválido ou expirado" (backend, HTTP 400)

**Causa**: o state não existe mais no Redis — passou de 10 minutos, já foi usado (é apagado no primeiro callback) ou o Redis foi reiniciado.

**Solução**: iniciar o login de novo.

### Problema: "Sessão expirada"

**Causa**: `oauth_empresa_slug` não está no `sessionStorage` (ver problema conhecido acima).

### Problema: Carrinho vazio após login

**Causa**: cookie `cart_session_id` ausente/expirado (7 dias) ou carrinho de outra loja — a chave do Redis inclui `empresa_id`.

**Verificação**: DevTools → Application → Cookies → `cart_session_id`; Network → `GET /api/loja/carrinho?empresaSlug=...`.

### Problema: Não redireciona após login

**Verificação**:
```javascript
// Antes de clicar em "Entrar com Google"
console.log(sessionStorage.getItem('oauth_return_url'));
// Deve mostrar: /c/{empresaSlug}/checkout
```
Sem `oauth_return_url`, o callback usa `/c/{empresaSlug}/checkout` como fallback.

## 📊 Métricas Sugeridas

Nada disso está instrumentado hoje; são sugestões para medir o fluxo:

1. **Taxa de Conversão OAuth**: % de clientes que completam o OAuth
2. **Taxa de Abandono no Callback**: % que não retorna após autorizar
3. **Tempo Médio do Fluxo**: de "Entrar com Google" até voltar ao checkout
4. **Taxa de Finalização**: % que completam a compra após OAuth

Os eventos do structlog no gateway são o ponto de partida: `oauth.cliente.{google|microsoft}.{init,callback,invalid_state,token_error,userinfo_error}` por provedor, e `oauth.cliente.created` / `oauth.cliente.login` no fluxo comum.

## 🚀 Melhorias Futuras

### 1. Pre-fill de Dados

Se o provedor retornar telefone, preencher automaticamente no checkout (hoje só e-mail e nome são lidos).

### 2. Login Silencioso

Hoje o gateway sempre manda `prompt=consent`, então a tela de consentimento aparece todo login. Remover/ajustar o `prompt` evitaria isso para quem já autorizou.

### 3. Corrigir o OAuth do ClienteLoginPage

Gravar `oauth_state`/`oauth_empresa_slug` no `ClienteLoginPage` como o `CheckoutPage` faz.

## 📚 Referências

- [Configuração dos provedores (Google/Azure)](./OAUTH_PROVIDERS_CONFIG.md)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft OAuth 2.0 Documentation](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [OWASP OAuth Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
