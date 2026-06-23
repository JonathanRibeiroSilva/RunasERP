# 📦 CHANGELOG - Produtos Multi-tenancy (WIP)

> **Data**: 08/06/2026  
> **Status**: 🔄 Em Progresso (Modelos Concluídos)

---

## ✅ Concluído

### 1. Modelos Atualizados

#### Produto ✅
- Campo `empresa_id` adicionado
- Índices compostos:
  - `ix_produtos_empresa_id_ativo`
  - `ix_produtos_empresa_id_nome`

#### Categoria ✅
- Campo `empresa_id` adicionado
- Unique constraint `(empresa_id, nome)`
- Índice `ix_categorias_empresa_id`
- Nome agora único por empresa

#### Variante ✅
- Campo `empresa_id` adicionado  
- Unique constraint `(empresa_id, sku)`
- Índice `ix_variantes_empresa_id_ativo`
- SKU agora único por empresa

### 2. Utilitários ✅
- `utils/tenant.py` - get_empresa_id()
- `utils/__init__.py`

---

## 🔄 Próximos Passos

1. Atualizar Schemas Pydantic
2. Atualizar Repositories (filtros por empresa)
3. Atualizar Services (regras de negócio)
4. Atualizar Routers (dependency injection)
5. Criar Migration Alembic
6. Atualizar Seed

---

**Status**: Modelos + Utilities = 30% completo
