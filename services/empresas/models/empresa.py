"""
Modelos do domínio de Empresas (Multi-tenancy).
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SQLAEnum, Text, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from database import Base


class TipoEmpresa(str, enum.Enum):
    """Tipos de empresa."""
    MATRIZ = "MATRIZ"
    FILIAL = "FILIAL"


class StatusEmpresa(str, enum.Enum):
    """Status da empresa."""
    ATIVA = "ATIVA"
    INATIVA = "INATIVA"
    SUSPENSA = "SUSPENSA"


class RegimeTributario(str, enum.Enum):
    """Regime tributário da empresa."""
    SIMPLES_NACIONAL = "SIMPLES_NACIONAL"
    LUCRO_PRESUMIDO = "LUCRO_PRESUMIDO"
    LUCRO_REAL = "LUCRO_REAL"
    MEI = "MEI"


class Empresa(Base):
    """
    Modelo de Empresa (Multi-tenancy).
    
    Cada empresa representa um tenant no sistema.
    Todos os dados de clientes, produtos, vendas, etc. são isolados por empresa_id.
    """
    __tablename__ = "empresas"

    # Identificação
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Slug único para URL do catálogo e identificação da empresa"
    )
    razao_social: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment="Razão social da empresa"
    )
    nome_fantasia: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment="Nome fantasia da empresa"
    )
    
    # Classificação
    tipo: Mapped[TipoEmpresa] = mapped_column(
        SQLAEnum(TipoEmpresa),
        nullable=False,
        default=TipoEmpresa.MATRIZ
    )
    status: Mapped[StatusEmpresa] = mapped_column(
        SQLAEnum(StatusEmpresa),
        nullable=False,
        default=StatusEmpresa.ATIVA
    )
    
    # Documentação
    cnpj: Mapped[str] = mapped_column(
        String(18),
        unique=True,
        nullable=False,
        index=True,
        comment="CNPJ formatado: XX.XXX.XXX/XXXX-XX"
    )
    inscricao_estadual: Mapped[Optional[str]] = mapped_column(String(20))
    inscricao_municipal: Mapped[Optional[str]] = mapped_column(String(20))
    regime_tributario: Mapped[RegimeTributario] = mapped_column(
        SQLAEnum(RegimeTributario),
        nullable=False,
        default=RegimeTributario.SIMPLES_NACIONAL
    )
    
    # Endereço
    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    logradouro: Mapped[str] = mapped_column(String(200), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[Optional[str]] = mapped_column(String(100))
    bairro: Mapped[str] = mapped_column(String(100), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    
    # Contato
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    celular: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    site: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Configurações
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="URL da logo da empresa"
    )
    cor_primaria: Mapped[Optional[str]] = mapped_column(
        String(7),
        default="#3B82F6",
        comment="Cor primária do tema (hex)"
    )
    cor_secundaria: Mapped[Optional[str]] = mapped_column(
        String(7),
        default="#10B981",
        comment="Cor secundária do tema (hex)"
    )
    
    # Catálogo Público
    catalogo_ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Se o catálogo público está ativo"
    )
    catalogo_titulo: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="Título personalizado do catálogo"
    )
    catalogo_descricao: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Descrição do catálogo"
    )
    catalogo_whatsapp: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="WhatsApp para contato no catálogo"
    )
    
    # Limites e Planos (para futuro SaaS)
    plano: Mapped[str] = mapped_column(
        String(50),
        default="BASICO",
        comment="Plano contratado (BASICO, PRO, ENTERPRISE)"
    )
    max_usuarios: Mapped[int] = mapped_column(
        Integer,
        default=5,
        comment="Número máximo de usuários permitidos"
    )
    max_produtos: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Número máximo de produtos (null = ilimitado)"
    )
    max_lojas: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="Número máximo de lojas permitidas"
    )
    
    # Matriz/Filial
    empresa_matriz_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="ID da empresa matriz (apenas para filiais)"
    )
    
    # Controle
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Campos de auditoria (futuro)
    criado_por: Mapped[Optional[int]] = mapped_column(Integer)
    atualizado_por: Mapped[Optional[int]] = mapped_column(Integer)
    
    def __repr__(self) -> str:
        return f"<Empresa(id={self.id}, slug='{self.slug}', razao_social='{self.razao_social}')>"
