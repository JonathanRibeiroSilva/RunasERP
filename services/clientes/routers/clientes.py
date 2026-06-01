"""
Router de Clientes.
"""
from typing import Annotated
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from database import get_db
from services.cliente_service import ClienteService
from schemas.cliente import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteComEnderecos,
    CreditoUpdate,
    CreditoDelta
)


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
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """
    Cria um novo cliente.
    
    - **cpf**: CPF do cliente (será validado)
    - **nome**: Nome completo
    - **telefone**: Telefone (formato E.164)
    - **email**: Email (opcional)
    - **data_nasc**: Data de nascimento (opcional)
    """
    return await service.criar_cliente(data)


@router.get(
    "",
    summary="Listar clientes"
)
async def listar_clientes(
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    nome: str | None = Query(None, description="Filtrar por nome (busca parcial)"),
    cpf: str | None = Query(None, description="Filtrar por CPF"),
    bloqueado: bool | None = Query(None, description="Filtrar por status de bloqueio")
):
    """
    Lista clientes com paginação e filtros.
    
    Retorna:
    - **items**: Lista de clientes
    - **total**: Total de registros
    - **skip**: Offset usado
    - **limit**: Limite usado
    """
    clientes, total = await service.listar_clientes(skip, limit, nome, cpf, bloqueado)
    
    # Converter modelos SQLAlchemy para schemas Pydantic
    clientes_response = [ClienteResponse.model_validate(cliente) for cliente in clientes]
    
    return {
        "items": clientes_response,
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
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """Busca um cliente por ID."""
    return await service.buscar_cliente(cliente_id)


@router.get(
    "/{cliente_id}/completo",
    response_model=ClienteComEnderecos,
    summary="Buscar cliente com endereços"
)
async def buscar_cliente_completo(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """Busca um cliente por ID incluindo seus endereços."""
    cliente = await service.buscar_cliente(cliente_id)
    enderecos = await service.listar_enderecos(cliente_id)
    
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
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """Busca um cliente por CPF."""
    return await service.buscar_por_cpf(cpf)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar cliente"
)
async def atualizar_cliente(
    cliente_id: UUID,
    data: ClienteUpdate,
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """
    Atualiza dados de um cliente.
    
    Apenas os campos fornecidos serão atualizados.
    """
    return await service.atualizar_cliente(cliente_id, data)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar cliente"
)
async def desativar_cliente(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """
    Desativa um cliente (soft delete).
    
    O cliente não será removido do banco, apenas marcado como inativo.
    """
    await service.desativar_cliente(cliente_id)
    return None


@router.put(
    "/{cliente_id}/credito",
    response_model=ClienteResponse,
    summary="Definir limite de crédito"
)
async def definir_credito(
    cliente_id: UUID,
    data: CreditoUpdate,
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """
    Define o limite de crédito e dia de vencimento do cliente.
    
    - **limite_credito**: Valor do limite (>= 0)
    - **dia_vencimento**: Dia do vencimento (1-28)
    """
    return await service.definir_credito(cliente_id, data)


@router.post(
    "/{cliente_id}/credito/ajustar",
    response_model=ClienteResponse,
    summary="Ajustar crédito disponível"
)
async def ajustar_credito(
    cliente_id: UUID,
    data: CreditoDelta,
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """
    Ajusta o crédito disponível do cliente.
    
    - **delta**: Valor a ajustar (positivo = crédito, negativo = débito)
    
    Este endpoint é usado internamente pelos serviços de Vendas e Financeiro.
    """
    return await service.ajustar_credito(cliente_id, data.delta)


@router.post(
    "/{cliente_id}/bloquear",
    response_model=ClienteResponse,
    summary="Bloquear cliente"
)
async def bloquear_cliente(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """
    Bloqueia um cliente manualmente.
    
    Cliente bloqueado não pode fazer compras fiadas.
    """
    return await service.bloquear_cliente(cliente_id)


@router.post(
    "/{cliente_id}/desbloquear",
    response_model=ClienteResponse,
    summary="Desbloquear cliente"
)
async def desbloquear_cliente(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)]
):
    """Desbloqueia um cliente."""
    return await service.desbloquear_cliente(cliente_id)
