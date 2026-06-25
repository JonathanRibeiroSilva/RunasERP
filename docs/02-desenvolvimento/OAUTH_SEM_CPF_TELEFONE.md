# OAuth sem CPF/Telefone Obrigatórios

## 📌 Problema Original

O fluxo de autenticação OAuth (Google/Microsoft) estava exigindo CPF e telefone, campos que não são fornecidos pelos provedores OAuth. Isso causava erro 422 ao criar clientes.

## ✅ Solução Implementada

### Arquitetura Correta

**OAuth não deve exigir CPF/telefone** - esses dados podem ser coletados opcionalmente após o primeiro login.

```
┌─────────────────────────────────────────────────────────────┐
│ Fluxo OAuth Correto                                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Cliente autoriza no Google/Microsoft                     │
│ 2. API Gateway recebe: email + nome                         │
│ 3. Cria cliente com APENAS email + nome                     │
│ 4. CPF/telefone = NULL (podem ser preenchidos depois)       │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Mudanças Implementadas

### 1. Schema Separado para OAuth

**Arquivo**: `services/clientes/schemas/cliente.py`

```python
class ClienteCreateOAuth(BaseModel):
    """Schema para criação de cliente via OAuth (sem CPF/telefone obrigatórios)."""
    empresa_id: int = Field(..., gt=0)
    nome: str = Field(..., min_length=3, max_length=255)
    email: str = Field(..., description="Email obrigatório para OAuth")
    cpf: str | None = Field(None, description="CPF opcional")
    telefone: str | None = Field(None, description="Telefone opcional")
    data_nasc: date | None = None
```

**Diferenças com `ClienteCreate`**:
- ✅ Email é obrigatório (não opcional)
- ✅ CPF é opcional (não obrigatório)
- ✅ Telefone é opcional (não obrigatório)

### 2. Migration de Banco de Dados

**Migration**: `20260624_215611_make_cpf_telefone_nullable_for_oauth.py`

```sql
-- Tornar CPF e telefone nullable
ALTER TABLE clientes.clientes 
  ALTER COLUMN cpf DROP NOT NULL,
  ALTER COLUMN telefone DROP NOT NULL;

-- Constraint única continua válida
-- PostgreSQL ignora NULLs em unique constraints
-- Múltiplos clientes OAuth (cpf=NULL) são permitidos
```

**Importante**: A constraint `uq_clientes_empresa_cpf` ainda garante unicidade de CPF quando preenchido.

### 3. Modelo ORM

**Arquivo**: `services/clientes/models/cliente.py`

```python
cpf: Mapped[str | None] = mapped_column(
    String(11), 
    nullable=True, 
    index=True, 
    comment="CPF opcional para clientes OAuth"
)

telefone: Mapped[str | None] = mapped_column(
    String(20), 
    nullable=True, 
    comment="Telefone opcional para clientes OAuth"
)
```

### 4. Repository

**Arquivo**: `services/clientes/repositories/cliente_repository.py`

**Novos métodos**:

```python
async def criar_oauth(self, data: ClienteCreateOAuth) -> Cliente:
    """Cria cliente OAuth sem CPF/telefone obrigatórios."""
    cliente = Cliente(
        empresa_id=data.empresa_id,
        cpf=data.cpf,  # Pode ser None
        nome=data.nome,
        telefone=data.telefone,  # Pode ser None
        email=data.email,
        data_nasc=data.data_nasc
    )
    # ... resto do código

async def buscar_por_email(self, email: str, empresa_id: int) -> Cliente | None:
    """Busca cliente por email (usado para verificar duplicatas OAuth)."""
    # ... implementação
```

### 5. Service

**Arquivo**: `services/clientes/services/cliente_service.py`

```python
async def criar_cliente_oauth(self, data: ClienteCreateOAuth) -> Cliente:
    """
    Cria cliente via OAuth.
    
    Regras:
    - Email deve ser único por empresa
    - CPF e telefone são opcionais
    - Se cliente inativo existe, reativa e atualiza
    """
    # Verifica duplicata por email (não CPF)
    cliente_existente = await self.cliente_repo.buscar_por_email(
        data.email, 
        data.empresa_id
    )
    
    if cliente_existente:
        if cliente_existente.ativo:
            raise HTTPException(409, "Email já cadastrado")
        else:
            # Reativar cliente inativo
            cliente_existente.ativo = True
            # ... atualizar dados
    
    return await self.cliente_repo.criar_oauth(data)
```

### 6. Router

**Arquivo**: `services/clientes/routers/clientes.py`

**Novo endpoint**:

```python
@router.post(
    "/oauth",
    response_model=ClienteResponse,
    status_code=201,
    summary="Criar cliente via OAuth"
)
async def criar_cliente_oauth(
    data: ClienteCreateOAuth,
    service: ClienteService = Depends(get_cliente_service),
    empresa_id: int = Depends(get_empresa_id)
):
    """
    Endpoint específico para criação via OAuth.
    Não exige CPF/telefone.
    """
    if data.empresa_id != empresa_id:
        raise HTTPException(400, "empresa_id mismatch")
    
    return await service.criar_cliente_oauth(data)
```

### 7. API Gateway

**Arquivo**: `api-gateway/routers/auth_cliente.py`

**Callback OAuth atualizado**:

```python
# ❌ ANTES (errado)
cliente_response = await client.post(
    f"{settings.CLIENTES_URL}/clientes",
    json={
        "cpf": "12345678909",  # CPF fake
        "telefone": "+5511000000000",  # Telefone fake
        "nome": nome,
        "email": email
    }
)

# ✅ DEPOIS (correto)
cliente_response = await client.post(
    f"{settings.CLIENTES_URL}/clientes/oauth",  # Endpoint específico
    json={
        "empresa_id": empresa_id,
        "nome": nome,
        "email": email
        # Sem CPF/telefone!
    },
    headers={"X-Empresa-Id": str(empresa_id)}
)
```

## 🎯 Fluxo Completo OAuth

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Cliente clica "Login com Google"                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Redireciona para Google OAuth                            │
│    → Cliente autoriza                                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Callback recebe: code + state                            │
│    → Troca code por access_token                            │
│    → Busca userinfo: {email, name}                          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Busca ClienteAuth por email                              │
│    → Se existe: faz login                                   │
│    → Se não existe: cria novo                               │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Criar cliente no serviço de clientes                     │
│    POST /clientes/oauth                                     │
│    {                                                         │
│      "empresa_id": 4,                                        │
│      "nome": "João Silva",                                   │
│      "email": "joao@gmail.com"                               │
│      // cpf: null                                            │
│      // telefone: null                                       │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Criar ClienteAuth no gateway                             │
│    {                                                         │
│      email: "joao@gmail.com",                                │
│      senha_hash: "",  // vazio para OAuth                    │
│      cliente_id: uuid,                                       │
│      empresa_id: 4                                           │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Gerar tokens JWT                                          │
│    → access_token                                            │
│    → refresh_token                                           │
│    → Definir cookies                                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. Cliente autenticado! ✅                                   │
│    → CPF/telefone podem ser pedidos depois                   │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Estrutura de Dados

### Tabela `clientes.clientes`

```sql
CREATE TABLE clientes.clientes (
    id UUID PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Campos opcionais para OAuth
    cpf VARCHAR(11) NULL,          -- ✅ Nullable
    telefone VARCHAR(20) NULL,     -- ✅ Nullable
    
    -- Campos obrigatórios
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NULL,
    data_nasc DATE NULL,
    
    -- Crédito
    limite_credito NUMERIC(10,2) DEFAULT 0,
    credito_disponivel NUMERIC(10,2) DEFAULT 0,
    dia_vencimento INTEGER NULL,
    
    -- Status
    bloqueado BOOLEAN DEFAULT FALSE,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT now(),
    
    -- Constraints
    CONSTRAINT uq_clientes_empresa_cpf UNIQUE (empresa_id, cpf)
    -- PostgreSQL ignora NULLs: múltiplos (empresa_id=4, cpf=NULL) são OK
);
```

### Tabela `gateway.clientes_auth`

```sql
CREATE TABLE gateway.clientes_auth (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,  -- "" para OAuth
    cliente_id UUID NOT NULL,          -- FK para clientes.clientes.id
    empresa_id INTEGER NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT now()
);
```

## 🔐 Segurança

### Validações Mantidas

1. **Email único por empresa**: Garante que não há duplicatas OAuth
2. **CPF único quando preenchido**: Constraint `uq_clientes_empresa_cpf` ainda funciona
3. **Validação de CPF**: Se fornecido, deve ser válido (validate_docbr)
4. **Telefone E.164**: Se fornecido, deve ser formato válido

### Coleta de Dados Posterior

O cliente OAuth pode preencher CPF/telefone depois:

```http
PATCH /clientes/{id}
{
  "cpf": "12345678909",
  "telefone": "+5511999999999"
}
```

A validação normal será aplicada nesse momento.

## 🧪 Testes

### Teste Manual

1. Acesse **https://runaserp.com.br**
2. Clique em **"Login com Google"**
3. Autorize a aplicação
4. ✅ Login deve funcionar sem pedir CPF/telefone

### Verificar Cliente Criado

```sql
SELECT id, nome, email, cpf, telefone, ativo
FROM clientes.clientes
WHERE email = 'seu-email@gmail.com';
```

Deve retornar:
- ✅ `cpf`: NULL
- ✅ `telefone`: NULL
- ✅ `email`: seu-email@gmail.com

## 📝 Considerações

### Por que CPF/Telefone São Opcionais?

1. **OAuth não fornece esses dados**: Google/Microsoft só retornam email e nome
2. **Fricção no cadastro**: Pedir dados extras afasta usuários
3. **Compliance**: LGPD recomenda coletar apenas dados necessários
4. **UX moderna**: Cadastro em 1 clique

### Quando Coletar CPF/Telefone?

- **No checkout**: Se necessário para NF-e
- **No primeiro pedido**: Para entrega
- **Opcional**: Para crédito/carnê

### Clientes Sem CPF

Clientes OAuth sem CPF podem:
- ✅ Fazer login
- ✅ Adicionar produtos ao carrinho
- ✅ Ver catálogo
- ⚠️ Podem precisar preencher CPF no checkout (dependendo da empresa)

## 🚀 Deploy

### Aplicar em Produção

```bash
# 1. Rodar migration no serviço de clientes
docker exec erp-clientes-prod alembic upgrade head

# 2. Reiniciar serviços
docker restart erp-clientes-prod erp-api-gateway-prod
```

### Rollback (Se Necessário)

```bash
# Reverter migration (⚠️ falhará se houver clientes OAuth com cpf=NULL)
docker exec erp-clientes-prod alembic downgrade -1
```

## 📚 Referências

- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [Google OAuth Scopes](https://developers.google.com/identity/protocols/oauth2/scopes)
- [PostgreSQL NULL in UNIQUE Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [LGPD - Princípio da Necessidade](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

---

**Implementado em**: 2026-06-24  
**Autor**: Kiro AI Assistant  
**Status**: ✅ Produção
