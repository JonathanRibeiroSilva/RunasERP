"""
Rotas para Empresas.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResponse,
    EmpresaListItem,
    EmpresaPublicInfo,
)
from services.empresa_service import EmpresaService


router = APIRouter(prefix="/empresas", tags=["Empresas"])


async def exigir_tenant(
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-Id")
) -> int:
    """
    Tenant do chamador — injetado pelo gateway a partir do usuário autenticado.

    Fail closed: sem header não há como saber de qual tenant é a requisição,
    então rotas por empresa_id são rejeitadas (mesmo padrão dos demais serviços).
    """
    if not x_empresa_id or not x_empresa_id.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Empresa-Id é obrigatório"
        )
    return int(x_empresa_id)


def validar_tenant(empresa_id: int, tenant_id: int) -> None:
    """Isolamento multi-tenant: um lojista só acessa a própria empresa."""
    if empresa_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: empresa não pertence ao seu usuário"
        )


@router.post(
    "",
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova empresa",
    description="Cria uma nova empresa no sistema (multi-tenancy)"
)
async def criar_empresa(
    empresa_data: EmpresaCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova empresa.
    
    Validações:
    - CNPJ deve ser válido
    - CNPJ não pode estar cadastrado
    - Slug não pode estar em uso
    - Se for filial, matriz deve existir e ter limite disponível
    """
    service = EmpresaService(db)
    return await service.criar_empresa(empresa_data)


@router.get(
    "",
    response_model=dict,
    summary="Listar empresas",
    description="Lista empresas com filtros e paginação"
)
async def listar_empresas(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    busca: Optional[str] = Query(None, description="Buscar por razão social, nome fantasia ou CNPJ"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (MATRIZ ou FILIAL)"),
    status: Optional[str] = Query(None, description="Filtrar por status (ATIVA, INATIVA, SUSPENSA)"),
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista empresas com filtros opcionais.
    
    Retorna apenas empresas ativas (soft delete).
    """
    service = EmpresaService(db)
    empresas, total = await service.listar_empresas(
        skip=skip,
        limit=limit,
        busca=busca,
        tipo=tipo,
        status=status,
        uf=uf
    )
    
    return {
        "items": empresas,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/{empresa_id}",
    response_model=EmpresaResponse,
    summary="Buscar empresa por ID",
    description="Retorna os dados completos de uma empresa"
)
async def buscar_empresa(
    empresa_id: int,
    tenant_id: int = Depends(exigir_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca uma empresa específica por ID (apenas a própria empresa do chamador).
    """
    validar_tenant(empresa_id, tenant_id)
    service = EmpresaService(db)
    return await service.buscar_empresa(empresa_id)


@router.get(
    "/slug/{slug}",
    response_model=EmpresaResponse,
    summary="Buscar empresa por slug",
    description="Retorna os dados completos de uma empresa pelo slug"
)
async def buscar_empresa_por_slug(
    slug: str,
    tenant_id: int = Depends(exigir_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca uma empresa específica por slug (apenas a própria empresa do chamador).
    """
    service = EmpresaService(db)
    empresa = await service.buscar_empresa_por_slug(slug)
    validar_tenant(empresa.id, tenant_id)
    return empresa


@router.get(
    "/publico/{slug}",
    response_model=EmpresaPublicInfo,
    summary="Buscar informações públicas da empresa",
    description="Retorna informações públicas da empresa para exibição no catálogo"
)
async def buscar_info_publica(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca informações públicas da empresa para o catálogo.
    
    Retorna apenas se:
    - Empresa está ativa
    - Status é ATIVA
    - Catálogo está ativo
    """
    service = EmpresaService(db)
    return await service.buscar_info_publica(slug)


@router.put(
    "/{empresa_id}",
    response_model=EmpresaResponse,
    summary="Atualizar empresa",
    description="Atualiza os dados de uma empresa"
)
async def atualizar_empresa(
    empresa_id: int,
    empresa_data: EmpresaUpdate,
    tenant_id: int = Depends(exigir_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza uma empresa existente (apenas a própria empresa do chamador).

    Validações:
    - Se CNPJ for alterado, deve ser válido e único
    - Se slug for alterado, deve ser único
    """
    validar_tenant(empresa_id, tenant_id)
    service = EmpresaService(db)
    return await service.atualizar_empresa(empresa_id, empresa_data)


@router.delete(
    "/{empresa_id}",
    response_model=EmpresaResponse,
    summary="Desativar empresa",
    description="Desativa uma empresa (soft delete)"
)
async def desativar_empresa(
    empresa_id: int,
    tenant_id: int = Depends(exigir_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Desativa uma empresa (soft delete, apenas a própria empresa do chamador).

    A empresa não é removida do banco, apenas marcada como inativa.
    """
    validar_tenant(empresa_id, tenant_id)
    service = EmpresaService(db)
    return await service.desativar_empresa(empresa_id)


@router.get(
    "/{empresa_matriz_id}/filiais",
    response_model=list[EmpresaListItem],
    summary="Listar filiais",
    description="Lista todas as filiais de uma empresa matriz"
)
async def listar_filiais(
    empresa_matriz_id: int,
    tenant_id: int = Depends(exigir_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas as filiais de uma empresa matriz (apenas a própria matriz do chamador).
    """
    validar_tenant(empresa_matriz_id, tenant_id)
    service = EmpresaService(db)
    return await service.listar_filiais(empresa_matriz_id)
