# Correção: Endpoints Públicos do Carrinho - Uso de empresa_slug

**Data**: 21/06/2026  
**Tipo**: fix  
**Escopo**: loja-online/carrinho

---

## 🎯 Problema Identificado

Alguns endpoints públicos do carrinho no router `/loja` estavam usando `get_empresa_id` ao invés de `get_empresa_id_from_slug`, o que causava erro nos endpoints públicos da loja online que dependem do slug da empresa na URL.

## ✅ Solução Implementada

### Arquivos Modificados

#### `services/vendas/routers/loja.py`

Corrigidos 4 endpoints que estavam usando `get_empresa_id`:

1. **`PUT /loja/carrinho/itens/{produto_id}`** (atualizar_quantidade_item)
   - ❌ Antes: `Depends(get_empresa_id)`
   - ✅ Depois: `Depends(get_empresa_id_from_slug)`

2. **`DELETE /loja/carrinho/itens/{produto_id}`** (remover_item_carrinho)
   - ❌ Antes: `Depends(get_empresa_id)`
   - ✅ Depois: `Depends(get_empresa_id_from_slug)`

3. **`DELETE /loja/carrinho`** (limpar_carrinho)
   - ❌ Antes: `Depends(get_empresa_id)`
   - ✅ Depois: `Depends(get_empresa_id_from_slug)`

4. **`GET /loja/meus-pedidos`** (listar_meus_pedidos)
   - ❌ Antes: `Depends(get_empresa_id)`
   - ✅ Depois: `Depends(get_empresa_id_from_slug)`

### Endpoints Já Corretos

Os seguintes endpoints já estavam usando `get_empresa_id_from_slug` corretamente:
- ✅ `GET /loja/carrinho` (obter_carrinho)
- ✅ `POST /loja/carrinho/itens` (adicionar_item_carrinho)
- ✅ `POST /loja/checkout` (processar_checkout)
- ✅ `GET /loja/rastrear/{numero_venda}` (rastrear_pedido)

## 🔍 Contexto

### Diferença entre `get_empresa_id` e `get_empresa_id_from_slug`

| Função | Fonte | Uso |
|--------|-------|-----|
| `get_empresa_id` | Cookie `empresa_id` | Endpoints administrativos autenticados |
| `get_empresa_id_from_slug` | Query param `empresaSlug` | Endpoints públicos da loja |

### Por que essa correção é importante?

1. **Endpoints públicos** (carrinho, checkout, catálogo) não têm cookie `empresa_id`
2. Clientes não autenticados acessam a loja pelo slug: `/loja?empresaSlug=minha-empresa`
3. O API Gateway faz proxy e passa o `empresaSlug` como query parameter
4. Usar `get_empresa_id` em endpoints públicos causa erro 401/403

## 🧪 Testes Sugeridos

```bash
# 1. Adicionar item ao carrinho (público)
POST /loja/carrinho/itens?empresaSlug=runas
{
  "produto_id": "uuid-produto",
  "quantidade": 2
}

# 2. Atualizar quantidade (agora corrigido)
PUT /loja/carrinho/itens/{produto_id}?empresaSlug=runas
{
  "quantidade": 3
}

# 3. Remover item (agora corrigido)
DELETE /loja/carrinho/itens/{produto_id}?empresaSlug=runas

# 4. Limpar carrinho (agora corrigido)
DELETE /loja/carrinho?empresaSlug=runas

# 5. Listar pedidos (agora corrigido)
GET /loja/meus-pedidos?empresaSlug=runas&cliente_id={uuid}
```

## 📋 Checklist de Qualidade

- [x] Código segue padrão Clean Code
- [x] Mantém consistência com outros endpoints públicos
- [x] Não quebra endpoints administrativos (eles usam `get_empresa_id` corretamente)
- [x] Documentação atualizada (este changelog)
- [ ] Testes manuais realizados
- [ ] Validado no ambiente de desenvolvimento

## 🎓 Lições Aprendidas

1. **Separação clara de contextos**: Endpoints públicos vs. administrativos
2. **Naming conventions**: Funções com nomes descritivos (`*_from_slug`) facilitam identificar o contexto
3. **Revisão sistemática**: Sempre verificar todos os endpoints de um router ao identificar um padrão incorreto

## 🔜 Próximos Passos

1. Validar correções em ambiente local
2. Testar fluxo completo do carrinho na loja online
3. Considerar criar um linter/validator que detecte uso incorreto de `get_empresa_id` em routers públicos

---

**Autor**: Kiro AI  
**Revisor**: Pendente
