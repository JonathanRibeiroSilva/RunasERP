"""
Routers de Vendas.
"""
from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from utils.tenant import get_empresa_id
from schemas.venda import (
    VendaCreate,
    VendaUpdate,
    VendaResponse,
    VendaDetalhada,
    ConfirmarVendaRequest,
    CancelarVendaRequest,
    AdicionarPagamentoRequest,
    PagamentoVendaResponse
)
from services.venda_service import EstoqueIndeterminadoError, VendaService
from repositories.venda_repository import PagamentoVendaRepository
from models.venda import StatusVenda, FormaPagamento

router = APIRouter(prefix="/vendas", tags=["Vendas"])


# ==================== VENDA ====================

@router.post("", response_model=VendaDetalhada, status_code=status.HTTP_201_CREATED)
async def criar_venda(
    data: VendaCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova venda.
    
    - Status inicial: PEDIDO
    - Reserva estoque automaticamente
    - Valida produtos e cliente (se fornecido)
    """
    # Validar que empresa_id do body corresponde ao header
    if data.empresa_id != empresa_id:
        raise HTTPException(
            status_code=403,
            detail="empresa_id do body não corresponde ao header X-Empresa-Id"
        )
    
    try:
        return await VendaService.criar_venda(db, empresa_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=dict)
async def listar_vendas(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filtro: Optional[StatusVenda] = Query(None, description="Filtrar por status"),
    cliente_id: Optional[UUID] = Query(None, description="Filtrar por cliente"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data final"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista vendas com filtros opcionais.
    
    Filtros disponíveis:
    - status: PEDIDO, CONFIRMADA, SEPARADA, ENTREGUE, FINALIZADA, CANCELADA
    - cliente_id: Vendas de um cliente específico
    - data_inicio/data_fim: Período de vendas
    """
    vendas, total = await VendaService.listar_vendas(
        db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        status=status_filtro,
        cliente_id=cliente_id,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": vendas
    }


@router.get("/{venda_id}", response_model=VendaDetalhada)
async def buscar_venda(
    venda_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """Busca venda por ID com itens e pagamentos."""
    venda = await VendaService.buscar_venda(db, empresa_id, venda_id)
    if not venda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
    return venda


@router.put("/{venda_id}", response_model=VendaDetalhada)
async def atualizar_venda(
    venda_id: UUID,
    data: VendaUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza venda (apenas se status=PEDIDO).
    
    Campos editáveis:
    - cliente_id
    - tipo_entrega
    - observacao
    - desconto
    """
    try:
        venda = await VendaService.atualizar_venda(db, empresa_id, venda_id, data)
        if not venda:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
        return venda
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== WORKFLOW ====================

@router.post("/{venda_id}/confirmar", response_model=VendaDetalhada)
async def confirmar_venda(
    venda_id: UUID,
    data: ConfirmarVendaRequest,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Confirma venda e registra pagamentos.
    
    Transição: PEDIDO → CONFIRMADA
    
    Validações:
    - Soma dos pagamentos >= valor total
    - Se FIADO: cliente deve estar identificado
    - Calcula troco automaticamente para DINHEIRO
    """
    try:
        return await VendaService.confirmar_venda(db, empresa_id, venda_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{venda_id}/separar", response_model=VendaDetalhada)
async def separar_venda(
    venda_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Marca venda como separada (produtos separados para entrega/retirada).
    
    Transição: CONFIRMADA → SEPARADA
    """
    try:
        return await VendaService.separar_venda(db, empresa_id, venda_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{venda_id}/entregar", response_model=VendaDetalhada)
async def entregar_venda(
    venda_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Marca venda como entregue e BAIXA ESTOQUE definitivamente.
    
    Transição: SEPARADA → ENTREGUE
    
    Ações:
    - Baixa estoque no serviço de Estoque
    - Libera reservas (já foram baixadas)
    - Marca itens como estoque_baixado=True
    """
    try:
        return await VendaService.entregar_venda(db, empresa_id, venda_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{venda_id}/finalizar", response_model=VendaDetalhada)
async def finalizar_venda(
    venda_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Finaliza venda.
    
    Transição: ENTREGUE → FINALIZADA
    
    Ações:
    - Se tem pagamento FIADO: cria conta a receber no Financeiro (futuro)
    - Fecha o ciclo da venda
    """
    try:
        return await VendaService.finalizar_venda(db, empresa_id, venda_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{venda_id}/cancelar", response_model=VendaDetalhada)
async def cancelar_venda(
    venda_id: UUID,
    data: CancelarVendaRequest,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Cancela venda e LIBERA RESERVAS de estoque.
    
    Permitido apenas em: PEDIDO, CONFIRMADA, SEPARADA
    
    Para vendas ENTREGUE ou FINALIZADA, use devolução.
    
    Ações:
    - Libera reservas de estoque
    - Marca reservas como LIBERADA
    - Registra motivo e usuário que cancelou
    """
    try:
        return await VendaService.cancelar_venda(db, empresa_id, venda_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EstoqueIndeterminadoError as e:
        # Nada foi cancelado e o estorno é idempotente: é seguro repetir. 503, não
        # 400 — o pedido estava certo, o estoque é que não respondeu.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cancelamento não concluído: {e}. Tente novamente.",
        )


# ==================== PAGAMENTOS ====================

@router.get("/{venda_id}/pagamentos", response_model=List[PagamentoVendaResponse])
async def listar_pagamentos(
    venda_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """Lista pagamentos de uma venda."""
    # Verificar se venda pertence à empresa
    venda = await VendaService.buscar_venda(db, empresa_id, venda_id)
    if not venda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
    
    pagamentos = await PagamentoVendaRepository.listar_por_venda(db, venda_id)
    return [PagamentoVendaResponse.model_validate(p) for p in pagamentos]


@router.post("/{venda_id}/pagamentos", response_model=PagamentoVendaResponse, status_code=status.HTTP_201_CREATED)
async def adicionar_pagamento(
    venda_id: UUID,
    data: AdicionarPagamentoRequest,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    db: AsyncSession = Depends(get_db)
):
    """
    Adiciona um pagamento adicional à venda.
    
    Útil para vendas com múltiplas formas de pagamento.
    
    Validações:
    - Venda não pode estar CANCELADA ou FINALIZADA
    - Se DINHEIRO: calcula troco automaticamente
    - Se FIADO: cliente deve estar identificado
    """
    try:
        # Verificar se venda existe e pertence à empresa
        venda = await VendaService.buscar_venda(db, empresa_id, venda_id)
        if not venda:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
        
        # Validar status
        if venda.status in [StatusVenda.CANCELADA.value, StatusVenda.FINALIZADA.value]:
            raise ValueError(f"Não é possível adicionar pagamento. Status atual: {venda.status}")
        
        # Validar FIADO
        if data.forma_pagamento == FormaPagamento.FIADO and not venda.cliente_id:
            raise ValueError("Pagamento FIADO requer cliente identificado")
        
        # Criar pagamento
        pag_data = {
            'venda_id': venda_id,
            'forma_pagamento': data.forma_pagamento.value,
            'valor_pago': data.valor_pago,
            'comprovante': data.comprovante,
            'gera_conta_receber': data.forma_pagamento == FormaPagamento.FIADO
        }
        
        # Calcular troco se DINHEIRO
        if data.forma_pagamento == FormaPagamento.DINHEIRO and data.valor_recebido:
            pag_data['valor_recebido'] = data.valor_recebido
            pag_data['valor_troco'] = data.valor_recebido - data.valor_pago
        
        pagamento = await PagamentoVendaRepository.criar(db, **pag_data)
        await db.commit()
        
        return PagamentoVendaResponse.model_validate(pagamento)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== RELATÓRIOS ====================

@router.get("/relatorios/resumo", response_model=dict)
async def relatorio_resumo(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    data_inicio: datetime = Query(..., description="Data inicial"),
    data_fim: datetime = Query(..., description="Data final"),
    db: AsyncSession = Depends(get_db)
):
    """
    Relatório resumido de vendas no período.
    
    Retorna:
    - Total de vendas
    - Valor total
    - Vendas por status
    - Ticket médio
    """
    vendas, total = await VendaService.listar_vendas(
        db,
        empresa_id=empresa_id,
        skip=0,
        limit=10000,  # Buscar todas
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    if not vendas:
        return {
            "periodo_inicio": data_inicio,
            "periodo_fim": data_fim,
            "total_vendas": 0,
            "valor_total": 0.0,
            "ticket_medio": 0.0,
            "por_status": {}
        }
    
    # Calcular métricas
    valor_total = sum(float(v.valor_total) for v in vendas)
    ticket_medio = valor_total / len(vendas) if vendas else 0
    
    # Agrupar por status
    por_status = {}
    for venda in vendas:
        status_key = venda.status.value if hasattr(venda.status, 'value') else venda.status
        if status_key not in por_status:
            por_status[status_key] = {"count": 0, "valor": 0.0}
        por_status[status_key]["count"] += 1
        por_status[status_key]["valor"] += float(venda.valor_total)
    
    return {
        "periodo_inicio": data_inicio,
        "periodo_fim": data_fim,
        "total_vendas": len(vendas),
        "valor_total": valor_total,
        "ticket_medio": ticket_medio,
        "por_status": por_status
    }
