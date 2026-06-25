"""
Router de Clientes.
"""
from typing import Annotated
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from database import get_db
from services.cliente_service import ClienteService
from schemas.cliente import (
    ClienteCreate,
    ClienteCreateOAuth,
    ClienteUpdate,
    ClienteResponse,
    ClienteComEnderecos,
    CreditoUpdate,
    CreditoDelta
)
from utils import get_empresa_id


router = APIRouter(prefix="/clientes", tags=["Clientes"])
log = structlog.get_logger()


def get_cliente_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ClienteService:
    """Dependency para obter ClienteService."""
    return ClienteService(db)


@router.post(
    "",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar cliente"
)
async def criar_cliente(
    data: ClienteCreate,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Cria um novo cliente.
    
    - **empresa_id**: ID da empresa (multi-tenancy)
    - **cpf**: CPF do cliente (será validado)
    - **nome**: Nome completo
    - **telefone**: Telefone (formato E.164)
    - **email**: Email (opcional)
    - **data_nasc**: Data de nascimento (opcional)
    
    **Headers obrigatórios**:
    - X-Empresa-Id: ID da empresa
    """
    # Validar que empresa_id do body == empresa_id do header
    if data.empresa_id != empresa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"empresa_id no body ({data.empresa_id}) deve ser igual ao header X-Empresa-Id ({empresa_id})"
        )
    
    return await service.criar_cliente(data)


@router.post(
    "/oauth",
    response_model=ClienteResponse,
    status_code=status.HTTP_200_OK,  # Alterado para 200 pois pode retornar cliente existente
    summary="Criar cliente via OAuth"
)
async def criar_cliente_oauth(
    data: ClienteCreateOAuth,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Cria um novo cliente via OAuth (Google/Microsoft).
    
    - **empresa_id**: ID da empresa (multi-tenancy)
    - **nome**: Nome completo do usuário OAuth
    - **email**: Email do usuário OAuth (obrigatório)
    - **cpf**: CPF (opcional - pode ser preenchido depois)
    - **telefone**: Telefone (opcional - pode ser preenchido depois)
    
    **Headers obrigatórios**:
    - X-Empresa-Id: ID da empresa
    """
    # Validar que empresa_id do body == empresa_id do header
    if data.empresa_id != empresa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"empresa_id no body ({data.empresa_id}) deve ser igual ao header X-Empresa-Id ({empresa_id})"
        )
    
    return await service.criar_cliente_oauth(data)


@router.get(
    "",
    summary="Listar clientes"
)
async def listar_clientes(
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    nome: str | None = Query(None, description="Filtrar por nome ou CPF (busca parcial)"),
    cpf: str | None = Query(None, description="Filtrar por CPF exato"),
    bloqueado: bool | None = Query(None, description="Filtrar por status de bloqueio"),
    ativo: bool | None = Query(None, description="Filtrar por status ativo/inativo")
):
    """
    Lista clientes com paginação e filtros.
    
    Retorna apenas clientes da empresa especificada no header X-Empresa-Id.
    
    Retorna:
    - **items**: Lista de clientes
    - **total**: Total de registros
    - **skip**: Offset usado
    - **limit**: Limite usado
    """
    clientes, total = await service.listar_clientes(empresa_id, skip, limit, nome, cpf, bloqueado, ativo)
    
    # Converter modelos SQLAlchemy para schemas Pydantic
    clientes_response = [ClienteResponse.model_validate(cliente) for cliente in clientes]
    
    return {
        "clientes": clientes_response,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Buscar cliente por ID"
)
async def buscar_cliente(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """Busca um cliente por ID (filtrado por empresa)."""
    return await service.buscar_cliente(cliente_id, empresa_id)


@router.get(
    "/{cliente_id}/completo",
    response_model=ClienteComEnderecos,
    summary="Buscar cliente com endereços"
)
async def buscar_cliente_completo(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """Busca um cliente por ID incluindo seus endereços (filtrado por empresa)."""
    cliente = await service.buscar_cliente(cliente_id, empresa_id)
    enderecos = await service.listar_enderecos(cliente_id, empresa_id)
    
    # Converter para dict e adicionar endereços
    cliente_dict = ClienteResponse.model_validate(cliente).model_dump()
    cliente_dict["enderecos"] = enderecos
    
    return ClienteComEnderecos(**cliente_dict)


@router.get(
    "/cpf/{cpf}",
    response_model=ClienteResponse,
    summary="Buscar cliente por CPF"
)
async def buscar_por_cpf(
    cpf: str,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """Busca um cliente por CPF (filtrado por empresa)."""
    return await service.buscar_por_cpf(cpf, empresa_id)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar cliente"
)
async def atualizar_cliente(
    cliente_id: UUID,
    data: ClienteUpdate,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Atualiza dados de um cliente (filtrado por empresa).
    
    Apenas os campos fornecidos serão atualizados.
    """
    return await service.atualizar_cliente(cliente_id, empresa_id, data)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar cliente"
)
async def desativar_cliente(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Desativa um cliente (soft delete) (filtrado por empresa).
    
    O cliente não será removido do banco, apenas marcado como inativo.
    """
    await service.desativar_cliente(cliente_id, empresa_id)
    return None


@router.put(
    "/{cliente_id}/credito",
    response_model=ClienteResponse,
    summary="Definir limite de crédito"
)
async def definir_credito(
    cliente_id: UUID,
    data: CreditoUpdate,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Define o limite de crédito e dia de vencimento do cliente (filtrado por empresa).
    
    - **limite_credito**: Valor do limite (>= 0)
    - **dia_vencimento**: Dia do vencimento (1-28)
    """
    return await service.definir_credito(cliente_id, empresa_id, data)


@router.post(
    "/{cliente_id}/credito/ajustar",
    response_model=ClienteResponse,
    summary="Ajustar crédito disponível"
)
async def ajustar_credito(
    cliente_id: UUID,
    data: CreditoDelta,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Ajusta o crédito disponível do cliente (filtrado por empresa).
    
    - **delta**: Valor a ajustar (positivo = crédito, negativo = débito)
    
    Este endpoint é usado internamente pelos serviços de Vendas e Financeiro.
    """
    return await service.ajustar_credito(cliente_id, empresa_id, data.delta)


@router.post(
    "/{cliente_id}/bloquear",
    response_model=ClienteResponse,
    summary="Bloquear cliente"
)
async def bloquear_cliente(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Bloqueia um cliente manualmente (filtrado por empresa).
    
    Cliente bloqueado não pode fazer compras fiadas.
    """
    return await service.bloquear_cliente(cliente_id, empresa_id)


@router.post(
    "/{cliente_id}/desbloquear",
    response_model=ClienteResponse,
    summary="Desbloquear cliente"
)
async def desbloquear_cliente(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """Desbloqueia um cliente (filtrado por empresa)."""
    return await service.desbloquear_cliente(cliente_id, empresa_id)
