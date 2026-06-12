"""
Modelo de Produto.
"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Integer, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Produto(Base):
    """Modelo de Produto."""
    
    __tablename__ = "produtos"
    __table_args__ = (
        Index('ix_produtos_empresa_id_ativo', 'empresa_id', 'ativo'),
        Index('ix_produtos_empresa_id_nome', 'empresa_id', 'nome'),
        UniqueConstraint('empresa_id', 'codigo_barras', name='uq_produtos_empresa_codigo_barras'),
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
    
    categoria_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.categorias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    
    # Campos essenciais de produto
    codigo_barras: Mapped[str | None] = mapped_column(String(50), index=True, comment="Código de barras/EAN")
    sku: Mapped[str | None] = mapped_column(String(100), index=True, comment="SKU interno")
    unidade_medida: Mapped[str] = mapped_column(String(10), default="UN", comment="UN, KG, LT, etc")
    
    # Preços e custos
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), comment="Preço de venda")
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), comment="Custo de aquisição")
    preco_promocional: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="Preço promocional")
    
    # Estoque
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=0, comment="Estoque mínimo para alerta")
    estoque_maximo: Mapped[int | None] = mapped_column(Integer, comment="Estoque máximo")
    
    # Características físicas
    peso_bruto: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), comment="Peso em KG")
    peso_liquido: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), comment="Peso líquido em KG")
    
    # Controle
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deletado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    
    # Relacionamentos
    categoria: Mapped["Categoria"] = relationship("Categoria", back_populates="produtos")
    variantes: Mapped[list["Variante"]] = relationship(
        "Variante",
        back_populates="produto",
        cascade="all, delete-orphan"
    )
    catalogo_config: Mapped["CatalogoConfig"] = relationship(
        "CatalogoConfig",
        back_populates="produto",
        uselist=False,
        cascade="all, delete-orphan"
    )
    catalogo_fotos: Mapped[list["CatalogoFoto"]] = relationship(
        "CatalogoFoto",
        back_populates="produto",
        cascade="all, delete-orphan",
        order_by="CatalogoFoto.ordem"
    )
    fornecedores: Mapped[list["FornecedorProduto"]] = relationship(
        "FornecedorProduto",
        back_populates="produto",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Produto(id={self.id}, nome={self.nome}, preco={self.preco})>"
