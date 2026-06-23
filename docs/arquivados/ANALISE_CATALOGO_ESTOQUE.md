# Análise: Catálogo Público vs Estoque

## 📊 Resumo Executivo

**Produtos aparecem no catálogo baseado em 2 critérios:**
1. ✅ `produto.ativo = True` (produto está ativo no sistema)
2. ⚠️ `catalogo_config.visivel = True` (TODO: ainda não implementado)

**Estoque NÃO impacta visibilidade no catálogo atualmente.**

---

## 🏗️ Arquitetura

### Serviços Separados

```
┌─────────────────────┐    ┌─────────────────────┐
│ Serviço de Produtos │    │ Serviço de Estoque  │
│                     │    │                     │
│ - Produtos          │    │ - Estoque (qty)     │
│ - Categorias        │    │ - Lotes             │
│ - Variantes         │    │ - Movimentações     │
│ - CatalogoConfig    │    │ - Inventários       │
│ - CatalogoFotos     │    │                     │
└─────────────────────┘    └─────────────────────┘
        ↓                           ↓
    produtos.produtos          estoque.estoque
```

### Tabela Produtos

```sql
-- services/produtos/models/produto.py
produtos.produtos:
  - id (UUID)
  - empresa_id (int) -- Multi-tenancy
  - categoria_id (UUID)
  - nome (string)
  - descricao (text)
  - codigo_barras (string)
  - sku (string)
  - preco (decimal)
  - custo (decimal)
  - estoque_minimo (int) ← APENAS ALERTA, NÃO É ESTOQUE REAL
  - estoque_maximo (int) ← APENAS ALERTA
  - ativo (bool) ← CONTROLA VISIBILIDADE NO SISTEMA
  - catalogo_config → CatalogoConfig (1:1)
  - catalogo_fotos → CatalogoFoto[] (1:N)
```

**⚠️ IMPORTANTE**: 
- `estoque_minimo` e `estoque_maximo` são **apenas campos de alerta**
- **NÃO representam a quantidade real em estoque**
- São usados para notificar quando o estoque está baixo

### Tabela Estoque (Serviço Separado)

```sql
-- services/estoque/models/estoque.py
estoque.estoque:
  - id (UUID)
  - empresa_id (int)
  - produto_id (UUID) ← Referência ao produto
  - variante_id (UUID, opcional)
  - quantidade (decimal) ← QUANTIDADE REAL
  - quantidade_reservada (decimal)
  - quantidade_disponivel (decimal)
  - estoque_minimo (decimal) ← Limite para alerta
  - estoque_maximo (decimal)
  - localizacao (string)
  - ativo (bool)
```

---

## 🔍 Lógica Atual do Catálogo

### Endpoint: `/catalogo/publico/produtos`

**Localização**: `services/produtos/routers/produtos.py:383`

```python
async def listar_produtos_catalogo_publico(
    empresa_id: int,
    categoria_id: UUID | None,
    busca: str | None,
    ordenar: str,
    skip: int,
    limit: int,
):
    """
    Retorna produtos visíveis no catálogo.
    
    Filtros aplicados:
    ✅ produto.ativo = True
    ⚠️ TODO: catalogo_config.visivel = True (não implementado)
    ❌ NÃO filtra por estoque disponível
    """
    produtos, total = await service.listar_produtos(
        empresa_id=empresa_id,
        apenas_ativos=True  # ← Único filtro aplicado
    )
    
    return produtos
```

### O que está faltando

```python
# TODO no código:
# - Filtrar por catalogo_config.visivel = True
# - Integrar com serviço de estoque (opcional)
# - Mostrar badge "Fora de Estoque" no frontend
```

---

## 📦 Estado Atual dos Seeds

### ✅ Seeds Implementados

1. **Categorias** (`services/produtos/seed_categorias.py`)
   - 8 categorias padrão
   - Execução: `docker exec erp-produtos python seed_categorias.py`

2. **Produtos** (`services/produtos/seed_produtos.py`)
   - 29 produtos de exemplo
   - **Populado**: ❌ NÃO (banco vazio)
   - Execução: `docker exec erp-produtos python seed_produtos.py`

3. **Estoque** (`services/estoque/seed.py`)
   - 3 registros de estoque fictícios
   - **Usa UUIDs aleatórios** (não vincula aos produtos reais)
   - **Populado**: ❌ NÃO
   - Execução: `docker exec erp-estoque python seed.py`

4. **Empresas** (`services/empresas/seed.py`)
   - 3 empresas criadas
   - **Populado**: ✅ SIM
   - Execução: `docker exec erp-empresas python seed.py`

### ❌ Problema: Produtos não Populados

**Por que o catálogo está vazio:**
```
Catálogo → Busca produtos em produtos.produtos
         → Tabela está vazia
         → Nenhum produto retornado
```

---

## 🔧 Solução: Popul

ar Produtos

### Opção 1: Seed Rápido (Recomendado para MVP)

```bash
# 1. Executar seed de categorias
docker exec erp-produtos python seed_categorias.py

# 2. Executar seed de produtos
docker exec erp-produtos python seed_produtos.py

# 3. (Opcional) Seed de estoque
docker exec erp-estoque python seed.py
```

**Resultado**: 29 produtos aparecem no catálogo

### Opção 2: Vincular Estoque aos Produtos (Futuro)

**Problema atual**: O seed de estoque usa UUIDs aleatórios que não correspondem aos produtos reais.

**Solução**:
1. Modificar `services/estoque/seed.py` para buscar produtos reais do banco
2. Criar registros de estoque vinculados aos produtos do seed

```python
# Exemplo de seed melhorado
async def seed_estoque():
    # Buscar produtos reais do banco
    stmt = select(Produto).where(Produto.empresa_id == 1).limit(10)
    result = await session.execute(stmt)
    produtos = result.scalars().all()
    
    # Criar estoque para cada produto
    for produto in produtos:
        estoque = Estoque(
            empresa_id=1,
            produto_id=produto.id,
            quantidade=100.0,
            ...
        )
        session.add(estoque)
```

---

## 🎯 Integração Estoque ↔ Catálogo

### Cenários de Uso

#### Cenário 1: Mostrar Produtos Sem Estoque (Atual)
```
✅ Produto ativo → Aparece no catálogo
✅ Cliente pode ver e adicionar ao carrinho
⚠️ Erro só aparece no checkout se estoque = 0
```

**Vantagens**:
- Simples
- Cliente vê todo catálogo
- Útil para encomendas

**Desvantagens**:
- Cliente pode se frustrar ao não conseguir comprar

#### Cenário 2: Ocultar Produtos Sem Estoque (Futuro)
```
✅ Produto ativo + estoque > 0 → Aparece
❌ Produto ativo + estoque = 0 → Não aparece
```

**Implementação**:
```python
# No serviço de produtos, fazer query no estoque
async def listar_produtos_catalogo_publico(...):
    # 1. Buscar produtos ativos
    produtos = await produto_repo.listar(ativo=True)
    
    # 2. Para cada produto, consultar estoque
    produtos_com_estoque = []
    for prod in produtos:
        estoque = await httpx.get(f"http://estoque:8005/estoque/produto/{prod.id}")
        if estoque["quantidade_disponivel"] > 0:
            produtos_com_estoque.append(prod)
    
    return produtos_com_estoque
```

**Problema**: Performance (N+1 queries)

#### Cenário 3: Badge "Fora de Estoque" (Recomendado)
```
✅ Todos produtos ativos aparecem
✅ Badge visual indica estoque
✅ Botão "Comprar" desabilitado se estoque = 0
```

**Implementação**:
```typescript
// Frontend
<ProdutoCard>
  {estoque === 0 && <Badge>Fora de Estoque</Badge>}
  <Button disabled={estoque === 0}>Adicionar ao Carrinho</Button>
</ProdutoCard>
```

---

## 🚀 Recomendações para MVP

### Fase 1: MVP Funcional (AGORA)
1. ✅ Executar seeds de produtos
2. ✅ Catálogo mostra todos produtos ativos
3. ⚠️ Não verificar estoque no catálogo
4. ✅ Verificar estoque apenas no checkout

### Fase 2: Melhorias UX (Logo após MVP)
1. Integrar chamada HTTP entre produtos ↔ estoque
2. Adicionar badge "Fora de Estoque" no frontend
3. Desabilitar botão "Comprar" se estoque = 0

### Fase 3: Performance (Futuro)
1. Cache de estoque no Redis
2. Event-driven: estoque notifica produtos via RabbitMQ
3. Denormalização: copiar `quantidade_disponivel` para `produtos.estoque_cache`

---

## 📝 Comandos Úteis

```bash
# Ver produtos no banco
docker exec erp-db psql -U erp -d erp -c "SELECT COUNT(*) FROM produtos.produtos WHERE empresa_id = 1;"

# Ver estoque no banco
docker exec erp-db psql -U erp -d erp -c "SELECT COUNT(*) FROM estoque.estoque WHERE empresa_id = 1;"

# Executar todos os seeds
docker exec erp-produtos python seed_categorias.py
docker exec erp-produtos python seed_produtos.py
docker exec erp-estoque python seed.py
docker exec erp-empresas python seed.py

# Limpar dados
docker exec erp-db psql -U erp -d erp -c "DELETE FROM produtos.produtos WHERE empresa_id = 1;"
docker exec erp-db psql -U erp -d erp -c "DELETE FROM estoque.estoque WHERE empresa_id = 1;"
```

---

## 🎓 Conclusão

### Como funciona HOJE:
```
Produto cadastrado
└─ ativo = True
   └─ Aparece no catálogo ✅
      └─ Cliente adiciona ao carrinho
         └─ No checkout → Verifica estoque
            ├─ Estoque OK → Finaliza compra
            └─ Estoque = 0 → Erro "Produto indisponível"
```

### Estoque é gerenciado em serviço SEPARADO
- Tabela `estoque.estoque` (não `produtos.estoque_minimo`)
- Comunicação via HTTP entre serviços
- Controle de entrada/saída, lotes, inventários

### Para popular o MVP:
```bash
docker exec erp-produtos python seed_categorias.py
docker exec erp-produtos python seed_produtos.py
```

**Resultado**: 29 produtos visíveis no catálogo público! 🎉
