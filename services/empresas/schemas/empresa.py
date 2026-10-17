"""
Schemas do domínio de Empresas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re

from models.empresa import TipoEmpresa, StatusEmpresa, RegimeTributario
from utils.validators import validar_cnpj as validar_digitos_cnpj


def validar_formato_slug(v: str) -> str:
    """Slug é o endereço público da loja (/c/{slug}) — só kebab-case URL-safe."""
    v = v.lower().strip()
    if not re.match(r'^[a-z0-9-]+$', v):
        raise ValueError("Slug deve conter apenas letras minúsculas, números e hífen")
    if v.startswith('-') or v.endswith('-'):
        raise ValueError("Slug não pode começar ou terminar com hífen")
    if '--' in v:
        raise ValueError("Slug não pode conter hífens consecutivos")
    return v


class EmpresaBase(BaseModel):
    """Schema base de Empresa."""
    slug: str = Field(..., min_length=3, max_length=100)
    razao_social: str = Field(..., min_length=3, max_length=200)
    nome_fantasia: str = Field(..., min_length=3, max_length=200)
    tipo: TipoEmpresa = TipoEmpresa.MATRIZ
    status: StatusEmpresa = StatusEmpresa.ATIVA
    cnpj: str = Field(..., min_length=18, max_length=18)
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    regime_tributario: RegimeTributario = RegimeTributario.SIMPLES_NACIONAL
    cep: str = Field(..., min_length=9, max_length=9)
    logradouro: str = Field(..., min_length=3, max_length=200)
    numero: str = Field(..., min_length=1, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: str = Field(..., min_length=3, max_length=100)
    cidade: str = Field(..., min_length=3, max_length=100)
    uf: str = Field(..., min_length=2, max_length=2)
    telefone: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    site: Optional[str] = None
    logo_url: Optional[str] = None
    cor_primaria: Optional[str] = "#3B82F6"
    cor_secundaria: Optional[str] = "#10B981"
    catalogo_ativo: bool = True
    catalogo_titulo: Optional[str] = None
    catalogo_descricao: Optional[str] = None
    catalogo_whatsapp: Optional[str] = None
    plano: str = "BASICO"
    max_usuarios: int = 5
    max_produtos: Optional[int] = None
    max_lojas: int = 1
    empresa_matriz_id: Optional[int] = None

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        """Valida formato e dígitos verificadores do CNPJ."""
        if not re.match(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', v):
            raise ValueError("CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX")
        # A máscara sozinha aceitava 99.999.999/9999-99. O service já checava os
        # dígitos (empresa_service.py:63), só que depois de a requisição entrar.
        if not validar_digitos_cnpj(v):
            raise ValueError("CNPJ inválido")
        return v

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v: str) -> str:
        """Valida formato do CEP."""
        if not re.match(r'^\d{5}-\d{3}$', v):
            raise ValueError("CEP deve estar no formato XXXXX-XXX")
        return v

    @field_validator("uf")
    @classmethod
    def validar_uf(cls, v: str) -> str:
        """Valida UF."""
        v = v.upper()
        ufs_validas = [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
            "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
            "RS", "RO", "RR", "SC", "SP", "SE", "TO"
        ]
        if v not in ufs_validas:
            raise ValueError(f"UF inválida. Deve ser uma das: {', '.join(ufs_validas)}")
        return v

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, v: Optional[str]) -> Optional[str]:
        """Valida slug (apenas letras minúsculas, números e hífen)."""
        if v is None:
            return v
        return validar_formato_slug(v)

    @field_validator("cor_primaria", "cor_secundaria")
    @classmethod
    def validar_cor_hex(cls, v: Optional[str]) -> Optional[str]:
        """Valida cor hexadecimal."""
        if v and not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError("Cor deve estar no formato hexadecimal #RRGGBB")
        return v


class EmpresaCreate(EmpresaBase):
    """Schema para criação de empresa. Slug omitido é gerado a partir do nome fantasia."""
    slug: Optional[str] = Field(None, min_length=3, max_length=100)


class EmpresaUpdate(BaseModel):
    """Schema para atualização de empresa."""
    slug: Optional[str] = Field(None, min_length=3, max_length=100)
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    regime_tributario: Optional[RegimeTributario] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    telefone: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    site: Optional[str] = None
    logo_url: Optional[str] = None
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None
    catalogo_ativo: Optional[bool] = None
    catalogo_titulo: Optional[str] = None
    catalogo_descricao: Optional[str] = None
    catalogo_whatsapp: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato URL-safe do slug."""
        if v is None:
            return v
        return validar_formato_slug(v)

    model_config = ConfigDict(from_attributes=True)


class EmpresaPlanoUpdate(BaseModel):
    """Campos de billing/plataforma — só o router de plataforma pode escrever."""
    plano: Optional[str] = None
    max_usuarios: Optional[int] = None
    max_produtos: Optional[int] = None
    status: Optional[StatusEmpresa] = None
    ativo: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class EmpresaResponse(EmpresaBase):
    """Schema de resposta de empresa."""

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        """Resposta não revalida CNPJ: registros legados travariam a leitura/edição."""
        return v

    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
    criado_por: Optional[int] = None
    atualizado_por: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EmpresaListItem(BaseModel):
    """Schema simplificado para listagem de empresas."""
    id: int
    slug: str
    razao_social: str
    nome_fantasia: str
    cnpj: str
    tipo: TipoEmpresa
    status: StatusEmpresa
    cidade: str
    uf: str
    catalogo_ativo: bool
    plano: str
    # A tela de plano em /plataforma edita estes dois; sem eles o modal abre
    # em branco e o super admin redigita limites que ja existem.
    max_usuarios: int
    max_produtos: Optional[int]  # None = ilimitado
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class EmpresaPublicInfo(BaseModel):
    """Schema com informações públicas da empresa (para catálogo)."""
    id: int
    slug: str
    nome_fantasia: str
    logo_url: Optional[str]
    cor_primaria: str
    cor_secundaria: str
    catalogo_ativo: bool
    catalogo_titulo: Optional[str]
    catalogo_descricao: Optional[str]
    catalogo_whatsapp: Optional[str]
    cidade: str
    uf: str

    model_config = ConfigDict(from_attributes=True)
