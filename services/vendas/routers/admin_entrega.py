"""
Router Administrativo - Configuração de Entrega.
Endpoints para gerenciar taxa de entrega e exceções por bairro.
"""
from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from decimal import Decimal

from database import get_db
from utils.tenant import get_empresa_id
from services.entrega_service import EntregaService

router = APIRouter(prefix="/admin/entrega", tags=["admin-entrega"])


# ==================== SCHEMAS ====================

class ConfiguracaoLojaResponse(BaseModel):
    """Schema de resposta da configuração da loja."""
    id: UUID
    empresa_id: int
    taxa_entrega_padrao: Decimal
    cobrar_taxa_entrega: bool
    
    model_config = {"from_attributes": True}


class ConfiguracaoLojaUpdate(BaseModel):
    """Schema para atualizar configuração da loja."""
    taxa_entrega_padrao: Decimal = Field(..., ge=0, description="Taxa de entrega padrão (R$)")
    cobrar_taxa_entrega: bool = Field(default=True, description="Cobrar taxa de entrega?")


class FaixaEntregaCreate(BaseModel):
    """Schema para criar faixa de entrega."""
    bairro: str = Field(..., min_length=2, max_length=100, description="Nome do bairro")
    taxa: Decimal = Field(..., ge=0, description="Taxa de entrega para este bairro (R$)")
    ativo: bool = Field(default=True, description="Faixa ativa?")


class FaixaEntregaUpdate(BaseModel):
    """Schema para atualizar faixa de entrega."""
    taxa: Decimal = Field(..., ge=0, description="Nova taxa de entrega (R$)")
    ativo: bool = Field(default=True, description="Faixa ativa?")


class FaixaEntregaResponse(BaseModel):
    """Schema de resposta de faixa de entrega."""
    id: UUID
    empresa_id: int
    bairro: str
    taxa: Decimal
    ativo: bool
    
    model_config = {"from_attributes": True}


# ==================== CONFIGURAÇÃO DA LOJA ====================

@router.get(
    "/configuracao",
    response_model=ConfiguracaoLojaResponse,
    summary="Obter Configuração da Loja",
    description="Obtém configuração de entrega da empresa (taxa padrão)"
)
async def obter_configuracao_loja(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém configuração de entrega da loja.
    
    Se não existir, cria com valores padrão:
    - taxa_entrega_padrao: R$ 0,00
    - cobrar_taxa_entrega: True
    """
    try:
        config = await EntregaService.obter_config_loja(db, empresa_id)
        return config
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter configuração: {str(e)}"
        )


@router.put(
    "/configuracao",
    response_model=ConfiguracaoLojaResponse,
    summary="Atualizar Configuração da Loja",
    description="Atualiza taxa de entrega padrão e configurações"
)
async def atualizar_configuracao_loja(
    data: ConfiguracaoLojaUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza configuração de entrega da loja.
    
    **Campos**:
    - `taxa_entrega_padrao`: Taxa padrão quando não há exceção de bairro
    - `cobrar_taxa_entrega`: Se False, não cobra taxa (todas entregas grátis)
    """
    try:
        # Obter config existente
        config = await EntregaService.obter_config_loja(db, empresa_id)
        
        # Atualizar
        from repositories.venda_repository import ConfiguracaoLojaRepository
        
        config = await ConfiguracaoLojaRepository.atualizar(
            db,
            config.id,
            taxa_entrega_padrao=data.taxa_entrega_padrao,
            cobrar_taxa_entrega=data.cobrar_taxa_entrega
        )
        
        await db.commit()
        
        return config
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar configuração: {str(e)}"
        )


# ==================== FAIXAS DE ENTREGA (EXCEÇÕES POR BAIRRO) ====================

@router.get(
    "/faixas",
    response_model=List[FaixaEntregaResponse],
    summary="Listar Faixas de Entrega",
    description="Lista todas as exceções de taxa por bairro"
)
async def listar_faixas_entrega(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    apenas_ativas: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista faixas de entrega (exceções por bairro).
    
    **Query Params**:
    - `apenas_ativas`: Se True, retorna apenas faixas ativas
    """
    try:
        from repositories.venda_repository import FaixaEntregaRepository
        
        faixas = await FaixaEntregaRepository.listar(
            db,
            empresa_id,
            apenas_ativas=apenas_ativas
        )
        
        return faixas
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar faixas: {str(e)}"
        )


@router.post(
    "/faixas",
    response_model=FaixaEntregaResponse,
    summary="Criar Faixa de Entrega",
    description="Cria exceção de taxa para um bairro específico",
    status_code=201
)
async def criar_faixa_entrega(
    data: FaixaEntregaCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Cria faixa de entrega para um bairro específico.
    
    **Exemplo**: Se a taxa padrão é R$ 5,00, mas no "Centro" cobra R$ 3,00,
    cria uma faixa com bairro="Centro" e taxa=3.00.
    
    **Nota**: O nome do bairro deve corresponder ao retornado pela API ViaCEP.
    """
    try:
        from repositories.venda_repository import FaixaEntregaRepository
        
        # Verificar se já existe faixa para este bairro
        faixa_existente = await EntregaService.obter_faixa_por_bairro(
            db,
            empresa_id,
            data.bairro
        )
        
        if faixa_existente:
            raise HTTPException(
                status_code=409,
                detail=f"Já existe uma faixa de entrega para o bairro '{data.bairro}'"
            )
        
        # Criar faixa
        faixa = await FaixaEntregaRepository.criar(
            db,
            empresa_id=empresa_id,
            bairro=data.bairro,
            taxa=data.taxa,
            ativo=data.ativo
        )
        
        await db.commit()
        
        return faixa
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar faixa: {str(e)}"
        )


@router.get(
    "/faixas/{faixa_id}",
    response_model=FaixaEntregaResponse,
    summary="Obter Faixa de Entrega",
    description="Obtém detalhes de uma faixa específica"
)
async def obter_faixa_entrega(
    faixa_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém faixa de entrega por ID.
    """
    try:
        from repositories.venda_repository import FaixaEntregaRepository
        
        faixa = await FaixaEntregaRepository.buscar_por_id(db, faixa_id)
        
        if not faixa or faixa.empresa_id != empresa_id:
            raise HTTPException(
                status_code=404,
                detail="Faixa de entrega não encontrada"
            )
        
        return faixa
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter faixa: {str(e)}"
        )


@router.put(
    "/faixas/{faixa_id}",
    response_model=FaixaEntregaResponse,
    summary="Atualizar Faixa de Entrega",
    description="Atualiza taxa ou ativa/desativa faixa"
)
async def atualizar_faixa_entrega(
    faixa_id: UUID,
    data: FaixaEntregaUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza faixa de entrega.
    
    **Campos**:
    - `taxa`: Nova taxa de entrega
    - `ativo`: Ativar/desativar faixa (se desativar, usa taxa padrão)
    """
    try:
        from repositories.venda_repository import FaixaEntregaRepository
        
        # Verificar se existe
        faixa = await FaixaEntregaRepository.buscar_por_id(db, faixa_id)
        
        if not faixa or faixa.empresa_id != empresa_id:
            raise HTTPException(
                status_code=404,
                detail="Faixa de entrega não encontrada"
            )
        
        # Atualizar
        faixa = await FaixaEntregaRepository.atualizar(
            db,
            faixa_id,
            taxa=data.taxa,
            ativo=data.ativo
        )
        
        await db.commit()
        
        return faixa
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar faixa: {str(e)}"
        )


@router.delete(
    "/faixas/{faixa_id}",
    summary="Deletar Faixa de Entrega",
    description="Remove exceção de taxa para bairro"
)
async def deletar_faixa_entrega(
    faixa_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta faixa de entrega.
    
    Após deletar, o bairro volta a usar a taxa padrão.
    """
    try:
        from repositories.venda_repository import FaixaEntregaRepository
        
        # Verificar se existe
        faixa = await FaixaEntregaRepository.buscar_por_id(db, faixa_id)
        
        if not faixa or faixa.empresa_id != empresa_id:
            raise HTTPException(
                status_code=404,
                detail="Faixa de entrega não encontrada"
            )
        
        # Deletar
        await FaixaEntregaRepository.deletar(db, faixa_id)
        await db.commit()
        
        return {"message": "Faixa de entrega deletada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar faixa: {str(e)}"
        )


# ==================== SIMULAR CÁLCULO ====================

@router.get(
    "/simular/{cep}",
    summary="Simular Taxa de Entrega",
    description="Simula cálculo de taxa para um CEP (útil para teste)"
)
async def simular_taxa_entrega(
    cep: str,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Simula cálculo de taxa de entrega para um CEP.
    
    Retorna:
    - CEP validado
    - Bairro (via ViaCEP)
    - Taxa calculada
    - Se usou exceção ou taxa padrão
    """
    try:
        # Validar CEP
        cep_validado = await EntregaService.validar_cep(cep)
        
        if not cep_validado:
            raise HTTPException(
                status_code=400,
                detail="CEP inválido ou não encontrado"
            )
        
        # Calcular taxa
        taxa = await EntregaService.calcular_taxa_entrega(
            db,
            empresa_id,
            cep_validado['cep'],
            cep_validado['bairro']
        )
        
        # Verificar se tem exceção
        faixa = await EntregaService.obter_faixa_por_bairro(
            db,
            empresa_id,
            cep_validado['bairro']
        )
        
        return {
            "cep": cep_validado['cep'],
            "logradouro": cep_validado.get('logradouro'),
            "bairro": cep_validado['bairro'],
            "cidade": cep_validado['cidade'],
            "estado": cep_validado['estado'],
            "taxa_calculada": taxa,
            "tipo": "excecao" if faixa and faixa.ativo else "padrao"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao simular taxa: {str(e)}"
        )
