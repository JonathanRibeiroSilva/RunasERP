"""Routers do serviço de estoque."""
from .conferencia_visual import router as conferencia_visual_router
from .estoque import router as estoque_router

__all__ = ["conferencia_visual_router", "estoque_router"]
