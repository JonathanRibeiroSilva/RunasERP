"""
Modelo de autenticação de clientes (compradores).
Separado de Usuario (operadores do sistema).
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class ClienteAuth(Base):
    """
    Modelo de autenticação para clientes compradores.
    
    Este modelo armazena apenas credenciais de autenticação.
    Os dados completos do cliente ficam no serviço de clientes.
    """
    
    __tablename__ = "clientes_auth"
    __table_args__ = {"schema": "gateway"}
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="Hash da senha ou vazio para OAuth")
    cliente_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, comment="ID do cliente no serviço clientes")
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="ID da loja onde o cliente se cadastrou")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ClienteAuth(id={self.id}, email={self.email}, empresa_id={self.empresa_id})>"
