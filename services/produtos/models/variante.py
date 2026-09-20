"""
Modelos de Variante e AtributoVariante.
"""
from decimal import Decimal, ROUND_HALF_UP
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
        """
        Preço de venda derivado do custo e do markup, já na precisão da coluna.

        O `quantize` não é cosmético. Sem ele a instância carrega 13.3333
        enquanto a coluna `Numeric(10, 2)` guarda 13.33 — e é a instância que a
        rota devolve logo depois do POST, antes de qualquer SELECT novo. Dois
        números para o mesmo preço é exatamente o que este cálculo existe para
        não ter.

        `ROUND_HALF_UP` porque é o que o Postgres faz ao gravar em
        `Numeric(10, 2)`; o padrão do Python é `ROUND_HALF_EVEN`, que na metade
        do centavo (R$ 1,125) daria 1,12 aqui e 1,13 no disco.
        """
        return (self.preco_custo * (1 + self.markup_pct / 100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    
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
