"""
Modelos de Variante e AtributoVariante.
"""
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Variante(Base):
    """Modelo de Variante de Produto."""
    
    __tablename__ = "variantes"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'sku', name='uq_variantes_empresa_sku'),
        Index('ix_variantes_empresa_id_ativo', 'empresa_id', 'ativo'),
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
    
    produto_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    preco_custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    markup_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", back_populates="variantes")
    atributos: Mapped[list["AtributoVariante"]] = relationship(
        "AtributoVariante",
        back_populates="variante",
        cascade="all, delete-orphan"
    )
    
    def calcular_preco_venda(self) -> Decimal:
        """Calcula o preço de venda baseado no custo e markup."""
        return self.preco_custo * (1 + self.markup_pct / 100)
    
    def __repr__(self) -> str:
        return f"<Variante(id={self.id}, sku={self.sku})>"


class AtributoVariante(Base):
    """Modelo de Atributo de Variante (ex: cor, tamanho)."""
    
    __tablename__ = "atributos_variante"
    __table_args__ = {"schema": "produtos"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    variante_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.variantes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chave: Mapped[str] = mapped_column(String(50), nullable=False)
    valor: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relacionamentos
    variante: Mapped["Variante"] = relationship("Variante", back_populates="atributos")
    
    def __repr__(self) -> str:
        return f"<AtributoVariante(variante_id={self.variante_id}, {self.chave}={self.valor})>"
