"""
Utilitários para multi-tenancy.
"""
from fastapi import Header, HTTPException


def get_empresa_id(x_empresa_id: int = Header(..., alias="X-Empresa-Id")) -> int:
    """
    Extrai o empresa_id do header X-Empresa-Id.
    
    Args:
        x_empresa_id: ID da empresa enviado no header
        
    Returns:
        int: ID da empresa
        
    Raises:
        HTTPException: Se o header não for fornecido ou for inválido
    """
    if not x_empresa_id or x_empresa_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Header X-Empresa-Id é obrigatório e deve ser um número positivo"
        )
    return x_empresa_id
