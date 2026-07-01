"""
Modelos de Venda.
"""
from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Text, Integer, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class StatusVenda(str, Enum):
    """Status do fluxo de venda."""
    PEDIDO = "PEDIDO"
    PENDENTE_PAGAMENTO = "PENDENTE_PAGAMENTO"  # Aguardando pagamento online
    CONFIRMADA = "CONFIRMADA"
    SEPARADA = "SEPARADA"
    EM_ENTREGA = "EM_ENTREGA"  # Apenas para DELIVERY
    ENTREGUE = "ENTREGUE"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"
    REEMBOLSADA = "REEMBOLSADA"  # Devolução/reembolso


class TipoEntrega(str, Enum):
    """Tipo de entrega da venda."""
    RETIRADA = "RETIRADA"
    DELIVERY = "DELIVERY"


class TipoDesconto(str, Enum):
    """Tipo de desconto aplicado."""
    PERCENTUAL = "PERCENTUAL"
    VALOR_FIXO = "VALOR_FIXO"


class FormaPagamento(str, Enum):
    """Formas de pagamento aceitas."""
    DINHEIRO = "DINHEIRO"
    PIX = "PIX"
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"
    FIADO = "FIADO"


class StatusReserva(str, Enum):
    """Status da reserva de estoque."""
    RESERVADA = "RESERVADA"
    BAIXADA = "BAIXADA"
    LIBERADA = "LIBERADA"


class Venda(Base):
    """
    Modelo de Venda.
    Controla o pedido de venda completo com workflow de status.
    """
    __tablename__ = "vendas"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'numero_venda', name='uq_vendas_empresa_numero'),
        Index('ix_vendas_empresa_id', 'empresa_id'),
        Index('ix_vendas_empresa_id_status', 'empresa_id', 'status'),
        Index('ix_vendas_empresa_id_cliente', 'empresa_id', 'cliente_id'),
        Index('ix_vendas_empresa_id_data', 'empresa_id', 'data_pedido'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenancy
    empresa_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="ID da empresa (multi-tenancy)"
    )
    
    # Identificação
    numero_venda = Column(String(50), nullable=False, index=True)  # Ex: "V-2026-00001"
    
    # Cliente (nullable - venda balcão sem identificação)
    cliente_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Valores
    subtotal = Column(Numeric(10, 2), nullable=False, default=0.0)
    desconto_tipo = Column(String(20), nullable=True)  # TipoDesconto
    desconto_valor = Column(Numeric(10, 2), nullable=False, default=0.0)
    valor_total = Column(Numeric(10, 2), nullable=False, default=0.0)
    
    # Workflow
    status = Column(String(20), nullable=False, default=StatusVenda.PEDIDO.value, index=True)
    tipo_entrega = Column(String(20), nullable=False, default=TipoEntrega.RETIRADA.value)
    
    # Mercado Pago (para pagamentos online)
    mercadopago_preference_id = Column(String(100), nullable=True, index=True)
    mercadopago_payment_id = Column(String(100), nullable=True, index=True)
    
    # Sessão do carrinho (para limpar após pagamento confirmado)
    sessao_carrinho_id = Column(String(100), nullable=True, comment="ID da sessão do carrinho Redis")
    
    # Valor do frete (taxa de entrega)
    valor_frete = Column(Numeric(10, 2), nullable=False, default=0.0)
    
    # Dados do cliente convidado (se cliente_id for NULL)
    cliente_convidado_nome = Column(String(200), nullable=True)
    cliente_convidado_telefone = Column(String(20), nullable=True)
    cliente_convidado_email = Column(String(200), nullable=True)
    cliente_convidado_cpf = Column(String(11), nullable=True)
    
    # Endereço de entrega (para DELIVERY)
    endereco_logradouro = Column(String(200), nullable=True)
    endereco_numero = Column(String(20), nullable=True)
    endereco_complemento = Column(String(100), nullable=True)
    endereco_bairro = Column(String(100), nullable=True)
    endereco_cidade = Column(String(100), nullable=True)
    endereco_estado = Column(String(2), nullable=True)
    endereco_cep = Column(String(8), nullable=True)
    
    # Datas do workflow
    data_pedido = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_confirmacao = Column(DateTime, nullable=True)
    data_separacao = Column(DateTime, nullable=True)
    data_entregue = Column(DateTime, nullable=True)
    data_finalizada = Column(DateTime, nullable=True)
    data_cancelada = Column(DateTime, nullable=True)
    
    # Cancelamento
    motivo_cancelamento = Column(Text, nullable=True)
    cancelada_por = Column(UUID(as_uuid=True), nullable=True)  # usuario_id

    # Reconciliação cross-service (C4): pagamento aprovado mas resultado da baixa de
    # estoque indeterminado (timeout/erro). A venda NÃO é cancelada; um job retenta a
    # baixa idempotente e confirma (ou cancela se faltar estoque de fato).
    reconciliacao_estoque_pendente = Column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    reconciliacao_motivo = Column(Text, nullable=True)
    
    # Observações
    observacao = Column(Text, nullable=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")
    pagamentos = relationship("PagamentoVenda", back_populates="venda", cascade="all, delete-orphan")
    reservas = relationship("ReservaEstoqueVenda", back_populates="venda", cascade="all, delete-orphan")


class ItemVenda(Base):
    """
    Modelo de Item de Venda.
    Representa cada produto vendido.
    Snapshot dos dados do produto no momento da venda.
    """
    __tablename__ = "itens_venda"
    __table_args__ = (
        Index('ix_itens_venda_venda_id', 'venda_id'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    venda_id = Column(UUID(as_uuid=True), ForeignKey("vendas.vendas.id"), nullable=False, index=True)
    
    # Produto (snapshot - preserva dados mesmo se produto mudar)
    produto_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    variante_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    codigo_produto = Column(String(100), nullable=True)  # SKU/código de barras
    descricao_produto = Column(String(500), nullable=False)  # Nome do produto
    
    # Quantidades e Valores
    quantidade = Column(Numeric(10, 3), nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)  # quantidade * preco_unitario
    
    # Controle de Estoque
    estoque_reservado = Column(Boolean, default=False, nullable=False)
    estoque_baixado = Column(Boolean, default=False, nullable=False)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    venda = relationship("Venda", back_populates="itens")


class PagamentoVenda(Base):
    """
    Modelo de Pagamento de Venda.
    Uma venda pode ter múltiplas formas de pagamento.
    """
    __tablename__ = "pagamentos_venda"
    __table_args__ = (
        Index('ix_pagamentos_venda_venda_id', 'venda_id'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    venda_id = Column(UUID(as_uuid=True), ForeignKey("vendas.vendas.id"), nullable=False, index=True)
    
    # Forma de Pagamento
    forma_pagamento = Column(String(20), nullable=False, index=True)  # FormaPagamento
    valor_pago = Column(Numeric(10, 2), nullable=False)
    
    # Troco (apenas para DINHEIRO)
    valor_recebido = Column(Numeric(10, 2), nullable=True)
    valor_troco = Column(Numeric(10, 2), nullable=True)
    
    # Integração Financeiro (se FIADO)
    gera_conta_receber = Column(Boolean, default=False, nullable=False)
    conta_receber_id = Column(UUID(as_uuid=True), nullable=True)  # Criada ao finalizar
    
    # Comprovante
    comprovante = Column(String(200), nullable=True)  # Número transação PIX/cartão
    
    # Auditoria
    data_pagamento = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    venda = relationship("Venda", back_populates="pagamentos")


class ReservaEstoqueVenda(Base):
    """
    Modelo de Reserva de Estoque para Venda.
    Controla a reserva e baixa de estoque durante o workflow.
    """
    __tablename__ = "reservas_estoque_venda"
    __table_args__ = (
        Index('ix_reservas_venda_id', 'venda_id'),
        Index('ix_reservas_produto', 'produto_id', 'variante_id'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    venda_id = Column(UUID(as_uuid=True), ForeignKey("vendas.vendas.id"), nullable=False, index=True)
    item_venda_id = Column(UUID(as_uuid=True), ForeignKey("vendas.itens_venda.id"), nullable=False, index=True)
    
    # Produto
    produto_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    variante_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Quantidade
    quantidade_reservada = Column(Numeric(10, 3), nullable=False)
    
    # Datas
    reservada_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    liberada_em = Column(DateTime, nullable=True)  # Se cancelar
    baixada_em = Column(DateTime, nullable=True)  # Se confirmar entrega
    
    # Status
    status = Column(String(20), nullable=False, default=StatusReserva.RESERVADA.value, index=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    venda = relationship("Venda", back_populates="reservas")


class ReservaTemporaria(Base):
    """
    Modelo de Reserva Temporária de Estoque (Carrinho).
    Reserva estoque quando item é adicionado ao carrinho (15min).
    """
    __tablename__ = "reservas_temporarias"
    __table_args__ = (
        Index('ix_reservas_temp_produto', 'produto_id', 'variante_id'),
        Index('ix_reservas_temp_sessao', 'sessao_id'),
        Index('ix_reservas_temp_expira', 'expira_em'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Produto
    produto_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    variante_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Quantidade reservada
    quantidade = Column(Numeric(10, 3), nullable=False)
    
    # Sessão do carrinho
    sessao_id = Column(String(255), nullable=False, index=True)
    empresa_id = Column(Integer, nullable=False, index=True)
    
    # Controle de expiração
    expira_em = Column(DateTime, nullable=False, index=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WebhookProcessado(Base):
    """
    Modelo para controle de idempotência de webhooks (Mercado Pago).
    Garante que webhook não seja processado duas vezes.
    """
    __tablename__ = "webhooks_processados"
    __table_args__ = (
        Index('ix_webhooks_payment_id', 'payment_id'),
        Index('ix_webhooks_tipo', 'tipo_evento'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Payment ID do Mercado Pago (único)
    payment_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Tipo de evento
    tipo_evento = Column(String(50), nullable=False, index=True)  # payment.approved, etc.
    
    # Venda associada
    venda_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Payload completo (para auditoria)
    payload = Column(Text, nullable=True)
    
    # Auditoria
    processado_em = Column(DateTime, default=datetime.utcnow, nullable=False)


class ConfiguracaoPagamento(Base):
    """
    Modelo de Configuração de Pagamento (Mercado Pago) por empresa.
    Multi-tenant: cada empresa tem suas próprias credenciais.
    """
    __tablename__ = "configuracoes_pagamento"
    __table_args__ = (
        Index('ix_config_pag_empresa', 'empresa_id'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenancy
    empresa_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Credenciais Mercado Pago
    mercadopago_access_token = Column(String(255), nullable=True)
    mercadopago_public_key = Column(String(255), nullable=True)
    
    # Status
    ativo = Column(Boolean, default=True, nullable=False)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FaixaEntrega(Base):
    """
    Modelo de Faixa de Entrega (taxa por bairro).
    Permite configurar taxa diferente por bairro.
    """
    __tablename__ = "faixas_entrega"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'bairro', name='uq_faixa_empresa_bairro'),
        Index('ix_faixa_empresa', 'empresa_id'),
        Index('ix_faixa_bairro', 'bairro'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenancy
    empresa_id = Column(Integer, nullable=False, index=True)
    
    # Bairro (extraído do CEP via ViaCEP)
    bairro = Column(String(100), nullable=False, index=True)
    
    # Taxa de entrega
    taxa = Column(Numeric(10, 2), nullable=False)
    
    # Status
    ativo = Column(Boolean, default=True, nullable=False)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ConfiguracaoLoja(Base):
    """
    Modelo de Configuração da Loja (taxa padrão de entrega, etc).
    """
    __tablename__ = "configuracoes_loja"
    __table_args__ = (
        Index('ix_config_loja_empresa', 'empresa_id'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenancy
    empresa_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Taxa de entrega padrão
    taxa_entrega_padrao = Column(Numeric(10, 2), nullable=False, default=0.0)
    
    # Cobrar taxa de entrega
    cobrar_taxa_entrega = Column(Boolean, default=True, nullable=False)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class HistoricoStatusVenda(Base):
    """
    Modelo de Histórico de Status da Venda.
    Registra todas as mudanças de status para auditoria e rastreamento.
    """
    __tablename__ = "historico_status_venda"
    __table_args__ = (
        Index('ix_historico_venda', 'venda_id'),
        Index('ix_historico_data', 'alterado_em'),
        {"schema": "vendas"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Venda
    venda_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Status
    status_anterior = Column(String(20), nullable=True)
    status_novo = Column(String(20), nullable=False)
    
    # Quem alterou (NULL = sistema automático)
    alterado_por = Column(UUID(as_uuid=True), nullable=True)
    
    # Observação (ex: motivo do cancelamento)
    observacao = Column(Text, nullable=True)
    
    # Auditoria
    alterado_em = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
