# Refatoração: Catálogo → Loja Online

## Objetivo
Renomear todos os componentes relacionados a "catálogo" para "loja_online" (online_store) para melhor organização e clareza do código.

## Mapeamento de Nomes

### Backend (Python)

#### Modelos
- `CatalogoConfig` → `LojaOnlineConfig`
- `CatalogoFoto` → `LojaOnlineFoto`
- Arquivo: `models/catalogo.py` → `models/loja_online.py` ✅

#### Tabelas no Banco
- `produtos.catalogo_config` → `produtos.loja_online_config`
- `produtos.catalogo_fotos` → `produtos.loja_online_fotos`

#### Repositories
- `CatalogoConfigRepository` → `LojaOnlineConfigRepository`
- `CatalogoFotoRepository` → `LojaOnlineFotoRepository`

#### Services
- `CatalogoService` → `LojaOnlineService`

#### Schemas
- `CatalogoConfigBase` → `LojaOnlineConfigBase`
- `CatalogoConfigCreate` → `LojaOnlineConfigCreate`
- `CatalogoConfigRead` → `LojaOnlineConfigRead`
- `CatalogoConfigUpdate` → `LojaOnlineConfigUpdate`
- `CatalogoFotoBase` → `LojaOnlineFotoBase`
- `CatalogoFotoCreate` → `LojaOnlineFotoCreate`
- `CatalogoFotoRead` → `LojaOnlineFotoRead`
- `CatalogoFotoUpdate` → `LojaOnlineFotoUpdate`
- `ProdutoCatalogoRead` → `ProdutoLojaOnlineRead`
- `VarianteCatalogoRead` → `VarianteLojaOnlineRead`

#### Routers
- `router_catalogo` → `router_loja_online`

### Frontend (TypeScript/React)

#### Diretórios
- `pages/CatalogoPublico/` → `pages/LojaOnlinePublico/` ✅

#### Componentes
- `CatalogoPage` → `LojaOnlinePublicoPage`
- `ProdutoDetalhePage` (mantém, mas muda import)
- `CarrinhoPage` (mantém, mas muda import)
- `CheckoutPage` (mantém, mas muda import)
- `MeusPedidosPage` (mantém, mas muda import)
- `RastreamentoPedidoPage` (mantém, mas muda import)

#### Relacionamentos no Modelo Produto
- `produto.catalogo_config` → `produto.loja_online_config`
- `produto.catalogo_fotos` → `produto.loja_online_fotos`

## Status
- ✅ Diretório frontend movido
- ✅ Arquivo de modelo movido
- ✅ Classes e referências renomeadas
- ✅ Todos os imports atualizados
- ✅ Testes atualizados
- ✅ Commit realizado
- ⏳ Criando migração de banco de dados
- ⏳ Push para branch

## Arquivos Afetados
- Backend: 15 arquivos modificados
- Frontend: 17 arquivos movidos/modificados
- Testes: 2 arquivos atualizados
- Docs: 1 arquivo criado (este documento)
