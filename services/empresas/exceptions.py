"""
Exceções customizadas do serviço de empresas.
"""
from typing import Any, Dict, Optional


class BaseServiceError(Exception):
    """Exceção base para erros de serviço."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseServiceError):
    """Erro de validação de dados."""
    pass


class NotFoundError(BaseServiceError):
    """Recurso não encontrado."""
    pass


class ConflictError(BaseServiceError):
    """Conflito de dados (ex: duplicação)."""
    pass


class UnauthorizedError(BaseServiceError):
    """Erro de autenticação."""
    pass


class ForbiddenError(BaseServiceError):
    """Erro de permissão."""
    pass
