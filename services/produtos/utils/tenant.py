"""
Utilitários para gerenciamento de multi-tenancy (tenant).
"""
from fastapi import Header, HTTPException, status


async def get_empresa_id(
    x_empresa_id: int | None = Header(None, description="ID da empresa (multi-tenancy)")
) -> int:
    """
    Extrai o empresa_id do header X-Empresa-Id.
    
    Args:
        x_empresa_id: ID da empresa enviado no header
        
    Returns:
        ID da empresa
        
    Raises:
        HTTPException: Se o header não for fornecido
    """
    if x_empresa_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Empresa-Id é obrigatório"
        )
    
    if x_empresa_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Empresa-Id deve ser maior que zero"
        )
    
    return x_empresa_id
