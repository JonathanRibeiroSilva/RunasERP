"""
Modelos de Estoque.
"""
from datetime import datetime, date
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, String, Float, Boolean, DateTime, Date, ForeignKey, Text, Integer, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class TipoMovimentacao(str, Enum):
    """Tipos de movimentação de estoque."""
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"
    DEVOLUCAO = "DEVOLUCAO"
    PERDA = "PERDA"
    TRANSFERENCIA = "TRANSFERENCIA"


class StatusLote(str, Enum):
    """Status do lote."""
    ATIVO = "ATIVO"
    VENCIDO = "VENCIDO"
    BLOQUEADO = "BLOQUEADO"


class Estoque(Base):
    """
    Modelo de Estoque.
    Controla a quantidade disponível de cada produto/variante.
    """
    __tablename__ = "estoque"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'produto_id', 'variante_id', name='uq_estoque_empresa_produto_variante'),
        Index('ix_estoque_empresa_id', 'empresa_id'),
        Index('ix_estoque_empresa_id_ativo', 'empresa_id', 'ativo'),
        {"schema": "estoque"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenancy
    empresa_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="ID da empresa (multi-tenancy)"
    )
    
    produto_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    variante_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    quantidade = Column(Float, nullable=False, default=0.0)
    quantidade_reservada = Column(Float, nullable=False, default=0.0)
    quantidade_disponivel = Column(Float, nullable=False, default=0.0)
    
    estoque_minimo = Column(Float, nullable=False, default=0.0)
    estoque_maximo = Column(Float, nullable=True)
    
    localizacao = Column(String(100), nullable=True)  # Ex: "Prateleira A1"
    
    ativo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    movimentacoes = relationship("Movimentacao", back_populates="estoque", cascade="all, delete-orphan")
    lotes = relationship("Lote", back_populates="estoque", cascade="all, delete-orphan")


class Movimentacao(Base):
    """
    Modelo de Movimentação de Estoque.
    Registra todas as entradas e saídas de estoque.
    """
    __tablename__ = "movimentacoes"
    __table_args__ = {"schema": "estoque"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    estoque_id = Column(UUID(as_uuid=True), ForeignKey("estoque.estoque.id"), nullable=False, index=True)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("estoque.lotes.id"), nullable=True, index=True)
    
    tipo = Column(String(20), nullable=False, index=True)  # TipoMovimentacao
    quantidade = Column(Float, nullable=False)
    quantidade_anterior = Column(Float, nullable=False)
    quantidade_posterior = Column(Float, nullable=False)
    
    motivo = Column(String(200), nullable=True)
    observacao = Column(Text, nullable=True)
    
    documento = Column(String(100), nullable=True)  # Número da NF, pedido, etc.
    usuario_id = Column(UUID(as_uuid=True), nullable=True)  # ID do usuário que fez a movimentação
    
    custo_unitario = Column(Float, nullable=True)
    custo_total = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relacionamentos
    estoque = relationship("Estoque", back_populates="movimentacoes")
    lote = relationship("Lote", back_populates="movimentacoes")


class Lote(Base):
    """
    Modelo de Lote.
    Controla lotes de produtos com data de validade.
    """
    __tablename__ = "lotes"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'codigo', name='uq_lotes_empresa_codigo'),
        Index('ix_lotes_empresa_id', 'empresa_id'),
        {"schema": "estoque"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenancy
    empresa_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="ID da empresa (multi-tenancy)"
    )
    
    estoque_id = Column(UUID(as_uuid=True), ForeignKey("estoque.estoque.id"), nullable=False, index=True)
    
    codigo = Column(String(100), nullable=False, index=True)
    quantidade = Column(Float, nullable=False, default=0.0)
    quantidade_inicial = Column(Float, nullable=False)
    
    data_fabricacao = Column(Date, nullable=True)
    data_validade = Column(Date, nullable=True, index=True)
    
    fornecedor = Column(String(200), nullable=True)
    nota_fiscal = Column(String(100), nullable=True)
    
    custo_unitario = Column(Float, nullable=True)
    
    status = Column(String(20), nullable=False, default=StatusLote.ATIVO.value, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    estoque = relationship("Estoque", back_populates="lotes")
    movimentacoes = relationship("Movimentacao", back_populates="lote")


class BaixaVendaProcessada(Base):
    """
    Ledger de idempotência da baixa de estoque por venda.

    Garante que a dedução de estoque de uma venda execute EXATAMENTE UMA VEZ. A unique
    constraint (empresa_id, documento) é o gate de idempotência sob concorrência: webhooks
    duplicados/reentregues do Mercado Pago, retries e múltiplas instâncias da API tentando
    baixar a mesma venda colidem no índice único e não duplicam a movimentação.

    documento == numero_venda (chave de idempotência fornecida pelo serviço de vendas).
    """
    __tablename__ = "baixas_venda_processadas"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'documento', name='uq_baixa_venda_empresa_documento'),
        Index('ix_baixa_venda_empresa_documento', 'empresa_id', 'documento'),
        {"schema": "estoque"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Multi-tenancy
    empresa_id = Column(Integer, nullable=False, index=True)

    # Número da venda (chave de idempotência)
    documento = Column(String(100), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EstornoVendaProcessado(Base):
    """
    Ledger de idempotência do estorno (devolução) de estoque por venda reembolsada.

    Garante que a devolução de estoque de uma venda execute EXATAMENTE UMA VEZ. A unique
    constraint (empresa_id, documento) serializa estornos concorrentes do mesmo documento:
    webhooks de reembolso duplicados/reentregues do Mercado Pago e retries colidem no índice
    único e não devolvem estoque em duplicidade.

    Independente de BaixaVendaProcessada (baixa e estorno são eventos distintos da venda).
    documento == numero_venda.
    """
    __tablename__ = "estornos_venda_processados"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'documento', name='uq_estorno_venda_empresa_documento'),
        Index('ix_estorno_venda_empresa_documento', 'empresa_id', 'documento'),
        {"schema": "estoque"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Multi-tenancy
    empresa_id = Column(Integer, nullable=False, index=True)

    # Número da venda (chave de idempotência)
    documento = Column(String(100), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Inventario(Base):
    """
    Modelo de Inventário.
    Registra contagens físicas de estoque.
    """
    __tablename__ = "inventarios"
    __table_args__ = (
        Index('ix_inventarios_empresa_id', 'empresa_id'),
        Index('ix_inventarios_empresa_id_data', 'empresa_id', 'data_inventario'),
        {"schema": "estoque"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Multi-tenancy
    empresa_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="ID da empresa (multi-tenancy)"
    )
    
    data_inventario = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    responsavel = Column(String(200), nullable=False)
    observacao = Column(Text, nullable=True)
    
    finalizado = Column(Boolean, default=False, nullable=False)
    data_finalizacao = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    itens = relationship("ItemInventario", back_populates="inventario", cascade="all, delete-orphan")


class ItemInventario(Base):
    """
    Modelo de Item de Inventário.
    Registra a contagem de cada produto no inventário.
    """
    __tablename__ = "itens_inventario"
    __table_args__ = {"schema": "estoque"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    inventario_id = Column(UUID(as_uuid=True), ForeignKey("estoque.inventarios.id"), nullable=False, index=True)
    estoque_id = Column(UUID(as_uuid=True), ForeignKey("estoque.estoque.id"), nullable=False, index=True)
    
    quantidade_sistema = Column(Float, nullable=False)
    quantidade_contada = Column(Float, nullable=False)
    diferenca = Column(Float, nullable=False)
    
    observacao = Column(Text, nullable=True)
    ajustado = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    inventario = relationship("Inventario", back_populates="itens")
