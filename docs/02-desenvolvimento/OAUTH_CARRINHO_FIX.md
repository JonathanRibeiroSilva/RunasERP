# OAuth + Carrinho: Diagnóstico e Solução

## 🔍 Problema Identificado

Após login OAuth, o carrinho não aparece no checkout.

### Causa Raiz

O carrinho é gerenciado por **sessão no backend (Redis)** identificada por um cookie `cart_session_id`:

```
Fluxo Atual:
1. Usuário anônimo adiciona produtos
   → Cookie: cart_session_id = "abc123"
   → Redis: carrinho_abc123 = {produtos}

2. Usuário faz login OAuth  
   → Redireciona para Google
   → Volta para /auth/callback/google
   → Cookie cart_session_id pode ser perdido ou não enviado

3. Checkout tenta buscar carrinho
   → Sem cart_session_id ou com sessão diferente
   → Backend retorna carrinho vazio
```

## ✅ Solução: Preservar Cookie Durante OAuth

### Problema com Cookies e Redirects

Quando fazemos:
```typescript
window.location.href = auth_url; // Redireciona para Google
```

O navegador **mantém** os cookies do domínio. Porém, precisamos garantir que:

1. Cookie `cart_session_id` existe antes do OAuth
2. Cookie persiste durante redirect para Google
3. Cookie é enviado ao voltar para o checkout

###  Verificação (DevTools → Application → Cookies)

Antes do login:
```
Name: cart_session_id
Value: abc123-def456-...
Domain: runaserp.com.br
Path: /
HttpOnly: Yes
SameSite: Lax
```

Após login OAuth:
```
Se o cookie SUMIU → Problema!
Se o cookie EXISTE → Backend não está usando corretamente
```

## 🔧 Fix 1: Garantir Cookie Existe Antes de OAuth

Atualizar `CheckoutPage.tsx`:

```typescript
const fazerLoginGoogle = async () => {
  setFazendoLogin(true);
  try {
    // 1. GARANTIR que carrinho existe (cria sessão se não existir)
    await carregarCarrinho();
    
    // 2. Aguardar um momento para cookie ser setado
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // 3. Iniciar OAuth
    const empresaResponse = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
    const empresa_id = empresaResponse.data.id;
    const redirect_uri = `${window.location.origin}/auth/callback/google`;
    
    const response = await apiPublica.post('/auth/cliente/oauth/google/init', {
      redirect_uri,
      empresa_id
    });

    const { auth_url, state } = response.data;
    localStorage.setItem('oauth_state', state);
    localStorage.setItem('oauth_empresa_slug', empresaSlug);
    localStorage.setItem('oauth_return_url', `/c/${empresaSlug}/checkout`);
    
    window.location.href = auth_url;
  } catch (error) {
    Toast.error('Erro ao iniciar login com Google');
    setFazendoLogin(false);
  }
};
```

## 🔧 Fix 2: Recarregar Carrinho Após Login

Atualizar `GoogleCallback.tsx`:

```typescript
// Após salvar token
localStorage.setItem('cliente_token', access_token);

// Limpar dados OAuth
const returnUrl = localStorage.getItem('oauth_return_url') || `/c/${empresaSlug}/checkout`;
localStorage.removeItem('oauth_state');
localStorage.removeItem('oauth_empresa_slug');
localStorage.removeItem('oauth_return_url');

// Adicionar flag para recarregar carrinho
localStorage.setItem('reload_cart_after_oauth', 'true');

Toast.success(`Bem-vindo, ${cliente.nome}!`);
navigate(returnUrl);
```

Atualizar `CheckoutPage.tsx` para detectar retorno do OAuth:

```typescript
// Adicionar useEffect para detectar retorno do OAuth
useEffect(() => {
  const reloadCart = localStorage.getItem('reload_cart_after_oauth');
  if (reloadCart === 'true') {
    localStorage.removeItem('reload_cart_after_oauth');
    // Forçar reload do carrinho
    carregarCarrinho();
  }
}, [carregarCarrinho]);
```

## 🔧 Fix 3: Backend - Vincular Cliente ao Carrinho

Se o problema persistir, precisamos vincular o `cart_session_id` ao cliente após login.

Adicionar no callback OAuth (backend):

```python
@router.post("/oauth/google/callback")
async def oauth_google_callback_cliente(
    response: Response,
    callback: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    cart_session_id: str | None = Cookie(None, alias="cart_session_id")  # ← ADICIONAR
):
    # ... código existente de autenticação ...
    
    # Após criar/buscar cliente_auth
    # Vincular carrinho anônimo ao cliente
    if cart_session_id:
        try:
            # Buscar carrinho da sessão anônima
            carrinho_key = f"carrinho:{cart_session_id}"
            carrinho_data = await redis.get(carrinho_key)
            
            if carrinho_data:
                # Carrinho existe, vincular ao cliente
                carrinho_cliente_key = f"carrinho:cliente:{cliente_auth.id}"
                
                # Copiar carrinho para chave do cliente
                await redis.set(carrinho_cliente_key, carrinho_data)
                await redis.expire(carrinho_cliente_key, 7 * 24 * 60 * 60)  # 7 dias
                
                log.info("carrinho.vinculado_cliente", 
                         sessao_id=cart_session_id, 
                         cliente_id=str(cliente_auth.id))
        except Exception as e:
            log.warning("erro_vincular_carrinho", error=str(e))
            # Não falhar o login se houver erro ao vincular carrinho
    
    # ... restante do código ...
```

## 🎯 Abordagem Recomendada

### Opção A: Manter Sessão Anônima (Mais Simples)

- Cookie `cart_session_id` persiste
- Carrinho funciona para anônimos e autenticados
- **Implementação**: Fixes 1 e 2

### Opção B: Vincular Carrinho ao Cliente (Mais Robusto)

- Após login, carrinho é associado ao `cliente_id`
- Permite carrinho cross-device (se implementar)
- **Implementação**: Fix 3

### Recomendação: **Implementar Opção A primeiro**

É mais simples e resolve o problema imediato. Se quiser carrinho cross-device depois, implementar Opção B.

## 🧪 Teste do Fix

### Passo 1: Verificar Cookie Antes do Login

1. Adicione produtos ao carrinho
2. Abra DevTools → Application → Cookies
3. Verifique: `cart_session_id` existe e tem valor
4. **Anote o valor**

### Passo 2: Fazer Login OAuth

1. Vá para checkout
2. Clique "Login com Google"
3. Autorize no Google
4. Volte para checkout

### Passo 3: Verificar Cookie Após Login

1. DevTools → Application → Cookies
2. Verifique: `cart_session_id` **ainda existe**
3. **Compare o valor** - deve ser o mesmo!

### Passo 4: Verificar Carrinho

1. Se cookie é o mesmo → Carrinho deve aparecer
2. Se cookie mudou ou sumiu → Implementar fixes adicionais

## 📊 Debugging

### Log no Console (Frontend)

Adicionar no `CheckoutPage.tsx`:

```typescript
useEffect(() => {
  console.log('🛒 Carrinho:', carrinho);
  console.log('🍪 Cookies:', document.cookie);
}, [carrinho]);
```

### Log no Backend

Adicionar no `loja.py`:

```python
@router.get("/carrinho")
async def obter_carrinho(...):
    log.info("carrinho.request", sessao_id=sessao_id, empresa_id=empresa_id)
    # ... resto do código
```

Verificar logs:
```bash
docker logs erp-vendas-dev -f | grep carrinho
```

## ✅ Checklist de Verificação

- [ ] Cookie `cart_session_id` existe antes do OAuth
- [ ] Cookie persiste após OAuth redirect
- [ ] Cookie é enviado nas requisições ao backend
- [ ] Backend recebe o `sessao_id` correto
- [ ] Redis contém o carrinho na chave `carrinho:{sessao_id}`
- [ ] Frontend recebe os itens do carrinho após login

---

**Status**: 🔍 Diagnóstico Completo  
**Próximo Passo**: Implementar Fix 1 e Fix 2  
**Data**: 2026-06-25
