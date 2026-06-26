"""
Utilidades para Multi-Tenancy.
"""
from typing import Annotated, Optional
from fastapi import Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx


async def get_empresa_id_by_slug(
    db: AsyncSession,
    slug: str
) -> Optional[int]:
    """
    Obtém empresa_id a partir do slug consultando o serviço de empresas.
    
    Args:
        db: Sessão do banco (não utilizada, mas mantida para consistência)
        slug: Slug da empresa
    
    Returns:
        int: ID da empresa ou None se não encontrada
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://empresas:8007/empresas/publico/{slug}",
                timeout=5.0
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            empresa = response.json()
            return empresa['id']
            
    except httpx.HTTPError:
        return None


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


async def get_empresa_id_from_slug(
    empresaSlug: Annotated[Optional[str], Query()] = None
) -> int:
    """
    Obtém empresa_id a partir do slug.
    
    Args:
        empresaSlug: Slug da empresa (query param)
    
    Returns:
        int: ID da empresa
    
    Raises:
        HTTPException: 400 se slug não for fornecido ou empresa não encontrada
    """
    if not empresaSlug:
        raise HTTPException(
            status_code=400,
            detail="Query param 'empresaSlug' é obrigatório"
        )
    
    # Buscar empresa por slug
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://empresas:8007/empresas/publico/{empresaSlug}",
                timeout=5.0
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Empresa com slug '{empresaSlug}' não encontrada"
                )
            
            response.raise_for_status()
            empresa = response.json()
            return empresa['id']
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar empresa: {str(e)}"
        )
