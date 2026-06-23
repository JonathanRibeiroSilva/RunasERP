"""Repositories."""
from repositories.produtos import (
    CategoriaRepository,
    ProdutoRepository,
    VarianteRepository,
    AtributoVarianteRepository,
    LojaOnlineConfigRepository,
    LojaOnlineFotoRepository,
    FornecedorRepository,
    FornecedorProdutoRepository,
)

__all__ = [
    "CategoriaRepository",
    "ProdutoRepository",
    "VarianteRepository",
    "AtributoVarianteRepository",
    "LojaOnlineConfigRepository",
    "LojaOnlineFotoRepository",
    "FornecedorRepository",
    "FornecedorProdutoRepository",
]