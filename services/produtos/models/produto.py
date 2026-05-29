"""
Modelo de Produto.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Produto(Base):
    """Modelo de Produto."""
    
    __tablename__ = "produtos"
    __table_args__ = {"schema": "produtos"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    categoria_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.categorias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
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
        return f"<Produto(id={self.id}, nome={self.nome})>"
