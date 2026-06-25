# Autenticação de Clientes - Endpoint `/clientes/me`

## 📋 Visão Geral

Implementação de autenticação segura para clientes da loja online usando **Opção A + B**:

- **Opção A**: Dependency `get_current_cliente()` reutilizável
- **Opção B**: Endpoint REST `/clientes/me` (convenção da indústria)

Esta solução combina segurança máxima com simplicidade de uso.

## 🎯 Problema Resolvido

### ❌ Problema Anterior

```typescript
// Frontend precisava decodificar JWT
const tokenPayload = JSON.parse(atob(token.split('.')[1]));
const cliente_id = tokenPayload.cliente_id;

// Fazer chamada com ID explícito
const response = await api.get(`/clientes/${cliente_id}`);
```

**Problemas:**
1. Frontend precisa conhecer estrutura do JWT
2. Risco de passar ID errado (bug ou malícia)
3. Código duplicado em vários lugares
4. Difícil manter consistência

### ✅ Solução Implementada

```typescript
// Frontend simplesmente chama /me
const response = await api.get('/clientes/me');
```

**Benefícios:**
1. ✅ Backend extrai ID do token automaticamente
2. ✅ Impossível acessar dados de outro cliente
3. ✅ Código mais simples e limpo
4. ✅ Segue convenção REST da indústria

## 🏗️ Arquitetura da Solução

### Opção A: Dependency Reutilizável

**Arquivo**: `api-gateway/auth/oauth2.py`

```python
async def get_current_cliente(
    token: Annotated[str, Depends(get_token_from_cookie_or_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
) -> ClienteAuth:
    """
    Obtém o cliente atual a partir do token JWT.
    
    Valida que o token é de um CLIENTE (não de usuário operador).
    """
    # 1. Verificar blacklist
    is_blacklisted = await redis.get(f"blacklist:{token}")
    if is_blacklisted:
        raise HTTPException(401, "Token revogado")
    
    # 2. Decodificar e validar token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Token inválido")
    
    # 3. Validar tipo de token
    if payload.get("user_type") != "cliente":
        raise HTTPException(403, "Token de cliente requerido")
    
    # 4. Buscar cliente_auth no banco
    user_id = payload.get("sub")
    repo = ClienteAuthRepository(db)
    cliente_auth = await repo.buscar_por_id(UUID(user_id))
    
    if not cliente_auth or not cliente_auth.ativo:
        raise HTTPException(401, "Cliente não encontrado ou inativo")
    
    return cliente_auth
```

**Validações realizadas:**
1. ✅ Token não está na blacklist (logout/revogação)
2. ✅ Token é válido (assinatura, expiração)
3. ✅ Token é de CLIENTE (não admin/operador)
4. ✅ Cliente existe no banco
5. ✅ Cliente está ativo

### Opção B: Endpoint `/clientes/me`

**Arquivo**: `api-gateway/routers/proxy.py`

```python
@router.get("/clientes/me", tags=["Clientes Público"])
async def proxy_cliente_me(
    request: Request,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)]
):
    """
    Cliente autenticado busca seus próprios dados.
    
    Extrai cliente_id do token JWT automaticamente.
    """
    cliente_id = str(current_cliente.cliente_id)
    full_path = f"/clientes/{cliente_id}"
    return await ServiceProxy.proxy_request(request, full_path)
```

**Fluxo:**
1. Cliente faz `GET /clientes/me` com token no header
2. Dependency `get_current_active_cliente` valida token
3. Backend extrai `cliente_id` do `ClienteAuth` retornado
4. Faz proxy para `/clientes/{cliente_id}` no serviço de clientes
5. Retorna dados do cliente

## 🔐 Segurança

### Proteções Implementadas

#### 1. Validação de Token
- Token deve estar no header `Authorization: Bearer <token>`
- Token não pode estar na blacklist (logout)
- Token deve ser válido (assinatura JWT)
- Token não pode estar expirado

#### 2. Validação de Tipo
```python
if payload.get("user_type") != "cliente":
    raise HTTPException(403, "Token de cliente requerido")
```
- Impede que admin/operador acesse rota de cliente
- Impede que token seja falsificado com tipo errado

#### 3. Validação de Ownership
```python
cliente_id = str(current_cliente.cliente_id)  # Do token, não da URL
```
- Cliente_id sempre vem do token (não confia no frontend)
- Impossível acessar dados de outro cliente
- Mesmo se tentar passar outro ID na URL, é ignorado

#### 4. Validação de Status
```python
if not cliente_auth.ativo:
    raise HTTPException(403, "Cliente inativo")
```
- Clientes desativados não conseguem acessar dados
- Importante para compliance (LGPD - direito ao esquecimento)

### Comparação com Outras Soluções

| Solução | Segurança | Simplicidade | Reutilizável |
|---------|-----------|--------------|--------------|
| A+B (Implementada) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| A (Dependency only) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| B (/me only) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| C (Delegate) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| D (Inline) | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| Rota pública | ❌ INSEGURO | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 💻 Como Usar

### Frontend: Buscar dados do cliente

```typescript
// Opção 1: Usando apiPublica
const response = await apiPublica.get('/clientes/me', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Empresa-Id': empresa_id
  }
});
const cliente = response.data;

// Opção 2: Com retry automático (implementado no CheckoutPage)
const cliente = await buscarClienteComRetry(empresa_id);
```

### Frontend: Atualizar dados do cliente

```typescript
const response = await apiPublica.patch('/clientes/me', {
  telefone: '11999999999',
  cpf: '12345678900'
}, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Empresa-Id': empresa_id
  }
});
```

### Backend: Criar rota protegida para cliente

```python
from auth.oauth2 import get_current_active_cliente

@router.get("/pedidos/me")
async def listar_meus_pedidos(
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)]
):
    """Lista pedidos do cliente autenticado"""
    cliente_id = current_cliente.cliente_id
    # ... buscar pedidos do cliente
    return pedidos
```

## 🌐 Convenção da Indústria

A rota `/me` é padrão em APIs REST modernas:

| API | Endpoint | Descrição |
|-----|----------|-----------|
| GitHub | `GET /user` | Dados do usuário autenticado |
| Google | `GET /userinfo/me` | Informações do usuário OAuth |
| Facebook | `GET /me` | Perfil do usuário logado |
| Twitter | `GET /account/verify_credentials` | Credenciais do usuário |
| Stripe | `GET /account` | Conta do usuário logado |
| Discord | `GET /users/@me` | Usuário autenticado |

**Vantagens da convenção:**
- Desenvolvedores já conhecem o padrão
- Menos documentação necessária
- Mais intuitivo de usar
- Semântica clara ("meus dados")

## 📊 Fluxo Completo

### 1. Login via OAuth (Google)

```
Frontend                  API Gateway              Google
   |                          |                       |
   |--POST /oauth/google/init->|                       |
   |<---auth_url + state-------|                       |
   |                          |                       |
   |--Redirect to Google------------------------------>|
   |                          |                       |
   |<--Callback with code------------------------------|
   |                          |                       |
   |--POST /oauth/google/callback------------------->  |
   |  { code, state }         |                       |
   |                          |--Exchange code-------->|
   |                          |<--User info-----------|
   |                          |                       |
   |                          | [Create/fetch cliente]|
   |                          | [Generate JWT]        |
   |                          |                       |
   |<--{ access_token, cliente }|                      |
   |                          |                       |
   | localStorage.setItem('cliente_token', token)     |
```

### 2. Buscar dados após OAuth

```
Frontend                  API Gateway              Clientes Service
   |                          |                       |
   | token = localStorage.getItem('cliente_token')    |
   |                          |                       |
   |--GET /clientes/me------->|                       |
   |  Authorization: Bearer token                     |
   |                          |                       |
   |                          | [Validate token]      |
   |                          | [Extract cliente_id]  |
   |                          |                       |
   |                          |--GET /clientes/{id}-->|
   |                          |  X-Empresa-Id: 1      |
   |                          |                       |
   |                          |<--{ cliente data }-----|
   |<--{ cliente data }-------|                       |
   |                          |                       |
   | [Pre-fill form with data]                        |
```

## 🧪 Testes

### Teste Manual 1: Buscar próprios dados

```powershell
# 1. Fazer login e obter token
$response = Invoke-RestMethod -Uri "https://www.runaserp.com.br/api/auth/cliente/login" `
  -Method POST `
  -Body (@{email="teste@email.com"; senha="senha123"} | ConvertTo-Json) `
  -ContentType "application/json"

$token = $response.access_token

# 2. Buscar dados usando /me
$cliente = Invoke-RestMethod -Uri "https://www.runaserp.com.br/api/clientes/me" `
  -Method GET `
  -Headers @{
    "Authorization" = "Bearer $token"
    "X-Empresa-Id" = "1"
  }

Write-Host "Cliente: $($cliente.nome)"
```

### Teste Manual 2: Tentar acessar outro cliente (deve falhar)

```powershell
# Mesmo com token válido, não pode acessar outro ID
$outro = Invoke-RestMethod -Uri "https://www.runaserp.com.br/api/clientes/outro-id-qualquer" `
  -Method GET `
  -Headers @{
    "Authorization" = "Bearer $token"
    "X-Empresa-Id" = "1"
  }
# ❌ Deve retornar 404 ou 403 (rota não existe ou sem permissão)
```

### Teste Manual 3: Token de admin não funciona em rota de cliente

```powershell
# Login como admin
$adminToken = "token-de-admin..."

# Tentar acessar rota de cliente
$response = Invoke-RestMethod -Uri "https://www.runaserp.com.br/api/clientes/me" `
  -Method GET `
  -Headers @{
    "Authorization" = "Bearer $adminToken"
    "X-Empresa-Id" = "1"
  }
# ❌ Deve retornar 403: "Token de cliente requerido"
```

## 🔄 Reutilização da Dependency

A dependency `get_current_active_cliente` pode ser usada em outras rotas:

### Exemplo 1: Listar pedidos do cliente

```python
@router.get("/pedidos/me")
async def listar_meus_pedidos(
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Lista todos os pedidos do cliente autenticado"""
    cliente_id = current_cliente.cliente_id
    
    pedidos = await db.execute(
        select(Pedido)
        .where(Pedido.cliente_id == cliente_id)
        .order_by(Pedido.criado_em.desc())
    )
    
    return pedidos.scalars().all()
```

### Exemplo 2: Adicionar endereço

```python
@router.post("/clientes/me/enderecos")
async def adicionar_endereco(
    endereco: EnderecoCreate,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Adiciona novo endereço ao cliente autenticado"""
    cliente_id = current_cliente.cliente_id
    
    novo_endereco = Endereco(
        cliente_id=cliente_id,
        **endereco.dict()
    )
    
    db.add(novo_endereco)
    await db.commit()
    
    return novo_endereco
```

### Exemplo 3: Atualizar preferências

```python
@router.patch("/clientes/me/preferencias")
async def atualizar_preferencias(
    preferencias: PreferenciasUpdate,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)]
):
    """Atualiza preferências do cliente autenticado"""
    cliente_id = current_cliente.cliente_id
    # ... atualizar preferências
    return {"message": "Preferências atualizadas"}
```

## 📈 Próximos Passos

### Rotas futuras que podem usar a dependency

1. **Pedidos**:
   - `GET /pedidos/me` - listar meus pedidos
   - `GET /pedidos/me/{id}` - detalhes de um pedido
   - `POST /pedidos/me/{id}/cancelar` - cancelar pedido

2. **Endereços**:
   - `GET /clientes/me/enderecos` - listar endereços
   - `POST /clientes/me/enderecos` - adicionar endereço
   - `PATCH /clientes/me/enderecos/{id}` - editar endereço
   - `DELETE /clientes/me/enderecos/{id}` - remover endereço

3. **Favoritos**:
   - `GET /clientes/me/favoritos` - produtos favoritos
   - `POST /clientes/me/favoritos/{produto_id}` - favoritar
   - `DELETE /clientes/me/favoritos/{produto_id}` - desfavoritar

4. **Notificações**:
   - `GET /clientes/me/notificacoes` - listar notificações
   - `PATCH /clientes/me/notificacoes/{id}/ler` - marcar como lida

## 📚 Referências

- [RFC 7519 - JWT Standard](https://datatracker.ietf.org/doc/html/rfc7519)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [OAuth 2.0 Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [REST API Design - Resource Naming](https://restfulapi.net/resource-naming/)

## 🎉 Conclusão

A solução **Opção A + B** combina:
- ✅ **Segurança máxima**: validação em múltiplas camadas
- ✅ **Simplicidade de uso**: API intuitiva (`/me`)
- ✅ **Reutilizabilidade**: dependency para outras rotas
- ✅ **Padrão da indústria**: convenção REST reconhecida
- ✅ **Manutenibilidade**: código limpo e organizado

Esta é a solução recomendada para autenticação de clientes em sistemas modernos.
