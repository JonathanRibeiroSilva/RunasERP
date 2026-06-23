# Changelog - Produtos Multi-Tenancy Adaptation

## Status: 100% Complete ✅

### ✅ Completed

#### 1. **Models** (100%)
- ✅ `models/produto.py` - Adicionado `empresa_id`, indexes
- ✅ `models/categoria.py` - Adicionado `empresa_id`, unique constraint `(empresa_id, nome)`
- ✅ `models/variante.py` - Adicionado `empresa_id`, unique constraint `(empresa_id, sku)`
- ✅ `models/fornecedor.py` - Adicionado `empresa_id`, unique constraint `(empresa_id, cnpj)`

#### 2. **Schemas** (100%)
- ✅ `schemas/produtos.py` - Adicionado `empresa_id` em:
  - `CategoriaBase`
  - `ProdutoBase`
  - `VarianteBase`
  - `FornecedorBase`

#### 3. **Utils** (100%)
- ✅ `utils/tenant.py` - Criado com função `get_empresa_id()`

#### 4. **Repositories** (100%)
- ✅ `CategoriaRepository` - 7 métodos adaptados com `empresa_id` filter
- ✅ `ProdutoRepository` - 9 métodos adaptados com `empresa_id` filter
- ✅ `VarianteRepository` - 7 métodos adaptados com `empresa_id` filter
- ✅ `FornecedorRepository` - 7 métodos adaptados com `empresa_id` filter
- ✅ Outros repositories (CatalogoConfig, CatalogoFoto, FornecedorProduto, AtributoVariante) - sem empresa_id direto pois dependem de produto/fornecedor

#### 5. **Services** (100%)
- ✅ `CategoriaService` - 5 métodos adaptados com `empresa_id` parameter
- ✅ `ProdutoService` - 8 métodos adaptados com `empresa_id` parameter
- ✅ `VarianteService` - 5 métodos adaptados com `empresa_id` parameter
- ✅ `CatalogoService` - 7 métodos adaptados com `empresa_id` parameter
- ✅ `FornecedorService` - 5 métodos adaptados com `empresa_id` parameter
- ✅ `FornecedorProdutoService` - 7 métodos adaptados com `empresa_id` parameter

#### 6. **Routers** (100%)
- ✅ Adicionado import `from utils.tenant import get_empresa_id`
- ✅ Adicionado import `from typing import Annotated`
- ✅ `router_categorias` - 5 endpoints adaptados
- ✅ `router_produtos` - 8 endpoints adaptados
- ✅ `router_variantes` - 5 endpoints adaptados
- ✅ `router_catalogo` - 7 endpoints adaptados
- ✅ `router_catalogo_publico` - 3 endpoints adaptados (com empresa_id)
- ✅ `router_fornecedores` - 5 endpoints adaptados
- ✅ `router_fornecedor_produtos` - 6 endpoints adaptados
- **Total**: 39 endpoints adaptados

#### 7. **Migration** (100%)
- ✅ `alembic/versions/20260609_add_empresa_id_multitenancy.py`
  - ADD COLUMN `empresa_id` INT NOT NULL DEFAULT 1 em:
    - `produtos.produtos`
    - `produtos.categorias`
    - `produtos.variantes`
    - `produtos.fornecedores`
  - DROP CONSTRAINT global unique em:
    - `categorias.nome`
    - `variantes.sku`
    - `fornecedores.cnpj`
    - `fornecedores.email`
  - ADD CONSTRAINT composite unique:
    - `uq_categorias_empresa_nome` ON `categorias` (empresa_id, nome)
    - `uq_variantes_empresa_sku` ON `variantes` (empresa_id, sku)
    - `uq_fornecedores_empresa_cnpj` ON `fornecedores` (empresa_id, cnpj)
  - CREATE INDEX:
    - `ix_produtos_empresa_id`, `ix_produtos_empresa_id_ativo`, `ix_produtos_empresa_id_nome`
    - `ix_categorias_empresa_id`
    - `ix_variantes_empresa_id_ativo`
    - `ix_fornecedores_empresa_id`, `ix_fornecedores_empresa_id_ativo`
  - Implementado `downgrade()` completo para reverter

#### 8. **Seed** (100%)
- ✅ `seed.py` - Criado seed completo com `empresa_id=1`:
  - 3 Categorias (Eletrônicos, Vestuário, Alimentos)
  - 3 Produtos (Notebook, Mouse, Camiseta)
  - 4 Variantes com atributos (tamanho, cor)
  - 2 Fornecedores (Dell, Logitech)
  - 2 Vínculos fornecedor-produto
  - 3 Configurações de catálogo
  - 2 Fotos de catálogo

---

## Changes Summary

### Pattern Applied

```python
# ROUTER (antes)
@router.post("/")
async def criar(dados: Schema, session: AsyncSession = Depends(get_db)):
    service = Service(session)
    return await service.criar(dados)

# ROUTER (depois)
@router.post("/")
async def criar(
    dados: Schema,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    # Validar body vs header em POST/PUT
    if dados.empresa_id != empresa_id:
        raise HTTPException(status_code=403, detail="empresa_id incompatível")
    
    service = Service(session)
    return await service.criar(empresa_id, dados)
```

### Files Modified (11 files)

1. ✅ `models/produto.py`
2. ✅ `models/categoria.py`
3. ✅ `models/variante.py`
4. ✅ `models/fornecedor.py`
5. ✅ `schemas/produtos.py`
6. ✅ `utils/tenant.py` (NEW)
7. ✅ `repositories/produtos.py`
8. ✅ `services/produtos.py`
9. ✅ `routers/produtos.py`
10. ✅ `alembic/versions/20260609_add_empresa_id_multitenancy.py` (NEW)
11. ✅ `seed.py`

### Statistics

- **Arquivos criados**: 2 (utils/tenant.py, migration)
- **Arquivos modificados**: 9
- **Endpoints adaptados**: 39
- **Métodos de repository**: 30+
- **Métodos de service**: 37
- **Linhas de código**: ~400 linhas adicionadas
- **Tempo estimado**: 3h de desenvolvimento

---

## Ready to Deploy

### Pre-deployment Checklist

- [x] Models updated with empresa_id
- [x] Schemas updated with empresa_id
- [x] Repositories filter by empresa_id
- [x] Services require empresa_id parameter
- [x] Routers use get_empresa_id() dependency
- [x] Migration created (upgrade + downgrade)
- [x] Seed data updated
- [x] Changelog documented

### Deployment Steps

1. **Backup database**:
   ```bash
   pg_dump -h localhost -U postgres -d erp_dev > backup_produtos_$(date +%Y%m%d).sql
   ```

2. **Run migration**:
   ```bash
   cd services/produtos
   alembic upgrade head
   ```

3. **Verify migration**:
   ```sql
   -- Check empresa_id column exists
   SELECT column_name, data_type FROM information_schema.columns 
   WHERE table_schema = 'produtos' AND column_name = 'empresa_id';
   
   -- Check unique constraints
   SELECT conname FROM pg_constraint 
   WHERE connamespace = 'produtos'::regnamespace;
   ```

4. **Run seed (optional)**:
   ```bash
   python seed.py
   ```

5. **Test endpoints**:
   ```bash
   # Test with X-Empresa-Id header
   curl -H "X-Empresa-Id: 1" http://localhost:8000/categorias
   ```

### Rollback Plan

If issues occur:
```bash
cd services/produtos
alembic downgrade -1
```

---

## Architecture Notes

### Multi-Tenancy Strategy

- **Approach**: Shared database, empresa_id column (Row-Level Multi-Tenancy)
- **Isolation**: Row-level security via WHERE clause in all queries
- **Header**: `X-Empresa-Id` required in all protected endpoints
- **Validation**: Body `empresa_id` must match header `empresa_id` on POST/PUT operations

### Unique Constraints

- **Before**: Global uniqueness (categoria.nome, variante.sku, fornecedor.cnpj)
- **After**: Per-tenant uniqueness (empresa_id, nome), (empresa_id, sku), (empresa_id, cnpj)
- **Benefit**: Different companies can have same category names, SKUs, and even CNPJ (for branches)

### Performance Optimizations

- **Indexes**: Composite indexes on (empresa_id, field) for common queries
- **Query pattern**: Always filter by empresa_id first (most selective column)
- **Index types**: B-tree indexes for equality and range queries

### Public Catalog Endpoints

- Endpoints em `/catalogo/publico` **agora requerem** empresa_id via header
- Retornam produtos com `catalogo_config.visivel = True`
- Isolamento por empresa mantido mesmo em endpoints públicos

### Security Considerations

- **Header validation**: Middleware valida presença de X-Empresa-Id
- **Body validation**: POST/PUT endpoints validam consistência empresa_id
- **Repository layer**: Sempre filtra por empresa_id (defense in depth)
- **No trust**: Nunca confiar apenas no frontend

---

## Testing Guide

### Manual Testing

```bash
# 1. Criar categoria para empresa 1
curl -X POST http://localhost:8004/categorias \
  -H "Content-Type: application/json" \
  -H "X-Empresa-Id: 1" \
  -d '{"empresa_id": 1, "nome": "Eletrônicos", "descricao": "Produtos eletrônicos"}'

# 2. Tentar acessar com empresa diferente (deve falhar)
curl -X POST http://localhost:8004/categorias \
  -H "Content-Type: application/json" \
  -H "X-Empresa-Id: 2" \
  -d '{"empresa_id": 1, "nome": "Teste", "descricao": "Teste"}'
# Expected: HTTP 403

# 3. Listar categorias da empresa 1
curl -X GET http://localhost:8004/categorias \
  -H "X-Empresa-Id: 1"

# 4. Listar categorias da empresa 2 (deve retornar vazio)
curl -X GET http://localhost:8004/categorias \
  -H "X-Empresa-Id: 2"
```

### Integration Testing

1. Criar dados para empresa_id=1
2. Criar dados para empresa_id=2
3. Verificar isolamento:
   - Queries de empresa 1 não retornam dados de empresa 2
   - SKUs duplicados entre empresas são permitidos
   - Categorias com mesmo nome entre empresas são permitidas

---

Generated: 2026-06-09
Status: Complete ✅
Next: Apply migration and test
