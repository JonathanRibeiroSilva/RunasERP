"""Services (lógica de negócio)."""
from services.produtos import (
    CategoriaService,
    ProdutoService,
    VarianteService,
    LojaOnlineService,
    FornecedorService,
    FornecedorProdutoService,
)

__all__ = [
    "CategoriaService",
    "ProdutoService",
    "VarianteService",
    "LojaOnlineService",
    "FornecedorService",
    "FornecedorProdutoService",
]