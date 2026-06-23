"""
Schemas Pydantic para autenticação de clientes compradores.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class ClienteRegisterRequest(BaseModel):
    """Request para registro de cliente (comprador)."""
    email: EmailStr
    senha: str = Field(..., min_length=8, max_length=20)
    nome: str = Field(..., min_length=3, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF apenas números")
    telefone: str = Field(..., min_length=10, max_length=20)
    empresa_id: int = Field(..., gt=0, description="ID da loja onde está se cadastrando")
    
    @field_validator('senha')
    @classmethod
    def validate_senha(cls, v: str) -> str:
        """Valida força da senha."""
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        if len(v) > 20:
            raise ValueError('Senha deve ter no máximo 20 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter ao menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter ao menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter ao menos um número')
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Senha deve conter ao menos um caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?)')
        
        return v
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Valida que CPF contém apenas números."""
        if not v.isdigit():
            raise ValueError('CPF deve conter apenas números')
        return v


class ClienteLoginResponse(BaseModel):
    """Schema de resposta de login de cliente."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_type: str = "cliente"
    cliente: dict  # Dados do cliente do serviço clientes


class ClienteAuthResponse(BaseModel):
    """Schema de resposta de autenticação de cliente."""
    id: UUID
    email: str
    cliente_id: UUID
    empresa_id: int
    ativo: bool
    criado_em: datetime
    
    model_config = {"from_attributes": True}
