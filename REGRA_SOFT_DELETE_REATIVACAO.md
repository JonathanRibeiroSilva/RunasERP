# 🔄 Regra de Negócio: Soft Delete e Reativação Automática

> **Documento de especificação da regra de soft delete e reativação inteligente**
> 
> **Última atualização**: 27/05/2026

---

## 🎯 Objetivo

Definir como o sistema deve se comportar ao desativar e reativar registros (clientes, produtos, fornecedores, etc.), garantindo:
- Preservação de histórico
- Integridade de dados financeiros
- Melhor experiência do usuário
- Evitar duplicação de registros

---

## 📋 Regra Geral

### 1. Consultas (GET) - Apenas Ativos

**Comportamento**: Todas as consultas retornam APENAS registros ativos.

```
GET /clientes                    → Só clientes ativos
GET /clientes?nome=João          → Só clientes ativos
GET /clientes?cpf=12345678900    → Só clientes ativos
GET /clientes/:id                → Só se estiver ativo (404 se inativo)

GET /produtos                    → Só produtos ativos
GET /produtos?sku=ABC123         → Só produtos ativos
```

**Justificativa**: 
- Interface limpa (não polui com registros desativados)
- Usuário não precisa ver dados históricos no dia a dia
- Registros inativos ficam "invisíveis" mas preservados no banco

---

### 2. Cadastro (POST) - Reativação Inteligente

**Comportamento**: Ao tentar cadastrar um registro com identificador único já existente:


```
Fluxo de Decisão:

1. Buscar por identificador único (CPF, SKU, CNPJ, etc.) incluindo inativos
2. Se NÃO existe → Criar novo registro
3. Se existe e está ATIVO → Retornar erro 409 "Já cadastrado"
4. Se existe e está INATIVO → Reativar + Atualizar campos específicos
```

**Exemplo - Clientes**:
```
POST /clientes { cpf: "12345678900", nome: "João" }

Cenário A: CPF não existe
→ Cria novo cliente

Cenário B: CPF existe e cliente está ativo
→ Erro 409: "CPF já cadastrado"

Cenário C: CPF existe mas cliente está inativo
→ Reativa o cliente existente
→ Atualiza dados cadastrais (nome, telefone, email)
→ Mantém dados financeiros (limite_credito, credito_disponivel)
```

---

### 3. Atualização na Reativação - Seletiva

**Princípio**: Atualizar o que pode ter mudado, preservar o que é histórico.

#### Clientes

**✅ ATUALIZAM (dados cadastrais)**:
- Nome (pode ter casado, mudado de nome)
- Telefone (pode ter trocado de número)
- Email (pode ter trocado de email)
- Data de nascimento (correção de cadastro)

**❌ MANTÊM (dados financeiros/operacionais)**:
- Limite de crédito (histórico financeiro)
- Crédito disponível (saldo atual)
- Saldo devedor (dívidas pendentes)
- Dia de vencimento (acordo comercial)
- Status de bloqueio (decisão operacional)


#### Produtos

**✅ ATUALIZAM**:
- Nome
- Descrição
- Categoria
- Dados de catálogo

**❌ MANTÊM**:
- Variantes (preservar histórico de preços)
- Relacionamentos com fornecedores
- Histórico de vendas

#### Fornecedores

**✅ ATUALIZAM**:
- Razão social
- Nome fantasia
- Telefone
- Email
- Endereço

**❌ MANTÊM**:
- Histórico de compras
- Condições de pagamento acordadas
- Produtos vinculados

---

## 💡 Justificativas

### Por que não atualizar dados financeiros?

**Cenário Real**:
```
1. Cliente João tinha limite de R$ 5.000
2. Comprou R$ 3.000 fiado (deve R$ 3.000)
3. Cliente foi desativado (parou de comprar)
4. 6 meses depois, volta a comprar
5. Se zerássemos os dados: perderia o histórico de dívida!
```

**Solução**: Manter dados financeiros intactos.

### Por que atualizar dados cadastrais?

**Cenário Real**:
```
1. Cliente João tinha telefone (11) 1111-1111
2. Cliente foi desativado
3. 6 meses depois, volta com novo telefone (11) 9999-9999
4. Se não atualizássemos: não conseguiríamos contatar o cliente!
```

**Solução**: Atualizar dados de contato.

---

## 🔧 Implementação Técnica

### Estrutura de Tabelas

```sql
-- Todos os cadastros principais devem ter:
CREATE TABLE clientes (
    id UUID PRIMARY KEY,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    -- ... outros campos ...
    
    -- Campos de soft delete
    ativo BOOLEAN DEFAULT TRUE NOT NULL,
    deletado_em TIMESTAMP NULL,
    deletado_por UUID NULL,
    
    -- Índices
    INDEX idx_ativo (ativo),
    INDEX idx_cpf (cpf)
);
```


### Repository - Busca com Filtro de Ativos

```python
async def buscar_por_cpf(
    self, 
    cpf: str, 
    incluir_inativos: bool = False
) -> Cliente | None:
    """
    Busca cliente por CPF.
    
    Args:
        cpf: CPF do cliente
        incluir_inativos: Se True, busca também inativos
                         Se False (padrão), busca apenas ativos
    
    Returns:
        Cliente encontrado ou None
    """
    query = select(Cliente).where(Cliente.cpf == cpf)
    
    # Por padrão, filtra apenas ativos
    if not incluir_inativos:
        query = query.where(Cliente.ativo == True)
    
    result = await self.db.execute(query)
    return result.scalar_one_or_none()
```

### Repository - Reativação

```python
async def reativar(
    self, 
    cliente_id: UUID,
    nome: str,
    telefone: str,
    email: str | None,
    data_nasc: date | None
) -> Cliente:
    """
    Reativa cliente e atualiza APENAS dados cadastrais.
    Mantém dados financeiros intactos.
    
    Args:
        cliente_id: ID do cliente a reativar
        nome: Novo nome (pode ter mudado)
        telefone: Novo telefone (pode ter mudado)
        email: Novo email (pode ter mudado)
        data_nasc: Data de nascimento (correção)
    
    Returns:
        Cliente reativado
    """
    cliente = await self.buscar_por_id(cliente_id)
    
    # Atualizar APENAS dados cadastrais
    cliente.nome = nome
    cliente.telefone = telefone
    cliente.email = email
    cliente.data_nasc = data_nasc
    
    # Reativar
    cliente.ativo = True
    cliente.deletado_em = None
    cliente.deletado_por = None
    
    # NÃO toca em dados financeiros:
    # - limite_credito (mantém)
    # - credito_disponivel (mantém)
    # - dia_vencimento (mantém)
    # - bloqueado (mantém)
    
    await self.db.flush()
    await self.db.refresh(cliente)
    
    return cliente
```


### Service - Lógica de Criação/Reativação

```python
async def criar_cliente(self, data: ClienteCreate) -> Cliente:
    """
    Cria um novo cliente ou reativa um existente.
    
    Regras:
    - Se CPF não existe: cria novo cliente
    - Se CPF existe e está ATIVO: retorna erro "CPF já cadastrado"
    - Se CPF existe e está INATIVO: reativa e atualiza dados cadastrais
    """
    try:
        async with self.db.begin_nested():
            # Buscar cliente por CPF (incluindo inativos)
            cliente_existente = await self.cliente_repo.buscar_por_cpf(
                data.cpf, 
                incluir_inativos=True  # ← IMPORTANTE
            )
            
            if cliente_existente:
                # Se está ativo, retorna erro
                if cliente_existente.ativo:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="CPF já cadastrado"
                    )
                
                # Se está inativo, reativa
                log.info(
                    "cliente.reativando", 
                    cliente_id=str(cliente_existente.id),
                    cpf=data.cpf
                )
                
                cliente = await self.cliente_repo.reativar(
                    cliente_existente.id,
                    nome=data.nome,
                    telefone=data.telefone,
                    email=data.email,
                    data_nasc=data.data_nasc
                )
                
                return cliente
            
            # CPF não existe, cria novo
            cliente = await self.cliente_repo.criar(data)
        
        await self.db.commit()
        log.info("cliente.criado", cliente_id=str(cliente.id), cpf=data.cpf)
        return cliente
        
    except HTTPException:
        await self.db.rollback()
        raise
    except Exception as e:
        await self.db.rollback()
        log.error("erro_criar_cliente", error=str(e))
        raise
```

---

## 📊 Exemplos de Cenários

### Cenário 1: Cliente Novo

```python
# Estado: CPF não existe no banco

POST /clientes {
  "cpf": "12345678900",
  "nome": "João Silva",
  "telefone": "(11) 98765-4321"
}

# Resultado: Cria novo cliente
{
  "id": "uuid-1",
  "cpf": "12345678900",
  "nome": "João Silva",
  "telefone": "(11) 98765-4321",
  "limite_credito": 0.00,
  "credito_disponivel": 0.00,
  "ativo": true
}
```


### Cenário 2: Cliente Já Existe (Ativo)

```python
# Estado: Cliente já existe e está ativo

POST /clientes {
  "cpf": "12345678900",
  "nome": "João Silva"
}

# Resultado: Erro 409
{
  "detail": "CPF já cadastrado"
}
```

### Cenário 3: Cliente Reativado

```python
# Estado anterior (inativo):
{
  "id": "uuid-1",
  "cpf": "12345678900",
  "nome": "João Silva",
  "telefone": "(11) 11111-1111",
  "email": "joao.silva@email.com",
  "limite_credito": 5000.00,
  "credito_disponivel": 2000.00,
  "dia_vencimento": 10,
  "bloqueado": false,
  "ativo": false,
  "deletado_em": "2026-01-15T10:00:00"
}

# Novo cadastro (6 meses depois):
POST /clientes {
  "cpf": "12345678900",
  "nome": "João Santos",  ← mudou (casou)
  "telefone": "(11) 99999-9999",  ← mudou
  "email": "joao.santos@email.com"  ← mudou
}

# Resultado: Cliente reativado e atualizado
{
  "id": "uuid-1",  ← MESMO ID
  "cpf": "12345678900",
  "nome": "João Santos",  ← ATUALIZADO
  "telefone": "(11) 99999-9999",  ← ATUALIZADO
  "email": "joao.santos@email.com",  ← ATUALIZADO
  "limite_credito": 5000.00,  ← MANTIDO
  "credito_disponivel": 2000.00,  ← MANTIDO
  "dia_vencimento": 10,  ← MANTIDO
  "bloqueado": false,  ← MANTIDO
  "ativo": true,  ← REATIVADO
  "deletado_em": null  ← LIMPO
}
```

---

## ✅ Benefícios

1. **Preserva Histórico**: Não perde dados financeiros e relacionamentos
2. **Evita Duplicação**: Reutiliza o mesmo registro
3. **Melhor UX**: Não dá erro confuso ao usuário
4. **Integridade**: Mantém IDs e foreign keys
5. **Auditoria**: Histórico completo de ativações/desativações
6. **Flexibilidade**: Dados cadastrais podem ser atualizados

---

## 🎯 Aplicação

Esta regra deve ser aplicada em:

- ✅ **Clientes** (identificador: CPF)
- ✅ **Produtos** (identificador: SKU)
- ✅ **Fornecedores** (identificador: CNPJ)
- ✅ **Categorias** (identificador: Nome)
- ✅ **Usuários** (identificador: Email)
- ✅ Qualquer cadastro com identificador único

---

## 🚨 Exceções

### Quando NÃO aplicar reativação automática:

1. **Dados sensíveis**: Senhas, tokens, chaves de API
2. **Dados temporários**: Sessões, carrinhos de compra
3. **Dados transacionais**: Vendas, pagamentos, movimentações

Nesses casos, sempre criar novo registro.

---

## 📝 Checklist de Implementação

- [ ] Adicionar campos `ativo`, `deletado_em`, `deletado_por` na tabela
- [ ] Criar índice em `ativo`
- [ ] Atualizar repository com `incluir_inativos` parameter
- [ ] Implementar método `reativar()` no repository
- [ ] Atualizar service com lógica de reativação
- [ ] Atualizar todas as queries para filtrar por `ativo=true`
- [ ] Adicionar testes unitários
- [ ] Adicionar testes de integração
- [ ] Documentar no Swagger
- [ ] Atualizar frontend para lidar com reativação

---

**Documento criado em**: 27/05/2026  
**Responsável**: Equipe de Backend  
**Status**: Especificação aprovada, aguardando implementação
