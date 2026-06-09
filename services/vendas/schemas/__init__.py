"""Schemas do serviço."""
from .venda import (
    ItemVendaCreate,
    ItemVendaResponse,
    PagamentoVendaCreate,
    PagamentoVendaResponse,
    VendaCreate,
    VendaUpdate,
    VendaResponse,
    VendaDetalhada,
    ConfirmarVendaRequest,
    CancelarVendaRequest,
    AdicionarPagamentoRequest,
    RelatorioVendas,
    VendaPorCliente,
    ProdutoMaisVendido
)

__all__ = [
    "ItemVendaCreate",
    "ItemVendaResponse",
    "PagamentoVendaCreate",
    "PagamentoVendaResponse",
    "VendaCreate",
    "VendaUpdate",
    "VendaResponse",
    "VendaDetalhada",
    "ConfirmarVendaRequest",
    "CancelarVendaRequest",
    "AdicionarPagamentoRequest",
    "RelatorioVendas",
    "VendaPorCliente",
    "ProdutoMaisVendido"
]
