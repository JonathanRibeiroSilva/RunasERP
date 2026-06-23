# Changelog: Fix Catálogo Público - Erro 400 "Nenhum produto encontrado"

**Data**: 2026-06-12  
**Status**: ✅ Concluído

---

## 🎯 Problema Identificado

O catálogo público (`/c/distribuidora-central`) apresentava erro 400 ao tentar carregar produtos e categorias:

```
GET /api/catalogo/publico/produtos?limit=100&ordenar=nome → 400 Bad Request
GET /api/catalogo/publico/categorias → 400 Bad Request
```

**Causa Raiz:**
- Endpoints públicos de catálogo exigiam header `X-Empresa-Id`
- Frontend não enviava esse header (não tem como saber o `empresa_id`)
- Frontend só conhece `empresaSlug` da URL (`/c/{empresaSlug}`)

---

## 🛠️ Solução Implementada

### 1. Backend: Endpoints Públicos Atualizados

**Arquivo**: `services/produtos/routers/produtos.py`

Mudanças:
- ❌ **ANTES**: `Depends(get_empresa_id)` exigia header `X-Empresa-Id`
- ✅ **AGORA**: Recebe `empresaSlug` como query parameter e resolve internamente

#### Função Helper Criada

```python
async def get_empresa_id_from_slug(
    slug: str = Query(..., description="Slug da empresa"),
    session: AsyncSession = Depends(get_db)
) -> int:
    """Resolve empresa_id a partir do slug via query SQL direta."""
    query = text("""
        SELECT id 
        FROM empresas.empresas 
        WHERE slug = :slug AND status = 'ATIVA'
    """)
    result = await session.execute(query, {"slug": slug})
    row = result.fetchone()
    if not row:
        raise HTTPException(404, "Empresa não encontrada")
    return row[0]
```

#### Endpoints Atualizados

1. **GET /catalogo/publico/produtos**
   ```python
   async def listar_produtos_catalogo_publico(
       empresaSlug: str = Query(...),  # ✅ Novo parâmetro
       categoria_id: UUID | None = Query(None),
       busca: str | None = Query(None),
       ordenar: str = Query("nome"),
       skip: int = Query(0), 
       limit: int = Query(20),
       session: AsyncSession = Depends(get_db)
   )
   ```

2. **GET /catalogo/publico/categorias**
   ```python
   async def listar_categorias_catalogo_publico(
       empresaSlug: str = Query(...),  # ✅ Novo parâmetro
       session: AsyncSession = Depends(get_db)
   )
   ```

3. **GET /catalogo/publico/produto/{produto_id}**
   ```python
   async def obter_produto_catalogo_publico(
       produto_id: UUID,
       empresaSlug: str = Query(...),  # ✅ Novo parâmetro
       session: AsyncSession = Depends(get_db)
   )
   ```

---

### 2. Frontend: Atualizado para Enviar empresaSlug

**Arquivo**: `frontend/src/pages/CatalogoPublico/CatalogoPage.tsx`

```typescript
// ❌ ANTES
const params = new URLSearchParams({ limit: '100', ordenar: ordenacao });
await apiPublica.get(`/catalogo/publico/produtos?${params}`);
await apiPublica.get('/catalogo/publico/categorias');

// ✅ AGORA
const params = new URLSearchParams({ 
  empresaSlug: empresaSlug!,  // ✅ Enviando slug
  limit: '100', 
  ordenar: ordenacao 
});
await apiPublica.get(`/catalogo/publico/produtos?${params}`);
await apiPublica.get(`/catalogo/publico/categorias?empresaSlug=${empresaSlug}`);
```

**Arquivo**: `frontend/src/pages/CatalogoPublico/ProdutoDetalhePage.tsx`

```typescript
// ❌ ANTES
await apiPublica.get(`/catalogo/publico/produto/${produtoId}`);

// ✅ AGORA
await apiPublica.get(`/catalogo/publico/produto/${produtoId}?empresaSlug=${empresaSlug}`);
```

---

### 3. Fix de Dados: Produtos Migrados para Empresa Correta

**Problema Secundário Descoberto:**
- Seeds de produtos criaram 29 produtos para `empresa_id = 1`
- Mas empresas atuais começam do ID 4 (tabela foi recriada)
- Resultado: nenhum produto encontrado para `distribuidora-central` (ID 4)

**Solução:**
```sql
UPDATE produtos.produtos SET empresa_id = 4 WHERE empresa_id = 1;
UPDATE produtos.categorias SET empresa_id = 4 WHERE empresa_id = 1;
```

✅ Resultado: 29 produtos + 8 categorias migrados para empresa correta

---

## 📊 Testes Realizados

### 1. Endpoint de Produtos
```bash
GET /api/catalogo/publico/produtos?empresaSlug=distribuidora-central&limit=5
Response:
{
  "total": 29,
  "skip": 0,
  "limit": 5,
  "items": [
    { "nome": "Pão Francês kg", "ativo": true, ... },
    { "nome": "Bolo de Chocolate Fatia", "ativo": true, ... },
    ...
  ]
}
```
✅ Status: 200 OK

### 2. Endpoint de Categorias
```bash
GET /api/catalogo/publico/categorias?empresaSlug=distribuidora-central
Response:
{
  "total": 8,
  "items": [
    { "nome": "Alimentos", ... },
    { "nome": "Bebidas", ... },
    { "nome": "Higiene e Limpeza", ... },
    ...
  ]
}
```
✅ Status: 200 OK

### 3. Frontend
- ✅ Página `/c/distribuidora-central` carrega produtos
- ✅ Categorias carregam corretamente
- ✅ Nome fantasia da empresa aparece no topo
- ✅ Filtros funcionam (categoria, busca, ordenação)

---

## 🎯 Vantagens da Solução

1. **Simplicidade**: Não exige header customizado em endpoints públicos
2. **RESTful**: Slug como query param é mais semântico para recursos públicos
3. **Performance**: Query SQL direta é mais rápida que chamada HTTP entre serviços
4. **Segurança**: Valida status da empresa (apenas ATIVA retorna produtos)
5. **Cross-Schema**: Funciona mesmo com schemas separados no PostgreSQL

---

## 📝 Arquivos Modificados

### Backend
- `services/produtos/routers/produtos.py`
  - Função `get_empresa_id_from_slug()` criada
  - 3 endpoints públicos atualizados

### Frontend
- `frontend/src/pages/CatalogoPublico/CatalogoPage.tsx`
  - Função `carregarDados()` atualizada
- `frontend/src/pages/CatalogoPublico/ProdutoDetalhePage.tsx`
  - Função `carregarProduto()` atualizada

### Database
- Migration manual executada (atualização de empresa_id)

---

## 🚀 Próximos Passos (Sugeridos)

1. **Integração com Estoque**
   - Adicionar badge "Fora de Estoque" quando quantidade = 0
   - Desabilitar botão "Comprar" para produtos sem estoque

2. **Performance**
   - Adicionar cache Redis para resolver `slug → empresa_id`
   - Evitar consulta SQL em toda request

3. **Seed de Produtos**
   - Atualizar `seed_produtos.py` para usar empresa ativa dinamicamente
   - Não fixar `empresa_id = 1`

---

## ✅ Status Final

**Catálogo Público 100% funcional!**
- ✅ Produtos carregam corretamente
- ✅ Categorias carregam corretamente
- ✅ Nome fantasia da empresa exibido
- ✅ Filtros e busca funcionando
- ✅ Paginação funcionando
- ✅ Compartilhamento (link + WhatsApp) OK

**MVP pronto para demonstração!** 🎉
