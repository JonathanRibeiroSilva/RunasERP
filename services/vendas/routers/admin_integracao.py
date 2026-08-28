"""
Router Administrativo - Integrações do tenant (WhatsApp/Evolution e SMTP).

Sem try/except por decisão de arquitetura: os handlers globais de main.py são
donos do tratamento de erro (CLAUDE.md). O router vizinho admin_pagamento.py
ainda tem os try/except antigos — ele é o molde de estrutura, não disso.
"""
from typing import Annotated
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from utils.tenant import get_empresa_id
from services.configuracao_integracao_service import ConfiguracaoIntegracaoService

router = APIRouter(prefix="/integracoes", tags=["admin-integracoes"])


# ==================== SCHEMAS ====================

class IntegracaoUpsert(BaseModel):
    """
    Configuração de integrações do tenant.

    Segredos são opcionais e vazio significa "manter o atual": a tela exibe
    •••••• para o que já está configurado e só envia o campo quando o admin
    digita um valor novo.
    """
    # WhatsApp / Evolution
    evolution_url: str | None = Field(None, max_length=255)
    evolution_api_key: str | None = Field(None, max_length=500)
    evolution_instance: str | None = Field(None, max_length=100)
    whatsapp_ativo: bool | None = None

    # E-mail SMTP
    smtp_host: str | None = Field(None, max_length=255)
    smtp_port: int | None = Field(None, ge=1, le=65535)
    smtp_user: str | None = Field(None, max_length=255)
    smtp_password: str | None = Field(None, max_length=500)
    smtp_from_name: str | None = Field(None, max_length=100)
    email_ativo: bool | None = None


class IntegracaoResponse(BaseModel):
    """
    Estado das integrações — NUNCA devolve segredo.

    Os campos *_configurado são booleanos derivados: o admin precisa saber se
    há credencial gravada, não qual é. Devolver a chave permitiria ler pelo
    DevTools o que a cifra no banco existe para proteger.
    """
    id: UUID | None = None
    empresa_id: int

    evolution_url: str | None = None
    evolution_instance: str | None = None
    evolution_api_key_configurado: bool = False
    whatsapp_ativo: bool = False

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_from_name: str | None = None
    smtp_password_configurado: bool = False
    email_ativo: bool = False

    updated_at: datetime | None = None


def _para_response(config, empresa_id: int) -> IntegracaoResponse:
    """Projeta o registro para o schema público, trocando segredo por booleano."""
    if not config:
        return IntegracaoResponse(empresa_id=empresa_id)
    return IntegracaoResponse(
        id=config.id,
        empresa_id=config.empresa_id,
        evolution_url=config.evolution_url,
        evolution_instance=config.evolution_instance,
        evolution_api_key_configurado=bool(config.evolution_api_key_enc),
        whatsapp_ativo=config.whatsapp_ativo,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_user=config.smtp_user,
        smtp_from_name=config.smtp_from_name,
        smtp_password_configurado=bool(config.smtp_password_enc),
        email_ativo=config.email_ativo,
        updated_at=config.updated_at,
    )


# ==================== ENDPOINTS ====================

@router.get(
    "",
    response_model=IntegracaoResponse,
    summary="Obter Integrações",
    description="Estado das integrações do tenant (sem expor credenciais)"
)
async def obter_integracoes(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """Configuração do próprio tenant. Sem registro ainda devolve o estado vazio."""
    config = await ConfiguracaoIntegracaoService.obter_por_empresa(db, empresa_id)
    return _para_response(config, empresa_id)


@router.put(
    "",
    response_model=IntegracaoResponse,
    summary="Salvar Integrações",
    description="Cria ou atualiza as integrações do tenant"
)
async def salvar_integracoes(
    data: IntegracaoUpsert,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """Grava as integrações; segredos vão cifrados (utils/crypto.py)."""
    config = await ConfiguracaoIntegracaoService.criar_ou_atualizar(
        db, empresa_id, **data.model_dump(exclude_unset=True)
    )
    return _para_response(config, empresa_id)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover Integrações",
    description="Apaga as integrações do tenant (volta ao fallback global)"
)
async def remover_integracoes(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """Remove a configuração; o tenant volta a usar o SMTP/Evolution global."""
    if not await ConfiguracaoIntegracaoService.remover(db, empresa_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma configuração de integração para esta empresa"
        )
