"""Repositories do serviço."""
from .venda_repository import (
    VendaRepository,
    ItemVendaRepository,
    PagamentoVendaRepository,
    ReservaEstoqueVendaRepository
)

__all__ = [
    "VendaRepository",
    "ItemVendaRepository",
    "PagamentoVendaRepository",
    "ReservaEstoqueVendaRepository"
]
