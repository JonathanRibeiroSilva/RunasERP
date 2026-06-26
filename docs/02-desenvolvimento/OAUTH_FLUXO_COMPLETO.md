# OAuth - Fluxo Completo de E-commerce

## 🎯 Fluxo Correto Implementado

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. CLIENTE ADICIONA PRODUTOS AO CARRINHO                         │
│    → Navega pela loja                                            │
│    → Adiciona produtos (carrinho salvo no localStorage)          │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. CLIENTE VAI PARA CHECKOUT                                     │
│    → /c/{empresaSlug}/checkout                                   │
│    → Sistema detecta: não está autenticado                       │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. TELA DE AUTENTICAÇÃO                                          │
│    Opções:                                                       │
│    A) Login com email/senha                                      │
│    B) Login com Google OAuth                                     │
│    C) Login com Microsoft OAuth                                  │
│    D) Continuar como convidado (sem cadastro)                    │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. CLIENTE ESCOLHE OAUTH (Google ou Microsoft)                   │
│    → Sistema salva:                                              │
│      • oauth_state (CSRF protection)                             │
│      • oauth_empresa_slug (qual loja)                            │
│      • oauth_return_url = /c/{empresaSlug}/checkout              │
│    → Redireciona para Google/Microsoft                           │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. AUTORIZAÇÃO NO PROVEDOR OAUTH                                 │
│    → Cliente faz login no Google/Microsoft                       │
│    → Cliente autoriza acesso ao email/nome                       │
│    → Provedor redireciona de volta com code                      │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. CALLBACK OAUTH (/auth/callback/google ou /microsoft)          │
│    → Frontend captura: code + state                             │
│    → Valida state (CSRF check)                                  │
│    → POST /auth/cliente/oauth/{provider}/callback               │
│    → Backend:                                                    │
│      1. Troca code por access_token do provedor                 │
│      2. Busca userinfo (email + nome)                           │
│      3. Busca/cria cliente no banco                             │
│      4. Gera JWT tokens (access + refresh)                      │
│      5. Retorna: { access_token, refresh_token, cliente }       │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 7. FRONTEND SALVA TOKEN E REDIRECIONA                            │
│    → Salva: localStorage.setItem('cliente_token', access_token) │
│    → Lê: oauth_return_url do localStorage                       │
│    → Limpa dados OAuth temporários                              │
│    → Redireciona para: oauth_return_url                         │
│    → Mostra: Toast "Bem-vindo, {nome}!" ✅                       │
└──────────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────────┐
│ 8. DE VOLTA AO CHECKOUT - AGORA AUTENTICADO                      │
│    → URL: /c/{empresaSlug}/checkout                             │
│    → Cliente está logado (tem cliente_token)                    │
│    → Carrinho preservado (estava no localStorage)               │
│    → Pode finalizar a compra! 🎉                                 │
└──────────────────────────────────────────────────────────────────┘
```

## 🔧 Implementação Técnica

### Frontend - CheckoutPage.tsx

**Iniciando OAuth Google:**

```typescript
const fazerLoginGoogle = async () => {
  setFazendoLogin(true);
  try {
    const empresaResponse = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
    const empresa_id = empresaResponse.data.id;
    const redirect_uri = `${window.location.origin}/auth/callback/google`;
    
    const response = await apiPublica.post('/auth/cliente/oauth/google/init', {
      redirect_uri,
      empresa_id
    });

    const { auth_url, state } = response.data;
    
    // Salvar contexto para retornar depois do OAuth
    localStorage.setItem('oauth_state', state);
    localStorage.setItem('oauth_empresa_slug', empresaSlug);
    localStorage.setItem('oauth_return_url', `/c/${empresaSlug}/checkout`); // ← IMPORTANTE!
    
    // Redirecionar para Google
    window.location.href = auth_url;
  } catch (error) {
    Toast.error('Erro ao iniciar login com Google');
    setFazendoLogin(false);
  }
};
```

**Iniciando OAuth Microsoft:**

```typescript
const fazerLoginMicrosoft = async () => {
  // Mesma lógica, só muda o endpoint:
  // '/auth/cliente/oauth/microsoft/init'
  // redirect_uri: '/auth/callback/microsoft'
};
```

### Frontend - GoogleCallback.tsx

**Processando retorno do OAuth:**

```typescript
const processarCallback = async () => {
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  const savedState = localStorage.getItem('oauth_state');
  const empresaSlug = localStorage.getItem('oauth_empresa_slug');

  // Validações de segurança
  if (!code || !state) return setErro('Parâmetros inválidos');
  if (state !== savedState) return setErro('State inválido - CSRF');
  if (!empresaSlug) return setErro('Sessão expirada');

  try {
    // Enviar code para backend trocar por token
    const response = await apiPublica.post('/auth/cliente/oauth/google/callback', {
      code,
      state,
    });

    const { access_token, cliente } = response.data;

    // Salvar token de autenticação
    localStorage.setItem('cliente_token', access_token);

    // Recuperar URL de retorno (onde estava antes do OAuth)
    const returnUrl = localStorage.getItem('oauth_return_url') || `/c/${empresaSlug}/checkout`;

    // Limpar dados temporários do OAuth
    localStorage.removeItem('oauth_state');
    localStorage.removeItem('oauth_empresa_slug');
    localStorage.removeItem('oauth_return_url');

    Toast.success(`Bem-vindo, ${cliente.nome}!`);

    // Voltar para onde estava (checkout com carrinho)
    navigate(returnUrl);
  } catch (error) {
    // Tratar erro...
  }
};
```

### Backend - auth_cliente.py

**Callback OAuth Google:**

```python
@router.post("/oauth/google/callback")
async def oauth_google_callback_cliente(
    response: Response,
    callback: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    # 1. Validar state (CSRF protection)
    state_data = await redis.get(f"oauth:cliente:state:{callback.state}")
    if not state_data:
        raise HTTPException(400, "State inválido")
    
    redirect_uri, empresa_id_str = state_data.decode('utf-8').split("|")
    empresa_id = int(empresa_id_str)
    
    # 2. Trocar code por access_token do Google
    token_response = await client.post("https://oauth2.googleapis.com/token", data={
        "code": callback.code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    })
    
    google_access_token = token_response.json()["access_token"]
    
    # 3. Buscar informações do usuário no Google
    user_response = await client.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"}
    )
    
    user_data = user_response.json()
    email = user_data["email"]
    nome = user_data["name"]
    
    # 4. Buscar ou criar ClienteAuth
    repo = ClienteAuthRepository(db)
    cliente_auth = await repo.buscar_por_email(email)
    
    if not cliente_auth:
        # Cliente não existe, criar no serviço de clientes
        cliente_response = await client.post(
            f"{settings.CLIENTES_URL}/clientes/oauth",
            json={
                "empresa_id": empresa_id,
                "nome": nome,
                "email": email
                # CPF e telefone são opcionais para OAuth
            },
            headers={"X-Empresa-Id": str(empresa_id)}
        )
        
        cliente_data = cliente_response.json()
        cliente_id = UUID(cliente_data["id"])
        
        # Criar autenticação
        cliente_auth = await repo.criar(
            email=email,
            senha="",  # OAuth não usa senha
            cliente_id=cliente_id,
            empresa_id=empresa_id
        )
    else:
        # Cliente já existe, buscar dados atualizados
        cliente_response = await client.get(
            f"{settings.CLIENTES_URL}/clientes/{cliente_auth.cliente_id}",
            headers={"X-Empresa-Id": str(empresa_id)}
        )
        cliente_data = cliente_response.json()
    
    # 5. Gerar tokens JWT
    access_token = create_access_token(
        user_id=cliente_auth.id,
        role="CLIENTE",
        user_type="cliente",
        empresa_id=empresa_id
    )
    refresh_token = create_refresh_token(cliente_auth.id)
    
    # 6. Salvar refresh token no Redis
    await redis.setex(
        f"refresh:cliente:{cliente_auth.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    # 7. Definir cookies (httpOnly + secure)
    set_auth_cookies(response, access_token, refresh_token)
    
    # 8. Retornar resposta
    return ClienteLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_type="cliente",
        cliente=cliente_data  # Dados completos do cliente
    )
```

## 🎯 Pontos-Chave da Implementação

### 1. **Carrinho Preservado**

O carrinho é salvo no `localStorage` do navegador, então:
- ✅ Não é perdido durante o OAuth redirect
- ✅ Cliente volta e encontra os produtos que adicionou
- ✅ Pode finalizar a compra imediatamente

### 2. **Return URL Dinâmica**

```typescript
localStorage.setItem('oauth_return_url', `/c/${empresaSlug}/checkout`);
```

Isso permite que no futuro você possa iniciar OAuth de outros lugares:
- Da página de produto (add to cart + OAuth)
- Da página de perfil (atualizar dados)
- De qualquer lugar que precise autenticação

### 3. **CSRF Protection**

O `state` é um token aleatório que:
- Backend gera e salva no Redis
- Frontend armazena no localStorage
- Callback valida se são iguais
- Previne ataques CSRF

### 4. **Dados Opcionais (CPF/Telefone)**

Clientes OAuth não precisam fornecer CPF/telefone no primeiro login:
- ✅ Menos fricção = mais conversões
- ✅ Podem preencher depois (no checkout se necessário)
- ✅ Compliance com LGPD

## 🧪 Testando o Fluxo Completo

### Passo a Passo

1. **Acesse a loja**: `https://runaserp.com.br/c/distribuidora-central`

2. **Adicione produtos ao carrinho**:
   - Clique em produtos
   - Adicione quantidades
   - Carrinho mostra os itens

3. **Vá para checkout**: 
   - Clique no carrinho
   - Clique em "Finalizar pedido"
   - Vai para `/c/distribuidora-central/checkout`

4. **Faça login com Google**:
   - Clique no botão "Login com Google"
   - Autorize no Google
   - Aguarde redirecionamento

5. **Verifique o resultado**:
   - ✅ Deve aparecer: "Bem-vindo, [Seu Nome]!"
   - ✅ Deve estar na página de checkout
   - ✅ Carrinho deve conter os produtos que você adicionou
   - ✅ Deve poder finalizar a compra

### Verificação Técnica (DevTools)

**Local Storage deve conter:**
```javascript
{
  "cliente_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", // JWT válido
  "carrinho_distribuidora-central": "[{produto_id: ..., quantidade: ...}]" // Produtos preservados
}
```

**Local Storage NÃO deve conter** (dados temporários limpos):
```javascript
{
  "oauth_state": "...",          // ❌ Deve ser removido
  "oauth_empresa_slug": "...",   // ❌ Deve ser removido
  "oauth_return_url": "..."      // ❌ Deve ser removido
}
```

**Network → Response do callback deve ser:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_type": "cliente",
  "cliente": {
    "id": "uuid",
    "nome": "Seu Nome",
    "email": "seu@email.com",
    "cpf": null,
    "telefone": null,
    "empresa_id": 4,
    "ativo": true
  }
}
```

## 🐛 Troubleshooting

### Problema: "State inválido"

**Causa**: State do localStorage não corresponde ao do backend.

**Solução**:
```javascript
// Limpar dados corrompidos
localStorage.removeItem('oauth_state');
localStorage.removeItem('oauth_empresa_slug');
localStorage.removeItem('oauth_return_url');
// Tentar novamente
```

### Problema: Carrinho vazio após login

**Causa**: Carrinho pode ter expirado ou sido limpo.

**Verificação**:
```javascript
// No DevTools Console
console.log(localStorage.getItem('carrinho_distribuidora-central'));
```

**Solução**: O carrinho é salvo por loja. Se mudou de loja durante o processo, é esperado que esteja vazio.

### Problema: Não redireciona após login

**Causa**: `oauth_return_url` não foi salvo.

**Verificação**:
```javascript
// Antes de clicar em "Login com Google"
console.log(localStorage.getItem('oauth_return_url'));
// Deve mostrar: /c/{empresaSlug}/checkout
```

**Solução**: Código já corrigido, mas se persistir, limpar cache e tentar novamente.

## 📊 Métricas de Sucesso

Para medir se o fluxo está funcionando:

1. **Taxa de Conversão OAuth**: % de clientes que completam o OAuth
2. **Taxa de Abandono no Callback**: % que não retorna após autorizar
3. **Tempo Médio do Fluxo**: Desde "Login com Google" até voltar ao checkout
4. **Taxa de Finalização**: % que completam a compra após OAuth

## 🚀 Melhorias Futuras

### 1. Carrinho no Backend (Session-based)

Em vez de localStorage, salvar no backend:
- Permite carrinho cross-device
- Mais seguro
- Não perde se limpar cache

### 2. Pre-fill de Dados

Se Google/Microsoft retornar telefone, preencher automaticamente no checkout.

### 3. Login Silencioso (Prompt None)

Se usuário já autorizou antes, não mostrar tela de consentimento novamente.

### 4. Social Login Buttons

Melhorar UI dos botões OAuth para aumentar confiança.

## 📚 Referências

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft OAuth 2.0 Documentation](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [OWASP OAuth Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)

---

**Implementado em**: 2026-06-25  
**Autor**: Kiro AI Assistant  
**Status**: ✅ Produção  
**Última Atualização**: Fluxo completo com preservação de carrinho
