"""
Schemas para Loja Online (E-commerce).
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, field_validator

from models.venda import TipoEntrega, FormaPagamento


# ==================== CARRINHO ====================

class ItemCarrinhoBase(BaseModel):
    """Schema base de item do carrinho."""
    produto_id: UUID = Field(..., description="ID do produto")
    variante_id: Optional[UUID] = Field(None, description="ID da variante")
    quantidade: Decimal = Field(..., gt=0, description="Quantidade desejada")


class ItemCarrinhoCreate(ItemCarrinhoBase):
    """Schema para adicionar item ao carrinho."""
    pass


class ItemCarrinhoResponse(ItemCarrinhoBase):
    """Schema de resposta de item do carrinho."""
    codigo_produto: Optional[str]
    descricao_produto: str
    preco_unitario: Decimal
    subtotal: Decimal
    estoque_disponivel: bool = True
    
    model_config = {"from_attributes": True}


class CarrinhoResponse(BaseModel):
    """Schema de resposta do carrinho completo."""
    sessao_id: str = Field(..., description="ID da sessão (cookie)")
    empresa_id: int = Field(..., description="ID da empresa")
    itens: List[ItemCarrinhoResponse] = []
    subtotal: Decimal = Decimal('0.0')
    quantidade_itens: int = 0
    criado_em: datetime
    atualizado_em: datetime


class AtualizarQuantidadeRequest(BaseModel):
    """Schema para atualizar quantidade de item no carrinho."""
    quantidade: Decimal = Field(..., gt=0, description="Nova quantidade")


# ==================== CHECKOUT ====================

class EnderecoEntregaCheckout(BaseModel):
    """Schema de endereço de entrega no checkout."""
    logradouro: str = Field(..., min_length=3, max_length=200)
    numero: str = Field(..., max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: str = Field(..., min_length=2, max_length=100)
    cidade: str = Field(..., min_length=2, max_length=100)
    estado: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., pattern=r'^\d{8}$')


class ClienteCheckout(BaseModel):
    """Schema de dados do cliente no checkout (para clientes não cadastrados)."""
    nome: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    telefone: str = Field(..., pattern=r'^\(\d{2}\)\s?\d{4,5}-?\d{4}$')
    cpf: Optional[str] = Field(None, pattern=r'^\d{11}$')


class CheckoutRequest(BaseModel):
    """Schema para processar checkout."""
    # Cliente
    cliente_id: Optional[UUID] = Field(None, description="ID do cliente (se cadastrado)")
    cliente_novo: Optional[ClienteCheckout] = Field(None, description="Dados do cliente (se não cadastrado)")
    
    # Entrega
    tipo_entrega: TipoEntrega = Field(..., description="Tipo de entrega")
    endereco_entrega: Optional[EnderecoEntregaCheckout] = Field(
        None,
        description="Endereço de entrega (obrigatório para DELIVERY)"
    )
    
    # Pagamento (simplificado - apenas forma)
    forma_pagamento: FormaPagamento = Field(..., description="Forma de pagamento")
    
    # Observações
    observacao: Optional[str] = Field(None, max_length=500)
    
    @field_validator('endereco_entrega')
    @classmethod
    def validar_endereco_delivery(cls, v, info):
        """Valida que endereço é obrigatório para DELIVERY."""
        if info.data.get('tipo_entrega') == TipoEntrega.DELIVERY and not v:
            raise ValueError('endereco_entrega é obrigatório para tipo_entrega=DELIVERY')
        return v
    
    @field_validator('cliente_novo')
    @classmethod
    def validar_cliente(cls, v, info):
        """Valida que um dos dois (cliente_id ou cliente_novo) deve ser fornecido."""
        cliente_id = info.data.get('cliente_id')
        if not cliente_id and not v:
            raise ValueError('Forneça cliente_id ou cliente_novo')
        if cliente_id and v:
            raise ValueError('Forneça apenas cliente_id OU cliente_novo, não ambos')
        return v


class CheckoutResponse(BaseModel):
    """Schema de resposta do checkout."""
    venda_id: UUID
    numero_venda: str
    status: str
    valor_total: Decimal
    mensagem: str = "Pedido criado com sucesso! Aguarde confirmação do pagamento."


# ==================== PEDIDOS DO CLIENTE ====================

class PedidoClienteResumido(BaseModel):
    """Schema resumido de pedido para área do cliente."""
    id: UUID
    numero_venda: str
    data_pedido: datetime
    status: str
    valor_total: Decimal
    quantidade_itens: int


class RastreamentoPedido(BaseModel):
    """Schema de rastreamento do pedido."""
    numero_venda: str
    status_atual: str
    data_pedido: datetime
    data_confirmacao: Optional[datetime]
    data_separacao: Optional[datetime]
    data_entregue: Optional[datetime]
    data_finalizada: Optional[datetime]
    data_cancelada: Optional[datetime]
    tipo_entrega: str
    valor_total: Decimal
    
    # Timeline
    historico: List[dict] = []
    
    # Próxima ação esperada
    proxima_etapa: Optional[str] = None
    previsao_entrega: Optional[str] = None


class BuscarPedidoRequest(BaseModel):
    """Schema para buscar pedido por número ou email."""
    numero_venda: Optional[str] = Field(None, description="Número da venda")
    email: Optional[EmailStr] = Field(None, description="Email do cliente")
    
    @field_validator('email')
    @classmethod
    def validar_um_campo_obrigatorio(cls, v, info):
        """Valida que pelo menos um campo foi fornecido."""
        numero_venda = info.data.get('numero_venda')
        if not numero_venda and not v:
            raise ValueError('Forneça numero_venda ou email')
        return v
