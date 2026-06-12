"""
Modelo de usuário para autenticação.
"""
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class RoleEnum(str, PyEnum):
    """Roles de usuário."""
    ADMIN = "ADMIN"
    OPERADOR = "OPERADOR"


class Usuario(Base):
    """Modelo de usuário."""
    
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "gateway"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False, default=RoleEnum.OPERADOR)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="ID da empresa (multi-tenancy)")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Usuario(id={self.id}, email={self.email}, role={self.role}, empresa_id={self.empresa_id})>"
