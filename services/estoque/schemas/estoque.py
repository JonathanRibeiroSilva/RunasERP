"""
Schemas de Estoque.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from models.estoque import TipoMovimentacao, StatusLote


# ==================== ESTOQUE ====================

class EstoqueBase(BaseModel):
    """Schema base de Estoque."""
    produto_id: UUID = Field(..., description="ID do produto")
    variante_id: Optional[UUID] = Field(None, description="ID da variante (opcional)")
    quantidade: float = Field(0.0, ge=0, description="Quantidade em estoque")
    estoque_minimo: float = Field(0.0, ge=0, description="Estoque mínimo")
    estoque_maximo: Optional[float] = Field(None, ge=0, description="Estoque máximo")
    localizacao: Optional[str] = Field(None, max_length=100, description="Localização física")


class EstoqueCreate(EstoqueBase):
    """Schema para criar estoque."""
    pass


class EstoqueUpdate(BaseModel):
    """Schema para atualizar estoque."""
    estoque_minimo: Optional[float] = Field(None, ge=0)
    estoque_maximo: Optional[float] = Field(None, ge=0)
    localizacao: Optional[str] = Field(None, max_length=100)
    ativo: Optional[bool] = None


class EstoqueResponse(EstoqueBase):
    """Schema de resposta de Estoque."""
    id: UUID
    quantidade_reservada: float
    quantidade_disponivel: float
    ativo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EstoqueComAlerta(EstoqueResponse):
    """Schema de estoque com alertas."""
    alerta_estoque_baixo: bool = Field(..., description="True se estoque está abaixo do mínimo")
    alerta_estoque_zerado: bool = Field(..., description="True se estoque está zerado")


# ==================== MOVIMENTAÇÃO ====================

class MovimentacaoBase(BaseModel):
    """Schema base de Movimentação."""
    tipo: TipoMovimentacao = Field(..., description="Tipo de movimentação")
    quantidade: float = Field(..., gt=0, description="Quantidade movimentada")
    motivo: Optional[str] = Field(None, max_length=200, description="Motivo da movimentação")
    observacao: Optional[str] = Field(None, description="Observações adicionais")
    documento: Optional[str] = Field(None, max_length=100, description="Número do documento")
    custo_unitario: Optional[float] = Field(None, ge=0, description="Custo unitário")


class MovimentacaoCreate(MovimentacaoBase):
    """Schema para criar movimentação."""
    estoque_id: UUID = Field(..., description="ID do estoque")
    lote_id: Optional[UUID] = Field(None, description="ID do lote (opcional)")
    usuario_id: Optional[UUID] = Field(None, description="ID do usuário")


class MovimentacaoResponse(MovimentacaoBase):
    """Schema de resposta de Movimentação."""
    id: UUID
    estoque_id: UUID
    lote_id: Optional[UUID]
    quantidade_anterior: float
    quantidade_posterior: float
    custo_total: Optional[float]
    usuario_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== LOTE ====================

class LoteBase(BaseModel):
    """Schema base de Lote."""
    codigo: str = Field(..., max_length=100, description="Código do lote")
    quantidade: float = Field(..., gt=0, description="Quantidade do lote")
    data_fabricacao: Optional[date] = Field(None, description="Data de fabricação")
    data_validade: Optional[date] = Field(None, description="Data de validade")
    fornecedor: Optional[str] = Field(None, max_length=200, description="Nome do fornecedor")
    nota_fiscal: Optional[str] = Field(None, max_length=100, description="Número da nota fiscal")
    custo_unitario: Optional[float] = Field(None, ge=0, description="Custo unitário")

    @field_validator('data_validade')
    @classmethod
    def validar_data_validade(cls, v, info):
        """Valida que data de validade é posterior à fabricação."""
        if v and info.data.get('data_fabricacao') and v < info.data['data_fabricacao']:
            raise ValueError('Data de validade deve ser posterior à data de fabricação')
        return v


class LoteCreate(LoteBase):
    """Schema para criar lote."""
    estoque_id: UUID = Field(..., description="ID do estoque")


class LoteUpdate(BaseModel):
    """Schema para atualizar lote."""
    quantidade: Optional[float] = Field(None, gt=0)
    status: Optional[StatusLote] = None


class LoteResponse(LoteBase):
    """Schema de resposta de Lote."""
    id: UUID
    estoque_id: UUID
    quantidade_inicial: float
    status: StatusLote
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoteComAlerta(LoteResponse):
    """Schema de lote com alertas."""
    dias_para_vencer: Optional[int] = Field(None, description="Dias até o vencimento")
    alerta_vencimento: bool = Field(..., description="True se está próximo do vencimento")
    vencido: bool = Field(..., description="True se já venceu")


# ==================== INVENTÁRIO ====================

class ItemInventarioBase(BaseModel):
    """Schema base de Item de Inventário."""
    estoque_id: UUID = Field(..., description="ID do estoque")
    quantidade_contada: float = Field(..., ge=0, description="Quantidade contada")
    observacao: Optional[str] = Field(None, description="Observações")


class ItemInventarioCreate(ItemInventarioBase):
    """Schema para criar item de inventário."""
    pass


class ItemInventarioResponse(ItemInventarioBase):
    """Schema de resposta de Item de Inventário."""
    id: UUID
    inventario_id: UUID
    quantidade_sistema: float
    diferenca: float
    ajustado: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InventarioBase(BaseModel):
    """Schema base de Inventário."""
    responsavel: str = Field(..., max_length=200, description="Nome do responsável")
    observacao: Optional[str] = Field(None, description="Observações gerais")


class InventarioCreate(InventarioBase):
    """Schema para criar inventário."""
    itens: List[ItemInventarioCreate] = Field(..., description="Itens do inventário")


class InventarioUpdate(BaseModel):
    """Schema para atualizar inventário."""
    observacao: Optional[str] = None


class InventarioResponse(InventarioBase):
    """Schema de resposta de Inventário."""
    id: UUID
    data_inventario: datetime
    finalizado: bool
    data_finalizacao: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    itens: List[ItemInventarioResponse] = []

    class Config:
        from_attributes = True


# ==================== ENTRADA/SAÍDA ====================

class EntradaEstoqueRequest(BaseModel):
    """Schema para entrada de estoque."""
    produto_id: UUID = Field(..., description="ID do produto")
    variante_id: Optional[UUID] = Field(None, description="ID da variante")
    quantidade: float = Field(..., gt=0, description="Quantidade a adicionar")
    motivo: Optional[str] = Field(None, max_length=200)
    observacao: Optional[str] = None
    documento: Optional[str] = Field(None, max_length=100)
    custo_unitario: Optional[float] = Field(None, ge=0)
    
    # Dados do lote (opcional)
    criar_lote: bool = Field(False, description="Se deve criar um lote")
    codigo_lote: Optional[str] = Field(None, max_length=100)
    data_fabricacao: Optional[date] = None
    data_validade: Optional[date] = None
    fornecedor: Optional[str] = Field(None, max_length=200)
    nota_fiscal: Optional[str] = Field(None, max_length=100)


class SaidaEstoqueRequest(BaseModel):
    """Schema para saída de estoque."""
    produto_id: UUID = Field(..., description="ID do produto")
    variante_id: Optional[UUID] = Field(None, description="ID da variante")
    quantidade: float = Field(..., gt=0, description="Quantidade a remover")
    motivo: Optional[str] = Field(None, max_length=200)
    observacao: Optional[str] = None
    documento: Optional[str] = Field(None, max_length=100)
    lote_id: Optional[UUID] = Field(None, description="ID do lote específico")


class AjusteEstoqueRequest(BaseModel):
    """Schema para ajuste de estoque."""
    estoque_id: UUID = Field(..., description="ID do estoque")
    quantidade_nova: float = Field(..., ge=0, description="Nova quantidade")
    motivo: str = Field(..., max_length=200, description="Motivo do ajuste")
    observacao: Optional[str] = None


class ReservaEstoqueRequest(BaseModel):
    """Schema para reservar estoque."""
    produto_id: UUID = Field(..., description="ID do produto")
    variante_id: Optional[UUID] = Field(None, description="ID da variante")
    quantidade: float = Field(..., gt=0, description="Quantidade a reservar")
    documento: Optional[str] = Field(None, max_length=100, description="Número do pedido/venda")


class LiberarReservaRequest(BaseModel):
    """Schema para liberar reserva de estoque."""
    produto_id: UUID = Field(..., description="ID do produto")
    variante_id: Optional[UUID] = Field(None, description="ID da variante")
    quantidade: float = Field(..., gt=0, description="Quantidade a liberar")
    documento: Optional[str] = Field(None, max_length=100)


# ==================== RELATÓRIOS ====================

class RelatorioEstoque(BaseModel):
    """Schema de relatório de estoque."""
    total_produtos: int
    total_em_estoque: float
    produtos_estoque_baixo: int
    produtos_sem_estoque: int
    valor_total_estoque: Optional[float] = None


class RelatorioMovimentacoes(BaseModel):
    """Schema de relatório de movimentações."""
    periodo_inicio: datetime
    periodo_fim: datetime
    total_entradas: int
    total_saidas: int
    quantidade_entrada: float
    quantidade_saida: float
    valor_total_entradas: Optional[float] = None
    valor_total_saidas: Optional[float] = None
