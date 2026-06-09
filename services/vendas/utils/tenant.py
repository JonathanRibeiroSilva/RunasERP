"""
Utilidades para Multi-Tenancy.
"""
from typing import Annotated
from fastapi import Header, HTTPException


def get_empresa_id(
    x_empresa_id: Annotated[int, Header(alias="X-Empresa-Id")]
) -> int:
    """
    Extrai empresa_id do header X-Empresa-Id.
    
    Args:
        x_empresa_id: ID da empresa vindo do header
    
    Returns:
        int: ID da empresa validado
    
    Raises:
        HTTPException: 400 se header não for fornecido ou inválido
    """
    if not x_empresa_id or x_empresa_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Header X-Empresa-Id é obrigatório e deve ser > 0"
        )
    return x_empresa_id
