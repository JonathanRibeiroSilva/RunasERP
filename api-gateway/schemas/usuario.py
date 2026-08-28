"""
Schemas Pydantic para usuário.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from models.usuario import RoleEnum


class UsuarioBase(BaseModel):
    """Schema base de usuário."""
    nome: str = Field(..., min_length=3, max_length=255)
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    """Schema para criação de usuário."""
    senha: str = Field(..., min_length=0, max_length=100)  # min_length=0 para permitir OAuth (senha vazia)
    role: RoleEnum = RoleEnum.OPERADOR
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    
    @field_validator('senha')
    @classmethod
    def validate_senha(cls, v: str) -> str:
        """Valida força da senha (apenas se senha não for vazia - OAuth users têm senha vazia)."""
        # Se senha vazia, é usuário OAuth - não validar
        if not v or len(v) == 0:
            return v
        
        # Para senhas não-vazias, validar força
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
        
        # Verificar caractere especial
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Senha deve conter ao menos um caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?)')
        
        return v


class UsuarioUpdate(BaseModel):
    """Schema para atualização de usuário."""
    nome: str | None = Field(None, min_length=3, max_length=255)
    email: EmailStr | None = None
    role: RoleEnum | None = None
    ativo: bool | None = None


class UsuarioResponse(UsuarioBase):
    """Schema de resposta de usuário."""
    id: UUID
    role: RoleEnum
    ativo: bool
    empresa_id: int | None = None  # None = SUPER_ADMIN, sem tenant
    empresa_slug: str | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema de token JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Schema de resposta de login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UsuarioResponse


class TokenPayload(BaseModel):
    """Payload do token JWT."""
    sub: str  # user_id
    role: RoleEnum
    exp: int
    iat: int


class RefreshTokenRequest(BaseModel):
    """Request para refresh token."""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Request para solicitar reset de senha."""
    email: EmailStr


def validar_forca_senha(v: str) -> str:
    """Valida força da senha (8-20 chars, maiúscula, minúscula, número, especial)."""
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


class ResetPasswordRequest(BaseModel):
    """Request para resetar senha com token."""
    token: str
    nova_senha: str = Field(..., min_length=8, max_length=20)

    @field_validator('nova_senha')
    @classmethod
    def validate_nova_senha(cls, v: str) -> str:
        """Valida força da nova senha."""
        return validar_forca_senha(v)


class AlterarSenhaRequest(BaseModel):
    """Request para alterar a própria senha (usuário autenticado)."""
    senha_atual: str
    nova_senha: str = Field(..., min_length=8, max_length=20)

    @field_validator('nova_senha')
    @classmethod
    def validate_nova_senha(cls, v: str) -> str:
        """Valida força da nova senha."""
        return validar_forca_senha(v)


