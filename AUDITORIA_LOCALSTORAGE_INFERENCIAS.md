# 🔍 Auditoria de Inferências - localStorage e Autenticação

**Data**: 25/06/2026  
**Objetivo**: Identificar todas as inferências implícitas relacionadas ao `localStorage`, `sessionStorage` e tokens de autenticação no sistema.

---

## 📋 Sumário Executivo

### Principais Problemas Identificados

1. ❌ **Inconsistência OAuth**: GoogleCallback usa `sessionStorage`, MicrosoftCallback usa `localStorage`
2. ❌ **Token cliente_token**: MicrosoftCallback salva token no `localStorage`, violando arquitetura HTTP-only cookies
3. ⚠️ **Inferências de cliente_id**: Backend e frontend fazem inferências não validadas do `sub` do JWT
4. ⚠️ **CheckoutPage**: Busca `cliente_token` do `localStorage` apesar da migração para cookies
5. ✅ **GoogleCallback**: Implementação correta com cookies HTTP-only

---

## 🔴 CRÍTICO: Inconsistências OAuth

### Google OAuth (✅ CORRETO)

**Arquivo**: `frontend/src/pages/Auth/GoogleCallback.tsx`

```typescript
// ✅ Usa sessionStorage (correto para dados temporários)
const savedState = sessionStorage.getItem('oauth_state');
const empresaSlug = sessionStorage.getItem('oauth_empresa_slug');

// ✅ Backend seta cookies HTTP-only (seguro)
await apiPublica.post('/auth/cliente/oauth/google/callback', {
  code,
  state,
}, {
  withCredentials: true  // ✅ Permite cookies HTTP-only
});

// ✅ NÃO salva token no localStorage
console.log('🍪 Cookies HTTP-only foram setados pelo backend');

// ✅ Limpa sessionStorage após uso
sessionStorage.removeItem('oauth_state');
sessionStorage.removeItem('oauth_empresa_slug');
sessionStorage.removeItem('oauth_return_url');

// ✅ Flag para reload do carrinho
sessionStorage.setItem('reload_cart_after_oauth', 'true');
```

**Avaliação**: ✅ **PERFEITO** - Segue arquitetura correta com cookies HTTP-only

---

### Microsoft OAuth (❌ INCORRETO)

**Arquivo**: `frontend/src/pages/Auth/MicrosoftCallback.tsx`

```typescript
// ❌ Usa localStorage (deveria ser sessionStorage)
const savedState = localStorage.getItem('oauth_state');
const empresaSlug = localStorage.getItem('oauth_empresa_slug');

// ❌ Backend retorna access_token no body (vulnerável)
const { access_token, cliente } = response.data;

// ❌ PROBLEMA: Salva token no localStorage (vulnerável a XSS)
localStorage.setItem('cliente_token', access_token);

// ❌ Usa localStorage para flags temporárias
localStorage.removeItem('oauth_state');
localStorage.removeItem('oauth_empresa_slug');
localStorage.removeItem('oauth_return_url');

// ❌ Flag no localStorage (deveria ser sessionStorage)
localStorage.setItem('reload_cart_after_oauth', 'true');
```

**Problemas Identificados**:
1. ❌ Token salvo em `localStorage` (vulnerável a XSS)
2. ❌ Usa `localStorage` para dados temporários OAuth (deveria ser `sessionStorage`)
3. ❌ Backend retorna token no body (deveria usar HTTP-only cookies)
4. ❌ Falta `withCredentials: true` na requisição

**Avaliação**: ❌ **CRÍTICO** - Viola arquitetura de segurança

---

## ⚠️ CheckoutPage - Token em localStorage

**Arquivo**: `frontend/src/pages/LojaOnlinePublico/CheckoutPage.tsx`

### Problema 1: Busca token do localStorage

```typescript
// Linha 654
const token = localStorage.getItem('cliente_token');
```

**Contexto**: CheckoutPage busca token do `localStorage` para passar no header `Authorization`, mas:
- GoogleOAuth agora usa HTTP-only cookies
- MicrosoftOAuth ainda salva no `localStorage` (inconsistência)

**Impacto**: 
- ✅ GoogleOAuth: Token não será encontrado (esperado, usa cookies)
- ❌ MicrosoftOAuth: Token será encontrado (inconsistência)

---

### Problema 2: Detecção de retorno OAuth

```typescript
// Linha 160 - ✅ CORRETO (usa sessionStorage)
const reloadCart = sessionStorage.getItem('reload_cart_after_oauth');

if (reloadCart === 'true') {
  sessionStorage.removeItem('reload_cart_after_oauth');
  setRetornoOAuth(true);
  // Recarrega carrinho
}
```

**Mas**:
- GoogleCallback seta flag em `sessionStorage` ✅
- MicrosoftCallback seta flag em `localStorage` ❌

**Resultado**: MicrosoftOAuth **não recarrega carrinho** após login!

---

### Problema 3: Estado OAuth temporário

```typescript
// CheckoutPage salva em sessionStorage ✅
sessionStorage.setItem('oauth_state', state);
sessionStorage.setItem('oauth_empresa_slug', empresaSlug);
sessionStorage.setItem('oauth_return_url', `/c/${empresaSlug}/checkout`);

// MicrosoftCallback lê de localStorage ❌
const savedState = localStorage.getItem('oauth_state');
const empresaSlug = localStorage.getItem('oauth_empresa_slug');
```

**Resultado**: MicrosoftOAuth **sempre falha** em validação de state!

---

### Problema 4: Limpeza de token em erro 401

```typescript
// Linha 801
localStorage.removeItem('cliente_token');
```

**Inconsistência**:
- Tenta remover `cliente_token` do `localStorage`
- GoogleOAuth não salva nada lá (cookie HTTP-only)
- MicrosoftOAuth salva lá (deveria limpar cookies no backend)

---

## 🔒 Backend - Inferências de cliente_id

### JWT Payload

**Arquivo**: `api-gateway/auth/jwt.py`

```python
def create_access_token(
    user_id: UUID, 
    role: RoleEnum | str, 
    user_type: str = "usuario", 
    empresa_id: int | None = None,
    cliente_id: UUID | None = None  # ⚠️ Parâmetro opcional
) -> str:
    payload = {
        "sub": str(user_id),  # ⚠️ ID do cliente_auth, NÃO do cliente
        "role": role.value if isinstance(role, RoleEnum) else role,
        "user_type": user_type,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    }
    
    # Adicionar cliente_id para clientes (necessário para buscar dados)
    if cliente_id is not None:
        payload["cliente_id"] = str(cliente_id)  # ✅ Correto quando presente
```

**Problema**: 
- `sub` = `cliente_auth.id` (UUID do registro de autenticação)
- `cliente_id` = `cliente.id` (UUID do cliente real)
- Código pode confundir os dois!

---

### Router de Cliente OAuth

**Arquivo**: `api-gateway/routers/auth_cliente.py`

#### Google OAuth - ✅ CORRETO

```python
# Linha 530 - Google OAuth
access_token = create_access_token(
    user_id=cliente_auth.id,       # ✅ sub = cliente_auth.id
    role="CLIENTE",
    user_type="cliente",
    empresa_id=empresa_id,
    cliente_id=cliente_auth.cliente_id  # ✅ cliente_id explícito
)

# Linha 541 - Define cookies HTTP-only ✅
set_auth_cookies(response, access_token, refresh_token)

# Linha 543 - Retorna objeto completo
return ClienteLoginResponse(
    access_token=access_token,      # ✅ Retorna no body + cookie
    refresh_token=refresh_token,
    user_type="cliente",
    cliente=cliente_data            # ✅ Dados do cliente
)
```

**Avaliação**: ✅ Correto - Define `cliente_id` no JWT e seta cookies

#### Microsoft OAuth - ⚠️ INCONSISTENTE

```python
# Linha 756 - Microsoft OAuth
access_token = create_access_token(
    user_id=cliente_auth.id,       # ✅ sub = cliente_auth.id
    role="CLIENTE",
    user_type="cliente",
    empresa_id=empresa_id,
    cliente_id=cliente_auth.cliente_id  # ✅ cliente_id explícito
)

# Linha 763 - Define cookies HTTP-only ✅
set_auth_cookies(response, access_token, refresh_token)

# Linha 765 - Retorna objeto completo
return ClienteLoginResponse(
    access_token=access_token,      # ✅ Retorna no body + cookie
    refresh_token=refresh_token,
    user_type="cliente",
    cliente=cliente_data
)
```

**Avaliação**: ✅ Backend correto - **Frontend que está errado!**

---

### Serviço de Vendas - Inferências

**Arquivo**: `services/vendas/services/loja_service.py`

#### Problema 1: Inferir cliente_id do token

```python
# Linha 82-83
cliente_id = data.cliente_id

if data.cliente_novo and not cliente_id:
    # Cria cliente convidado
```

**Inferência Implícita**:
- Se `data.cliente_id` vem do frontend, pode ser `None`
- Frontend obtém `cliente_id` do JWT (`sub` ou `cliente_id`?)
- Não há validação se o `cliente_id` pertence ao token autenticado

**Risco**: Usuário pode enviar `cliente_id` de outro cliente!

---

#### Problema 2: Token payload com cliente_id

```python
# Linha 177-179
token_payload = {
    "sub": str(cliente_id),  # ⚠️ ERRO: deveria ser cliente_auth.id
    "role": "CLIENTE",
    "user_type": "cliente",
}
```

**ERRO CRÍTICO**:
- `sub` deveria ser `cliente_auth.id` (UUID do registro de autenticação)
- Código está setando `cliente_id` (UUID do cliente)
- Isso quebra toda lógica de autenticação!

**Correção Necessária**:
```python
# 1. Criar cliente_auth primeiro
cliente_auth_response = await client.post(
    f"{settings.API_GATEWAY_URL}/auth/cliente/registrar-interno",
    json={
        "email": cliente_info['email'],
        "senha_hash": senha_hash,
        "cliente_id": str(cliente_id),
        "empresa_id": empresa_id
    }
)
cliente_auth_data = cliente_auth_response.json()

# 2. Gerar token com cliente_auth_id correto
token_payload = {
    "sub": cliente_auth_data['id'],  # ✅ cliente_auth.id
    "role": "CLIENTE",
    "user_type": "cliente",
    "cliente_id": str(cliente_id),   # ✅ cliente.id no payload
    "empresa_id": empresa_id
}
```

---

#### Problema 3: Validar cliente existe

```python
# Linha 241
cliente_info = await VendaService.verificar_cliente_existe(empresa_id, cliente_id)
```

**Inferência**:
- Assume que `cliente_id` passado é válido
- Não valida se o `cliente_id` pertence ao token autenticado

**Correção**:
```python
# 1. Extrair cliente_id do token JWT
token = request.headers.get("Authorization").replace("Bearer ", "")
payload = verify_token(token)
token_cliente_id = UUID(payload.get("cliente_id"))

# 2. Validar que o cliente_id da requisição bate com o token
if data.cliente_id and data.cliente_id != token_cliente_id:
    raise HTTPException(401, "Cliente inválido")
```

---

## 📊 Inventário Completo de localStorage/sessionStorage

### localStorage (Persistente)

| Chave | Onde é usado | Propósito | Status |
|-------|--------------|-----------|--------|
| `cliente_token` | MicrosoftCallback, CheckoutPage | Token JWT cliente | ❌ Vulnerável (XSS) |
| `oauth_state` | MicrosoftCallback | Validação CSRF OAuth | ❌ Deveria ser session |
| `oauth_empresa_slug` | MicrosoftCallback | Empresa no OAuth | ❌ Deveria ser session |
| `oauth_return_url` | MicrosoftCallback | URL de retorno | ❌ Deveria ser session |
| `reload_cart_after_oauth` | MicrosoftCallback | Flag reload | ❌ Deveria ser session |
| `admin_token` | MicrosoftCallback | Token admin (legado) | ✅ Removido corretamente |
| `usuario_token` | MicrosoftCallback | Token usuário (legado) | ✅ Removido corretamente |
| `access_token` | tokenService (deprecated) | Token legado | ✅ Deprecated |
| `refresh_token` | tokenService (deprecated) | Refresh legado | ✅ Deprecated |

---

### sessionStorage (Temporário - ✅ CORRETO)

| Chave | Onde é usado | Propósito | Status |
|-------|--------------|-----------|--------|
| `oauth_state` | GoogleCallback, CheckoutPage | Validação CSRF OAuth | ✅ Correto |
| `oauth_empresa_slug` | GoogleCallback, CheckoutPage | Empresa no OAuth | ✅ Correto |
| `oauth_return_url` | GoogleCallback, CheckoutPage | URL de retorno | ✅ Correto |
| `reload_cart_after_oauth` | GoogleCallback, CheckoutPage | Flag reload | ✅ Correto |
| `oauth_provider` | oauthService | Provider OAuth (google/microsoft) | ✅ Correto |

---

## 🎯 Recomendações de Correção

### 1. ❌ CRÍTICO - Corrigir MicrosoftCallback

**Arquivo**: `frontend/src/pages/Auth/MicrosoftCallback.tsx`

```typescript
// ❌ ANTES
const savedState = localStorage.getItem('oauth_state');
localStorage.setItem('cliente_token', access_token);

// ✅ DEPOIS
const savedState = sessionStorage.getItem('oauth_state');
// NÃO salvar token - backend já setou cookie HTTP-only

// ✅ Adicionar withCredentials
await apiPublica.post('/auth/cliente/oauth/microsoft/callback', {
  code,
  state,
}, {
  withCredentials: true  // ✅ Permite cookies HTTP-only
});

// ✅ Limpar sessionStorage (não localStorage)
sessionStorage.removeItem('oauth_state');
sessionStorage.removeItem('oauth_empresa_slug');
sessionStorage.removeItem('oauth_return_url');
sessionStorage.setItem('reload_cart_after_oauth', 'true');
```

---

### 2. ⚠️ IMPORTANTE - Remover cliente_token do CheckoutPage

**Arquivo**: `frontend/src/pages/LojaOnlinePublico/CheckoutPage.tsx`

```typescript
// ❌ ANTES - Linha 654
const token = localStorage.getItem('cliente_token');

// ✅ DEPOIS - Remover busca de token
// Cookies HTTP-only são enviados automaticamente com withCredentials: true
// Se precisar validar se está autenticado, fazer requisição ao backend
const validarAutenticacao = async () => {
  try {
    const response = await apiPublica.get('/auth/cliente/me', {
      withCredentials: true
    });
    return response.data; // Retorna dados do cliente
  } catch (error) {
    return null; // Não autenticado
  }
};
```

---

### 3. 🔒 CRÍTICO - Corrigir geração de token no Loja Service

**Arquivo**: `services/vendas/services/loja_service.py`

```python
# ❌ ANTES - Linha 177-179
token_payload = {
    "sub": str(cliente_id),  # ❌ ERRO: deveria ser cliente_auth.id
    "role": "CLIENTE",
    "user_type": "cliente",
}

# ✅ DEPOIS
# 1. Criar cliente_auth PRIMEIRO
cliente_auth_response = await client.post(
    f"{settings.API_GATEWAY_URL}/auth/cliente/registrar-interno",
    json={
        "email": cliente_info['email'],
        "senha_hash": senha_hash,
        "cliente_id": str(cliente_id),
        "empresa_id": empresa_id
    }
)

if cliente_auth_response.status_code != 201:
    raise HTTPException(500, "Erro ao criar autenticação")

cliente_auth_data = cliente_auth_response.json()

# 2. Gerar token com dados corretos
from auth.jwt import create_access_token
access_token = create_access_token(
    user_id=UUID(cliente_auth_data['id']),  # ✅ cliente_auth.id como sub
    role="CLIENTE",
    user_type="cliente",
    empresa_id=empresa_id,
    cliente_id=cliente_id  # ✅ cliente.id como claim adicional
)
```

---

### 4. 🛡️ IMPORTANTE - Validar cliente_id no token

**Arquivo**: `services/vendas/services/loja_service.py`

```python
# Adicionar validação de autorização
async def validar_cliente_autorizado(
    token: str,
    cliente_id_requisicao: UUID
) -> bool:
    """
    Valida se o cliente_id da requisição bate com o token JWT.
    """
    from auth.jwt import verify_token
    
    try:
        payload = verify_token(token)
        token_cliente_id = payload.get("cliente_id")
        
        if not token_cliente_id:
            return False
        
        return UUID(token_cliente_id) == cliente_id_requisicao
    except Exception:
        return False

# Usar na rota de checkout
if data.cliente_id:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not await validar_cliente_autorizado(token, data.cliente_id):
        raise HTTPException(
            status_code=403,
            detail="Cliente não autorizado"
        )
```

---

### 5. 📝 LIMPEZA - Remover código deprecated

**Arquivo**: `frontend/src/services/auth/tokenService.ts`

```typescript
// ❌ TODO O ARQUIVO PODE SER REMOVIDO
// Tokens agora são gerenciados via HTTP-only cookies
// Nenhum código deveria usar tokenService

// ✅ Se precisar manter por compatibilidade, adicionar:
export const tokenService = {
  // Deprecated: Use HTTP-only cookies
  getAccessToken(): never {
    throw new Error('DEPRECATED: Tokens are now HTTP-only cookies');
  },
  
  // ... outros métodos similares
};
```

---

## 📈 Matriz de Impacto

| Problema | Severidade | Impacto | Esforço | Prioridade |
|----------|-----------|---------|---------|------------|
| MicrosoftCallback usa localStorage | 🔴 Crítico | Segurança XSS | 2h | P0 |
| Token incorreto em LotaService | 🔴 Crítico | Autenticação quebrada | 4h | P0 |
| CheckoutPage busca localStorage | 🟡 Médio | Inconsistência | 1h | P1 |
| Validar cliente_id no token | 🟡 Médio | Segurança (autorização) | 3h | P1 |
| Limpar tokenService deprecated | 🟢 Baixo | Manutenibilidade | 1h | P2 |

---

## ✅ Checklist de Correção

### Frontend

- [ ] Corrigir `MicrosoftCallback.tsx`
  - [ ] Trocar `localStorage` por `sessionStorage`
  - [ ] Remover `localStorage.setItem('cliente_token')`
  - [ ] Adicionar `withCredentials: true`
  - [ ] Não decodificar token no frontend

- [ ] Corrigir `CheckoutPage.tsx`
  - [ ] Remover `localStorage.getItem('cliente_token')`
  - [ ] Usar `apiPublica` com `withCredentials: true`
  - [ ] Criar função `validarAutenticacao()` se necessário

- [ ] Limpar código deprecated
  - [ ] Remover ou marcar `tokenService.ts` como deprecated
  - [ ] Remover imports de `tokenService` não utilizados

### Backend

- [ ] Corrigir `services/vendas/services/loja_service.py`
  - [ ] Chamar `/auth/cliente/registrar-interno` primeiro
  - [ ] Usar `cliente_auth.id` como `sub` do token
  - [ ] Adicionar `cliente_id` como claim adicional

- [ ] Adicionar validação de autorização
  - [ ] Criar middleware `validar_cliente_autorizado()`
  - [ ] Validar `cliente_id` da requisição vs token
  - [ ] Rejeitar requisições não autorizadas

- [ ] Testes
  - [ ] Teste: MicrosoftOAuth salva cookies (não localStorage)
  - [ ] Teste: Token JWT tem `sub` correto
  - [ ] Teste: Validação de autorização funciona
  - [ ] Teste: CheckoutPage funciona sem localStorage

---

## 📚 Documentação Relacionada

- **CHECKOUT_OAUTH_IMPLEMENTATION_SUMMARY.md**: Decisão de usar HTTP-only cookies
- **OAUTH_FLUXO_COMPLETO.md**: Fluxo OAuth documentado (não reflete MicrosoftCallback atual)
- **AUTH_CLIENTE_ME_ENDPOINT.md**: Endpoint `/me` que usa claims do token

---

## 🏁 Conclusão

**Total de problemas**: 8  
**Críticos**: 2  
**Médios**: 4  
**Baixos**: 2  

**Tempo estimado de correção**: 12 horas  
**Prioridade**: P0 (segurança e autenticação)

**Próximos passos**:
1. Corrigir `MicrosoftCallback.tsx` (P0 - 2h)
2. Corrigir token em `LotaService.py` (P0 - 4h)
3. Adicionar validação de autorização (P1 - 3h)
4. Limpar código deprecated (P2 - 1h)
5. Rodar testes de regressão (2h)

---

**Gerado por**: Kiro AI  
**Data**: 25/06/2026
