"""
Modelos de Loja Online (LojaOnlineConfig e LojaOnlineFoto).
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class LojaOnlineConfig(Base):
    """Configuração de exibição do produto na loja online pública."""
    
    __tablename__ = "loja_online_config"
    __table_args__ = {"schema": "produtos"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    produto_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.produtos.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    visivel: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    destaque: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    ordem_exibicao: Mapped[int] = mapped_column(Integer, default=0)
    descricao_publica: Mapped[str | None] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", back_populates="loja_online_config")
    
    def __repr__(self) -> str:
        return f"<LojaOnlineConfig(produto_id={self.produto_id}, visivel={self.visivel})>"


class LojaOnlineFoto(Base):
    """Fotos do produto na loja online."""
    
    __tablename__ = "loja_online_fotos"
    __table_args__ = {"schema": "produtos"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    produto_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", back_populates="loja_online_fotos")
    
    def __repr__(self) -> str:
        return f"<LojaOnlineFoto(id={self.id}, produto_id={self.produto_id})>"
