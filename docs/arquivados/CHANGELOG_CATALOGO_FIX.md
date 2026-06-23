# Fix: Produtos não aparecem no catálogo público

## 🐛 Problema

Ao gerar o link do catálogo de produtos, os produtos cadastrados não apareciam na página pública.

## 🔍 Causa Raiz

O método `listar_produtos` do `ProdutoService` não aceitava o parâmetro `apenas_ativos`, fazendo com que o filtro de produtos ativos fosse ignorado quando o endpoint do catálogo público tentava passar `apenas_ativos=True`.

**Fluxo com bug:**
```
Endpoint Catálogo Público
  ↓ chama service.listar_produtos(apenas_ativos=True)
ProdutoService.listar_produtos()
  ↓ ignora o parâmetro e passa apenas_ativos=None
ProdutoRepository.listar_todos(apenas_ativos=None)
  ↓ retorna TODOS os produtos (ativos e inativos)
```

## ✅ Solução Implementada

Adicionado o parâmetro `apenas_ativos` ao método `listar_produtos` do `ProdutoService`:

**Arquivo:** `services/produtos/services/produtos.py`

```python
async def listar_produtos(
    self, 
    skip: int = 0, 
    limit: int = 10, 
    apenas_deletados: bool = False,
    apenas_ativos: bool | None = None  # ← ADICIONADO
):
    """
    Lista produtos.
    
    Args:
        skip: Offset para paginação
        limit: Limite de resultados
        apenas_deletados: True = só deletados, False = todos não deletados
        apenas_ativos: True = só ativos, False = só inativos, None = todos
    """
    return await self.produto_repo.listar_todos(
        skip=skip, 
        limit=limit, 
        apenas_ativos=apenas_ativos,  # ← AGORA PASSA O PARÂMETRO
        apenas_deletados=apenas_deletados
    )
```

## 🎯 Resultado

Agora o catálogo público filtra corretamente apenas produtos ativos:
- ✅ `deletado_em IS NULL` (produtos não deletados)
- ✅ `ativo = True` (apenas produtos ativos)

## ⚠️ Próximos Passos

Ainda há um TODO no código para implementar o filtro por `catalogo_config.visivel = True`, que permitirá controlar individualmente quais produtos aparecem no catálogo público, mesmo que estejam ativos.

**Arquivo:** `services/produtos/routers/produtos.py` (linha 318)
```python
# TODO: Filtrar apenas produtos com catalogo_config.visivel = True
```

## 📝 Arquivos Modificados

- `services/produtos/services/produtos.py` - Adicionado parâmetro `apenas_ativos`

## 🧪 Como Testar

1. Acesse a página de produtos no sistema
2. Clique no botão "Compartilhar Catálogo"
3. Copie o link gerado
4. Abra o link em uma aba anônima (sem autenticação)
5. Verifique que apenas produtos ativos aparecem
6. Desative um produto no sistema
7. Recarregue o catálogo público
8. Confirme que o produto desativado não aparece mais
