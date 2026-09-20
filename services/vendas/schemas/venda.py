"""
Schemas de Venda.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from models.venda import StatusVenda, TipoEntrega, TipoDesconto, FormaPagamento


# ==================== ITEM VENDA ====================

class ItemVendaBase(BaseModel):
    """Schema base de Item de Venda."""
    produto_id: UUID = Field(..., description="ID do produto")
    variante_id: Optional[UUID] = Field(None, description="ID da variante (opcional)")
    quantidade: Decimal = Field(..., gt=0, description="Quantidade vendida")
    codigo_produto: Optional[str] = Field(None, description="SKU/código de barras do produto")
    descricao_produto: Optional[str] = Field(None, description="Nome/descrição do produto")


class ItemVendaCreate(ItemVendaBase):
    """Schema para criar item de venda.

    Sem preco_unitario de propósito: o preço é o do catálogo, lido no serviço de
    produtos na criação da venda. Quem precisa cobrar menos usa desconto_tipo/
    desconto_valor, que é onde o relatório lê que houve desconto e de quanto — o
    override por item passava por fora deles.

    extra="forbid" para que um payload que ainda mande o campo leve 422: retirá-lo
    do schema sem isto o faria sumir calado, e o pedido seria gravado com um preço
    diferente do que quem chamou pediu.
    """
    model_config = ConfigDict(extra="forbid")


class ItemVendaResponse(BaseModel):
    """Schema de resposta de Item de Venda."""
    id: UUID
    venda_id: UUID
    produto_id: UUID
    variante_id: Optional[UUID]
    codigo_produto: Optional[str]
    descricao_produto: str
    quantidade: Decimal
    preco_unitario: Decimal
    subtotal: Decimal
    estoque_reservado: bool
    estoque_baixado: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== PAGAMENTO VENDA ====================

class PagamentoVendaBase(BaseModel):
    """Schema base de Pagamento de Venda."""
    forma_pagamento: FormaPagamento = Field(..., description="Forma de pagamento")
    valor_pago: Decimal = Field(..., gt=0, description="Valor pago nesta forma")
    valor_recebido: Optional[Decimal] = Field(None, ge=0, description="Valor recebido (apenas DINHEIRO)")
    comprovante: Optional[str] = Field(None, max_length=200, description="Número do comprovante")


class PagamentoVendaCreate(PagamentoVendaBase):
    """Schema para criar pagamento de venda."""
    
    @field_validator('valor_recebido')
    @classmethod
    def validar_valor_recebido(cls, v, info):
        """Valida que valor_recebido só é usado para DINHEIRO."""
        if v is not None and info.data.get('forma_pagamento') != FormaPagamento.DINHEIRO:
            raise ValueError('valor_recebido só pode ser usado para forma_pagamento=DINHEIRO')
        return v


class PagamentoVendaResponse(BaseModel):
    """Schema de resposta de Pagamento de Venda."""
    id: UUID
    venda_id: UUID
    forma_pagamento: FormaPagamento
    valor_pago: Decimal
    valor_recebido: Optional[Decimal]
    valor_troco: Optional[Decimal]
    gera_conta_receber: bool
    conta_receber_id: Optional[UUID]
    comprovante: Optional[str]
    data_pagamento: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== VENDA ====================

class VendaBase(BaseModel):
    """Schema base de Venda."""
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    cliente_id: Optional[UUID] = Field(None, description="ID do cliente (opcional - venda balcão)")
    tipo_entrega: TipoEntrega = Field(TipoEntrega.RETIRADA, description="Tipo de entrega")
    observacao: Optional[str] = Field(None, description="Observações adicionais")


class VendaCreate(VendaBase):
    """Schema para criar venda."""
    itens: List[ItemVendaCreate] = Field(..., min_length=1, description="Itens da venda")
    desconto_tipo: Optional[TipoDesconto] = Field(None, description="Tipo de desconto")
    desconto_valor: Decimal = Field(0.0, ge=0, description="Valor do desconto")
    
    @field_validator('desconto_valor')
    @classmethod
    def validar_desconto(cls, v, info):
        """Valida desconto conforme o tipo."""
        if v > 0 and not info.data.get('desconto_tipo'):
            raise ValueError('desconto_tipo é obrigatório quando desconto_valor > 0')
        
        if info.data.get('desconto_tipo') == TipoDesconto.PERCENTUAL and v > 100:
            raise ValueError('desconto_percentual não pode ser maior que 100%')
        
        return v


class VendaUpdate(BaseModel):
    """Schema para atualizar venda (apenas em status PEDIDO)."""
    cliente_id: Optional[UUID] = None
    tipo_entrega: Optional[TipoEntrega] = None
    observacao: Optional[str] = None
    desconto_tipo: Optional[TipoDesconto] = None
    desconto_valor: Optional[Decimal] = Field(None, ge=0)


class VendaResponse(VendaBase):
    """Schema de resposta de Venda."""
    id: UUID
    numero_venda: str
    subtotal: Decimal
    desconto_tipo: Optional[TipoDesconto]
    desconto_valor: Decimal
    valor_total: Decimal
    status: StatusVenda
    data_pedido: datetime
    data_confirmacao: Optional[datetime]
    data_separacao: Optional[datetime]
    data_entregue: Optional[datetime]
    data_finalizada: Optional[datetime]
    data_cancelada: Optional[datetime]
    motivo_cancelamento: Optional[str]
    cancelada_por: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VendaDetalhada(VendaResponse):
    """Schema de venda com itens e pagamentos."""
    itens: List[ItemVendaResponse] = []
    pagamentos: List[PagamentoVendaResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==================== AÇÕES ====================

class ConfirmarVendaRequest(BaseModel):
    """Schema para confirmar venda."""
    pagamentos: List[PagamentoVendaCreate] = Field(..., min_length=1, description="Formas de pagamento")


class CancelarVendaRequest(BaseModel):
    """Schema para cancelar venda."""
    motivo: str = Field(..., min_length=10, max_length=500, description="Motivo do cancelamento")
    usuario_id: Optional[UUID] = Field(None, description="ID do usuário que cancelou")


class AdicionarPagamentoRequest(BaseModel):
    """Schema para adicionar pagamento adicional."""
    forma_pagamento: FormaPagamento
    valor_pago: Decimal = Field(..., gt=0)
    valor_recebido: Optional[Decimal] = Field(None, ge=0)
    comprovante: Optional[str] = Field(None, max_length=200)


# ==================== RELATÓRIOS ====================

class RelatorioVendas(BaseModel):
    """Schema de relatório de vendas."""
    periodo_inicio: datetime
    periodo_fim: datetime
    total_vendas: int
    valor_total: Decimal
    vendas_finalizadas: int
    vendas_canceladas: int
    ticket_medio: Decimal
    
    # Por forma de pagamento
    total_dinheiro: Decimal = Decimal('0.0')
    total_pix: Decimal = Decimal('0.0')
    total_debito: Decimal = Decimal('0.0')
    total_credito: Decimal = Decimal('0.0')
    total_fiado: Decimal = Decimal('0.0')


class VendaPorCliente(BaseModel):
    """Schema de vendas agrupadas por cliente."""
    cliente_id: UUID
    total_vendas: int
    valor_total: Decimal
    ultima_venda: datetime


class ProdutoMaisVendido(BaseModel):
    """Schema de produtos mais vendidos."""
    produto_id: UUID
    descricao_produto: str
    quantidade_vendida: Decimal
    valor_total: Decimal
    numero_vendas: int
