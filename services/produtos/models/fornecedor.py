"""
Modelos de Fornecedor e FornecedorProduto.
"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Fornecedor(Base):
    """Modelo de Fornecedor."""

    __tablename__ = "fornecedores"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'cnpj', name='uq_fornecedores_empresa_cnpj'),
        Index('ix_fornecedores_empresa_id', 'empresa_id'),
        Index('ix_fornecedores_empresa_id_ativo', 'empresa_id', 'ativo'),
        {"schema": "produtos"}
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Multi-tenancy
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="ID da empresa (multi-tenancy)"
    )
    
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cnpj: Mapped[str | None] = mapped_column(String(18), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    telefone: Mapped[str | None] = mapped_column(String(20))
    endereco: Mapped[str | None] = mapped_column(Text)
    cidade: Mapped[str | None] = mapped_column(String(100), index=True)
    uf: Mapped[str | None] = mapped_column(String(2), index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relacionamentos
    produtos: Mapped[list["FornecedorProduto"]] = relationship(
        "FornecedorProduto",
        back_populates="fornecedor",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Fornecedor(id={self.id}, nome={self.nome})>"


class FornecedorProduto(Base):
    """Modelo de Associação entre Fornecedor e Produto."""

    __tablename__ = "fornecedor_produtos"
    __table_args__ = {"schema": "produtos"}

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    fornecedor_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.fornecedores.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    produto_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    codigo_fornecedor: Mapped[str | None] = mapped_column(String(100))
    preco_fornecedor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    prazo_entrega_dias: Mapped[int] = mapped_column(default=0)
    quantidade_minima: Mapped[int] = mapped_column(default=1)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    fornecedor: Mapped["Fornecedor"] = relationship(
        "Fornecedor",
        back_populates="produtos"
    )
    produto: Mapped["Produto"] = relationship(
        "Produto",
        back_populates="fornecedores"
    )

    def __repr__(self) -> str:
        return f"<FornecedorProduto(fornecedor_id={self.fornecedor_id}, produto_id={self.produto_id})>"
