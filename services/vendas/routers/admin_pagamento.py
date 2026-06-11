"""
Router Administrativo - Configuração de Pagamento (Mercado Pago).
Endpoints para gerenciar credenciais do Mercado Pago por empresa.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from database import get_db
from utils.tenant import get_empresa_id
from services.configuracao_pagamento_service import ConfiguracaoPagamentoService

router = APIRouter(prefix="/admin/pagamento", tags=["admin-pagamento"])


# ==================== SCHEMAS ====================

class ConfiguracaoPagamentoCreate(BaseModel):
    """Schema para criar configuração de pagamento."""
    mercadopago_access_token: str = Field(
        ...,
        min_length=20,
        description="Access Token do Mercado Pago"
    )
    mercadopago_public_key: str = Field(
        ...,
        min_length=20,
        description="Public Key do Mercado Pago"
    )
    ativo: bool = Field(default=True, description="Configuração ativa?")


class ConfiguracaoPagamentoUpdate(BaseModel):
    """Schema para atualizar configuração de pagamento."""
    mercadopago_access_token: str = Field(
        ...,
        min_length=20,
        description="Access Token do Mercado Pago"
    )
    mercadopago_public_key: str = Field(
        ...,
        min_length=20,
        description="Public Key do Mercado Pago"
    )
    ativo: bool = Field(default=True, description="Configuração ativa?")


class ConfiguracaoPagamentoResponse(BaseModel):
    """Schema de resposta da configuração de pagamento."""
    id: UUID
    empresa_id: int
    mercadopago_public_key: str  # Não expõe access_token por segurança
    ativo: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ConfiguracaoPagamentoStatusResponse(BaseModel):
    """Schema de status da configuração (sem credenciais)."""
    configurado: bool = Field(..., description="Se tem configuração ativa")
    ativo: bool = Field(default=False, description="Se configuração está ativa")
    ultima_atualizacao: datetime | None = Field(None, description="Data da última atualização")


# ==================== ENDPOINTS ====================

@router.get(
    "/status",
    response_model=ConfiguracaoPagamentoStatusResponse,
    summary="Verificar Status da Configuração",
    description="Verifica se Mercado Pago está configurado (sem expor credenciais)"
)
async def verificar_status_configuracao(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica se Mercado Pago está configurado para a empresa.
    
    **Retorna**:
    - `configurado`: True se tem configuração
    - `ativo`: True se configuração está ativa
    - `ultima_atualizacao`: Data da última atualização
    
    **Não expõe**: Access Token ou Public Key (segurança)
    """
    try:
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)
        
        if not config:
            return ConfiguracaoPagamentoStatusResponse(
                configurado=False,
                ativo=False,
                ultima_atualizacao=None
            )
        
        return ConfiguracaoPagamentoStatusResponse(
            configurado=True,
            ativo=config.ativo,
            ultima_atualizacao=config.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar status: {str(e)}"
        )


@router.get(
    "/configuracao",
    response_model=ConfiguracaoPagamentoResponse,
    summary="Obter Configuração de Pagamento",
    description="Obtém configuração do Mercado Pago da empresa"
)
async def obter_configuracao_pagamento(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém configuração de pagamento da empresa.
    
    **Segurança**: Não expõe `access_token` na resposta, apenas `public_key`.
    
    **404**: Se não houver configuração cadastrada.
    """
    try:
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuração de pagamento não encontrada. Use POST para criar."
            )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter configuração: {str(e)}"
        )


@router.post(
    "/configuracao",
    response_model=ConfiguracaoPagamentoResponse,
    summary="Criar Configuração de Pagamento",
    description="Cria configuração do Mercado Pago para a empresa",
    status_code=201
)
async def criar_configuracao_pagamento(
    data: ConfiguracaoPagamentoCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Cria configuração de pagamento do Mercado Pago.
    
    **Como obter credenciais**:
    1. Acesse: https://www.mercadopago.com.br/developers
    2. Vá em "Suas aplicações" → Criar aplicação
    3. Copie `Access Token` e `Public Key` da aplicação
    
    **Nota**: Cada empresa deve ter sua própria aplicação no Mercado Pago.
    
    **409**: Se já existir configuração (use PUT para atualizar).
    """
    try:
        # Verificar se já existe
        config_existente = await ConfiguracaoPagamentoService.obter_por_empresa(
            db,
            empresa_id
        )
        
        if config_existente:
            raise HTTPException(
                status_code=409,
                detail="Configuração já existe. Use PUT /configuracao para atualizar."
            )
        
        # Criar configuração
        config = await ConfiguracaoPagamentoService.criar(
            db,
            empresa_id=empresa_id,
            mercadopago_access_token=data.mercadopago_access_token,
            mercadopago_public_key=data.mercadopago_public_key,
            ativo=data.ativo
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar configuração: {str(e)}"
        )


@router.put(
    "/configuracao",
    response_model=ConfiguracaoPagamentoResponse,
    summary="Atualizar Configuração de Pagamento",
    description="Atualiza credenciais do Mercado Pago"
)
async def atualizar_configuracao_pagamento(
    data: ConfiguracaoPagamentoUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza configuração de pagamento do Mercado Pago.
    
    **Casos de uso**:
    - Rotação de credenciais (renovação)
    - Ativar/desativar Mercado Pago
    - Trocar para outra aplicação
    
    **404**: Se não houver configuração cadastrada (use POST para criar).
    """
    try:
        # Verificar se existe
        config_existente = await ConfiguracaoPagamentoService.obter_por_empresa(
            db,
            empresa_id
        )
        
        if not config_existente:
            raise HTTPException(
                status_code=404,
                detail="Configuração não encontrada. Use POST /configuracao para criar."
            )
        
        # Atualizar configuração
        config = await ConfiguracaoPagamentoService.atualizar(
            db,
            config_existente.id,
            mercadopago_access_token=data.mercadopago_access_token,
            mercadopago_public_key=data.mercadopago_public_key,
            ativo=data.ativo
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar configuração: {str(e)}"
        )


@router.patch(
    "/configuracao/ativar",
    response_model=ConfiguracaoPagamentoResponse,
    summary="Ativar Configuração de Pagamento",
    description="Ativa configuração do Mercado Pago"
)
async def ativar_configuracao_pagamento(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Ativa configuração de pagamento (ativo=True).
    
    Útil para reativar Mercado Pago sem precisar reenviar credenciais.
    """
    try:
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuração não encontrada"
            )
        
        if config.ativo:
            return config  # Já está ativa
        
        # Ativar
        config = await ConfiguracaoPagamentoService.atualizar(
            db,
            config.id,
            ativo=True
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ativar configuração: {str(e)}"
        )


@router.patch(
    "/configuracao/desativar",
    response_model=ConfiguracaoPagamentoResponse,
    summary="Desativar Configuração de Pagamento",
    description="Desativa configuração do Mercado Pago"
)
async def desativar_configuracao_pagamento(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Desativa configuração de pagamento (ativo=False).
    
    **Efeito**: Clientes não conseguirão usar pagamento online até reativar.
    
    **Casos de uso**:
    - Manutenção temporária
    - Problemas com Mercado Pago
    - Desabilitar pagamento online temporariamente
    """
    try:
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuração não encontrada"
            )
        
        if not config.ativo:
            return config  # Já está desativada
        
        # Desativar
        config = await ConfiguracaoPagamentoService.atualizar(
            db,
            config.id,
            ativo=False
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao desativar configuração: {str(e)}"
        )


@router.delete(
    "/configuracao",
    summary="Deletar Configuração de Pagamento",
    description="Remove configuração do Mercado Pago (irreversível)"
)
async def deletar_configuracao_pagamento(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta configuração de pagamento.
    
    ⚠️ **ATENÇÃO**: Esta ação é irreversível. As credenciais serão deletadas.
    
    **Efeito**: 
    - Clientes não conseguirão usar pagamento online
    - Webhooks do Mercado Pago falharão
    
    **Recomendação**: Use PATCH /desativar para desabilitar temporariamente.
    """
    try:
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuração não encontrada"
            )
        
        # Deletar
        await ConfiguracaoPagamentoService.deletar(db, config.id)
        
        return {"message": "Configuração de pagamento deletada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar configuração: {str(e)}"
        )
