"""
Router de Endereços.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from database import get_db
from services.cliente_service import ClienteService
from schemas.cliente import (
    EnderecoCreate,
    EnderecoUpdate,
    EnderecoResponse
)
from utils import get_empresa_id


router = APIRouter(prefix="/clientes/{cliente_id}/enderecos", tags=["Endereços"])
log = structlog.get_logger()


def get_cliente_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ClienteService:
    """Dependency para obter ClienteService."""
    return ClienteService(db)


@router.post(
    "",
    response_model=EnderecoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar endereço"
)
async def adicionar_endereco(
    cliente_id: UUID,
    data: EnderecoCreate,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Adiciona um novo endereço ao cliente (filtrado por empresa).
    
    - **cep**: CEP (8 dígitos)
    - **logradouro**: Rua, avenida, etc.
    - **numero**: Número do imóvel
    - **complemento**: Complemento (opcional)
    - **bairro**: Bairro
    - **cidade**: Cidade
    - **uf**: Estado (2 letras)
    - **principal**: Se é o endereço principal (padrão: false)
    """
    return await service.adicionar_endereco(cliente_id, empresa_id, data)


@router.get(
    "",
    response_model=list[EnderecoResponse],
    summary="Listar endereços"
)
async def listar_enderecos(
    cliente_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """Lista todos os endereços de um cliente (filtrado por empresa)."""
    return await service.listar_enderecos(cliente_id, empresa_id)


@router.patch(
    "/{endereco_id}",
    response_model=EnderecoResponse,
    summary="Atualizar endereço"
)
async def atualizar_endereco(
    cliente_id: UUID,
    endereco_id: UUID,
    data: EnderecoUpdate,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """
    Atualiza um endereço do cliente (filtrado por empresa).
    
    Apenas os campos fornecidos serão atualizados.
    """
    return await service.atualizar_endereco(cliente_id, empresa_id, endereco_id, data)


@router.delete(
    "/{endereco_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover endereço"
)
async def remover_endereco(
    cliente_id: UUID,
    endereco_id: UUID,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    empresa_id: Annotated[int, Depends(get_empresa_id)]
):
    """Remove um endereço do cliente (filtrado por empresa)."""
    await service.remover_endereco(cliente_id, empresa_id, endereco_id)
    return None
