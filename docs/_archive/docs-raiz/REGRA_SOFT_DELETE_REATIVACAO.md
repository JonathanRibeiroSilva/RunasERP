# 🔄 Regra de Negócio: Soft Delete e Reativação Automática

> **Documento de especificação da regra de soft delete e reativação inteligente**
> 
> **Última atualização**: 27/05/2026
> **Arquivado em**: 28/05/2026 — Regra resumida em `CHECKLIST_DESENVOLVIMENTO.md` (seção Regras de Negócio)

---

## 🎯 Objetivo

Definir como o sistema deve se comportar ao desativar e reativar registros (clientes, produtos, fornecedores, etc.), garantindo:
- Preservação de histórico
- Integridade de dados financeiros
- Melhor experiência do usuário
- Evitar duplicação de registros

---

## 📋 Regra Geral

### 1. Consultas (GET) — Apenas Ativos

Todas as consultas retornam APENAS registros ativos. Registros inativos ficam "invisíveis" mas preservados no banco.

```
GET /clientes          → Só clientes ativos
GET /clientes/:id      → 404 se inativo
GET /produtos          → Só produtos ativos
```

### 2. Cadastro (POST) — Reativação Inteligente

```
1. Buscar por identificador único (CPF, SKU, CNPJ) incluindo inativos
2. Se NÃO existe → Criar novo registro
3. Se existe e está ATIVO → Erro 409 "Já cadastrado"
4. Se existe e está INATIVO → Reativar + Atualizar campos específicos
```

### 3. Campos que Atualizam vs Mantêm na Reativação

#### Clientes
**✅ ATUALIZAM**: Nome, Telefone, Email, Data de nascimento  
**❌ MANTÊM**: Limite de crédito, Crédito disponível, Saldo devedor, Dia de vencimento, Status de bloqueio

#### Produtos
**✅ ATUALIZAM**: Nome, Descrição, Categoria, Dados de catálogo  
**❌ MANTÊM**: Variantes, Relacionamentos com fornecedores, Histórico de vendas

---

## 🔧 Implementação Técnica

### Estrutura de Tabelas

```sql
CREATE TABLE clientes (
    id UUID PRIMARY KEY,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    -- ... outros campos ...
    ativo BOOLEAN DEFAULT TRUE NOT NULL,
    deletado_em TIMESTAMP NULL,
    deletado_por UUID NULL,
    INDEX idx_ativo (ativo),
    INDEX idx_cpf (cpf)
);
```

### Repository

```python
async def buscar_por_cpf(self, cpf: str, incluir_inativos: bool = False) -> Cliente | None:
    query = select(Cliente).where(Cliente.cpf == cpf)
    if not incluir_inativos:
        query = query.where(Cliente.ativo == True)
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

async def reativar(self, cliente_id: UUID, nome: str, telefone: str, email: str | None, data_nasc: date | None) -> Cliente:
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
    # NÃO toca em: limite_credito, credito_disponivel, dia_vencimento, bloqueado
    await self.db.flush()
    await self.db.refresh(cliente)
    return cliente
```

### Service

```python
async def criar_cliente(self, data: ClienteCreate) -> Cliente:
    async with self.db.begin_nested():
        cliente_existente = await self.cliente_repo.buscar_por_cpf(data.cpf, incluir_inativos=True)
        
        if cliente_existente:
            if cliente_existente.ativo:
                raise HTTPException(status_code=409, detail="CPF já cadastrado")
            
            log.info("cliente.reativando", cliente_id=str(cliente_existente.id), cpf=data.cpf)
            return await self.cliente_repo.reativar(
                cliente_existente.id, nome=data.nome, telefone=data.telefone,
                email=data.email, data_nasc=data.data_nasc
            )
        
        cliente = await self.cliente_repo.criar(data)
    
    await self.db.commit()
    return cliente
```

---

## 📊 Exemplo de Cenário

```python
# Estado anterior (inativo):
{ "cpf": "12345678900", "nome": "João Silva", "telefone": "(11) 11111-1111",
  "limite_credito": 5000.00, "credito_disponivel": 2000.00, "ativo": false }

# Novo cadastro:
POST /clientes { "cpf": "12345678900", "nome": "João Santos", "telefone": "(11) 99999-9999" }

# Resultado:
{ "cpf": "12345678900", "nome": "João Santos",       # ← ATUALIZADO
  "telefone": "(11) 99999-9999",                      # ← ATUALIZADO
  "limite_credito": 5000.00,                          # ← MANTIDO
  "credito_disponivel": 2000.00,                      # ← MANTIDO
  "ativo": true }                                     # ← REATIVADO
```

---

## 🎯 Aplicação

- ✅ Clientes (CPF)
- ✅ Produtos (SKU)
- ✅ Fornecedores (CNPJ)
- ✅ Categorias (Nome)
- ✅ Usuários (Email)

---

**Documento criado em**: 27/05/2026  
**Arquivado em**: 28/05/2026
