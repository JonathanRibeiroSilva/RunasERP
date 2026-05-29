"""
Modelo de Categoria.
"""
from uuid import uuid4
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Categoria(Base):
    """Modelo de Categoria de Produtos."""
    
    __tablename__ = "categorias"
    __table_args__ = {"schema": "produtos"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(String(500))
    
    # Relacionamentos
    produtos: Mapped[list["Produto"]] = relationship(
        "Produto",
        back_populates="categoria"
    )
    
    def __repr__(self) -> str:
        return f"<Categoria(id={self.id}, nome={self.nome})>"
