"""
Modelos de Cliente e Endereco.
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class TipoMovimentoCredito(str, Enum):
    """Tipo de linha do ledger de crédito."""
    ABERTURA = "ABERTURA"
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"


class Cliente(Base):
    """Modelo de Cliente."""
    
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'cpf', name='uq_clientes_empresa_cpf'),
        Index('ix_clientes_empresa_id_ativo', 'empresa_id', 'ativo'),
        Index('ix_clientes_empresa_id_nome', 'empresa_id', 'nome'),
        {"schema": "clientes"}
    )
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Multi-tenancy
    empresa_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        index=True,
        comment="ID da empresa (multi-tenancy)"
    )
    
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True, comment="CPF opcional para clientes OAuth")
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="Telefone opcional para clientes OAuth")
    email: Mapped[str | None] = mapped_column(String(255))
    data_nasc: Mapped[date | None] = mapped_column(Date)
    limite_credito: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    credito_disponivel: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    dia_vencimento: Mapped[int | None] = mapped_column(Integer)
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    enderecos: Mapped[list["Endereco"]] = relationship(
        "Endereco",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, nome={self.nome}, cpf={self.cpf})>"


class Endereco(Base):
    """Modelo de Endereço."""
    
    __tablename__ = "enderecos"
    __table_args__ = {"schema": "clientes"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cliente_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.clientes.id", ondelete="CASCADE"))
    cep: Mapped[str] = mapped_column(String(8), nullable=False)
    logradouro: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(255))
    bairro: Mapped[str] = mapped_column(String(100), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    principal: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="enderecos")
    
    def __repr__(self) -> str:
        return f"<Endereco(id={self.id}, cliente_id={self.cliente_id})>"


class MovimentoCredito(Base):
    """
    Ledger de crédito do cliente — fonte de verdade de `Cliente.credito_disponivel`.

    C1+C2+C3 (Onda 6): antes, `credito_disponivel` era um campo solto, mutado direto
    por dois caminhos sem auditoria nenhuma — `atualizar_credito` (limite) zerava o
    saldo devedor a cada edição, `ajustar_credito_disponivel` (delta) não tinha
    proteção de concorrência nem idempotência, e nada em `vendas` checava o teto antes
    de fechar uma venda fiada. Este ledger substitui o campo mutável: toda mudança de
    saldo vira uma linha aqui, `credito_disponivel` continua existindo como cache
    (atualizado na mesma transação/lock, igual `estoque.quantidade_reservada`), mas a
    soma das linhas é o que de fato aconteceu.

    `documento` == numero_venda para DEBITO/CREDITO (chave de idempotência — mesmo
    desenho de `estoque.BaixaVendaProcessada`: unique (empresa_id, documento, tipo)
    serializa debitos/créditos concorrentes do mesmo evento). ABERTURA é a linha de
    backfill da migration, uma por cliente, documento = `ABERTURA-<cliente_id>`.
    """
    __tablename__ = "movimentos_credito"
    __table_args__ = (
        UniqueConstraint(
            'empresa_id', 'documento', 'tipo',
            name='uq_movimentos_credito_empresa_documento_tipo'
        ),
        Index('ix_movimentos_credito_cliente_id', 'cliente_id'),
        {"schema": "clientes"}
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cliente_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.clientes.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    # Sinal carrega o efeito: positivo aumenta credito_disponivel (ABERTURA, CREDITO),
    # negativo diminui (DEBITO). SUM(valor) por cliente == credito_disponivel.
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    documento: Mapped[str] = mapped_column(String(100), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<MovimentoCredito(cliente_id={self.cliente_id}, tipo={self.tipo}, valor={self.valor})>"
