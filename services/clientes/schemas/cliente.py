"""
Schemas Pydantic para Cliente.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from utils.validators import validar_cpf, normalizar_cpf, normalizar_telefone


class ClienteBase(BaseModel):
    """Schema base de cliente."""
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    nome: str = Field(..., min_length=3, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=14)
    telefone: str
    email: str | None = None
    data_nasc: date | None = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Valida e normaliza CPF."""
        cpf_limpo = normalizar_cpf(v)
        if not validar_cpf(cpf_limpo):
            raise ValueError('CPF inválido')
        return cpf_limpo
    
    @field_validator('telefone')
    @classmethod
    def validate_telefone(cls, v: str) -> str:
        """Normaliza telefone para E.164."""
        try:
            return normalizar_telefone(v)
        except ValueError as e:
            raise ValueError(str(e))


class ClienteCreate(ClienteBase):
    """Schema para criação de cliente."""
    pass


class ClienteCreateOAuth(BaseModel):
    """Schema para criação de cliente via OAuth (sem CPF/telefone obrigatórios)."""
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    nome: str = Field(..., min_length=3, max_length=255)
    email: str = Field(..., description="Email do cliente (obrigatório para OAuth)")
    cpf: str | None = Field(None, description="CPF opcional para OAuth")
    telefone: str | None = Field(None, description="Telefone opcional para OAuth")
    data_nasc: date | None = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str | None) -> str | None:
        """Valida e normaliza CPF se fornecido."""
        if v is None:
            return None
        cpf_limpo = normalizar_cpf(v)
        if not validar_cpf(cpf_limpo):
            raise ValueError('CPF inválido')
        return cpf_limpo
    
    @field_validator('telefone')
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        """Normaliza telefone para E.164 se fornecido."""
        if v is None:
            return None
        try:
            return normalizar_telefone(v)
        except ValueError as e:
            raise ValueError(str(e))


class ClienteUpdate(BaseModel):
    """Schema para atualização de cliente."""
    nome: str | None = Field(None, min_length=3, max_length=255)
    telefone: str | None = None
    email: str | None = None
    data_nasc: date | None = None
    
    @field_validator('telefone')
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        """Normaliza telefone para E.164."""
        if v is None:
            return None
        try:
            return normalizar_telefone(v)
        except ValueError as e:
            raise ValueError(str(e))


class ClienteResponse(BaseModel):
    """Schema de resposta de cliente."""
    id: UUID
    empresa_id: int
    nome: str
    cpf: str | None  # Opcional para clientes OAuth
    telefone: str | None  # Opcional para clientes OAuth
    email: str | None
    data_nasc: date | None
    limite_credito: Decimal
    credito_disponivel: Decimal
    dia_vencimento: int | None
    bloqueado: bool
    ativo: bool
    criado_em: datetime
    
    model_config = {"from_attributes": True}


class CreditoUpdate(BaseModel):
    """Schema para atualização de crédito."""
    limite_credito: Decimal = Field(..., ge=0)
    dia_vencimento: int | None = Field(None, ge=1, le=28)


class CreditoDelta(BaseModel):
    """Schema para ajuste de crédito (usado internamente)."""
    delta: Decimal  # Positivo = crédito, Negativo = débito


class EnderecoBase(BaseModel):
    """Schema base de endereço."""
    cep: str = Field(..., min_length=8, max_length=8)
    logradouro: str = Field(..., min_length=3, max_length=255)
    numero: str = Field(..., min_length=1, max_length=20)
    complemento: str | None = None
    bairro: str = Field(..., min_length=3, max_length=100)
    cidade: str = Field(..., min_length=3, max_length=100)
    uf: str = Field(..., min_length=2, max_length=2)
    principal: bool = False


class EnderecoCreate(EnderecoBase):
    """Schema para criação de endereço."""
    pass


class EnderecoUpdate(BaseModel):
    """Schema para atualização de endereço."""
    cep: str | None = Field(None, min_length=8, max_length=8)
    logradouro: str | None = Field(None, min_length=3, max_length=255)
    numero: str | None = Field(None, min_length=1, max_length=20)
    complemento: str | None = None
    bairro: str | None = Field(None, min_length=3, max_length=100)
    cidade: str | None = Field(None, min_length=3, max_length=100)
    uf: str | None = Field(None, min_length=2, max_length=2)
    principal: bool | None = None


class EnderecoResponse(EnderecoBase):
    """Schema de resposta de endereço."""
    id: UUID
    cliente_id: UUID
    
    model_config = {"from_attributes": True}


class ClienteComEnderecos(ClienteResponse):
    """Schema de cliente com endereços."""
    enderecos: list[EnderecoResponse] = []
