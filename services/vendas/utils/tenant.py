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
            # Loja desabilitada pelo lojista → storefront indisponível.
            if not empresa.get('catalogo_ativo', False):
                return None
            return empresa['id']

    except httpx.HTTPError:
        return None


async def get_empresa_slug_by_id(
    db: AsyncSession,
    empresa_id: int
) -> Optional[str]:
    """
    Obtém o slug da empresa a partir do empresa_id consultando o serviço de empresas.

    Args:
        db: Sessão do banco (não utilizada, mantida para consistência com get_empresa_id_by_slug)
        empresa_id: ID da empresa

    Returns:
        str: Slug da empresa ou None se não encontrada
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://empresas:8007/empresas/{empresa_id}",
                headers={"X-Empresa-Id": str(empresa_id)},
                timeout=5.0
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            empresa = response.json()
            return empresa.get('slug')

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

            # Loja desabilitada pelo lojista: carrinho/checkout ficam indisponíveis,
            # mas o branding segue público para a página de manutenção.
            if not empresa.get('catalogo_ativo', False):
                raise HTTPException(
                    status_code=404,
                    detail="Loja indisponível no momento"
                )

            return empresa['id']

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar empresa: {str(e)}"
        )


def get_cliente_id(
    x_cliente_id: Annotated[Optional[str], Header(alias="X-Cliente-Id")] = None
) -> str:
    """
    Extrai cliente_id do header X-Cliente-Id (enviado pelo API Gateway quando cliente autenticado).
    
    Args:
        x_cliente_id: UUID do cliente vindo do header
    
    Returns:
        str: UUID do cliente validado
    
    Raises:
        HTTPException: 401 se header não for fornecido (não autenticado)
    """
    if not x_cliente_id:
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária. Cliente não autenticado."
        )
    
    # Validar formato UUID básico
    if len(x_cliente_id) < 32:
        raise HTTPException(
            status_code=400,
            detail="Header X-Cliente-Id inválido"
        )
    
    return x_cliente_id
