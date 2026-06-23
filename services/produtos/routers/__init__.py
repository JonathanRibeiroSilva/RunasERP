"""Routers FastAPI."""
from routers.produtos import (
    router_categorias,
    router_produtos,
    router_variantes,
    router_loja_online,
    router_loja_online_publico,
    router_fornecedores,
    router_fornecedor_produtos,
)

__all__ = [
    "router_categorias",
    "router_produtos",
    "router_variantes",
    "router_loja_online",
    "router_loja_online_publico",
    "router_fornecedores",
    "router_fornecedor_produtos",
]