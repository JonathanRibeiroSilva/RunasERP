"""
Schemas Pydantic para Produtos.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ======================== CATEGORIA ========================

class CategoriaBase(BaseModel):
    """Schema base de Categoria."""
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=500)


class CategoriaCreate(CategoriaBase):
    """Schema para criar Categoria."""
    pass


class CategoriaUpdate(BaseModel):
    """Schema para atualizar Categoria."""
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=500)


class CategoriaRead(CategoriaBase):
    """Schema para ler Categoria."""
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# ======================== ATRIBUTO VARIANTE ========================

class AtributoVarianteBase(BaseModel):
    """Schema base de AtributoVariante."""
    chave: str = Field(..., min_length=1, max_length=50)
    valor: str = Field(..., min_length=1, max_length=100)


class AtributoVarianteCreate(AtributoVarianteBase):
    """Schema para criar AtributoVariante."""
    pass


class AtributoVarianteRead(AtributoVarianteBase):
    """Schema para ler AtributoVariante."""
    id: UUID
    variante_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# ======================== VARIANTE ========================

class VarianteBase(BaseModel):
    """Schema base de Variante."""
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    sku: str = Field(..., min_length=1, max_length=100)
    preco_custo: Decimal = Field(..., gt=0)
    markup_pct: Decimal = Field(..., ge=0)
    preco_venda: Decimal = Field(..., gt=0)
    ativo: bool = True


class VarianteCreate(VarianteBase):
    """Schema para criar Variante."""
    produto_id: UUID
    atributos: list[AtributoVarianteBase] = Field(default_factory=list)


class VarianteUpdate(BaseModel):
    """Schema para atualizar Variante."""
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    preco_custo: Decimal | None = Field(default=None, gt=0)
    markup_pct: Decimal | None = Field(default=None, ge=0)
    preco_venda: Decimal | None = Field(default=None, gt=0)
    ativo: bool | None = None


class VarianteRead(VarianteBase):
    """Schema para ler Variante."""
    id: UUID
    produto_id: UUID
    atributos: list[AtributoVarianteRead] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


# ======================== LOJA ONLINE FOTO ========================

class LojaOnlineFotoBase(BaseModel):
    """Schema base de LojaOnlineFoto."""
    url: str = Field(..., min_length=1, max_length=500)
    ordem: int = Field(default=0, ge=0)


class LojaOnlineFotoCreate(LojaOnlineFotoBase):
    """Schema para criar LojaOnlineFoto."""
    produto_id: UUID


class LojaOnlineFotoUpdate(BaseModel):
    """Schema para atualizar LojaOnlineFoto."""
    url: str | None = Field(default=None, min_length=1, max_length=500)
    ordem: int | None = Field(default=None, ge=0)


class LojaOnlineFotoRead(LojaOnlineFotoBase):
    """Schema para ler LojaOnlineFoto."""
    id: UUID
    produto_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# ======================== LOJA ONLINE CONFIG ========================

class LojaOnlineConfigBase(BaseModel):
    """Schema base de LojaOnlineConfig."""
    visivel: bool = False
    destaque: bool = False
    ordem_exibicao: int = Field(default=0, ge=0)
    descricao_publica: str | None = None


class LojaOnlineConfigCreate(LojaOnlineConfigBase):
    """Schema para criar LojaOnlineConfig."""
    produto_id: UUID


class LojaOnlineConfigUpdate(BaseModel):
    """Schema para atualizar LojaOnlineConfig."""
    visivel: bool | None = None
    destaque: bool | None = None
    ordem_exibicao: int | None = Field(default=None, ge=0)
    descricao_publica: str | None = None


class LojaOnlineConfigRead(LojaOnlineConfigBase):
    """Schema para ler LojaOnlineConfig."""
    id: UUID
    produto_id: UUID
    atualizado_em: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ======================== FORNECEDOR ========================

class FornecedorBase(BaseModel):
    """Schema base de Fornecedor."""
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    nome: str = Field(..., min_length=1, max_length=255)
    cnpj: str | None = Field(default=None, max_length=18)
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=20)
    endereco: str | None = None
    cidade: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    ativo: bool = True


class FornecedorCreate(FornecedorBase):
    """Schema para criar Fornecedor."""
    pass


class FornecedorUpdate(BaseModel):
    """Schema para atualizar Fornecedor."""
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    cnpj: str | None = Field(default=None, max_length=18)
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=20)
    endereco: str | None = None
    cidade: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    ativo: bool | None = None


class FornecedorRead(FornecedorBase):
    """Schema para ler Fornecedor."""
    id: UUID
    criado_em: datetime
    atualizado_em: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ======================== FORNECEDOR PRODUTO ========================

class FornecedorProdutoBase(BaseModel):
    """Schema base de FornecedorProduto."""
    codigo_fornecedor: str | None = Field(default=None, max_length=100)
    preco_fornecedor: Decimal = Field(..., gt=0)
    prazo_entrega_dias: int = Field(default=0, ge=0)
    quantidade_minima: int = Field(default=1, ge=1)
    ativo: bool = True


class FornecedorProdutoCreate(FornecedorProdutoBase):
    """Schema para criar FornecedorProduto."""
    fornecedor_id: UUID
    produto_id: UUID


class FornecedorProdutoUpdate(BaseModel):
    """Schema para atualizar FornecedorProduto."""
    codigo_fornecedor: str | None = Field(default=None, max_length=100)
    preco_fornecedor: Decimal | None = Field(default=None, gt=0)
    prazo_entrega_dias: int | None = Field(default=None, ge=0)
    quantidade_minima: int | None = Field(default=None, ge=1)
    ativo: bool | None = None


class FornecedorProdutoRead(FornecedorProdutoBase):
    """Schema para ler FornecedorProduto."""
    id: UUID
    fornecedor_id: UUID
    produto_id: UUID
    criado_em: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ======================== PRODUTO (COMPLETO) ========================

class ProdutoBase(BaseModel):
    """Schema base de Produto."""
    empresa_id: int = Field(..., gt=0, description="ID da empresa (multi-tenancy)")
    nome: str = Field(..., min_length=1, max_length=255)
    descricao: str | None = None
    ativo: bool = True


class ProdutoCreate(ProdutoBase):
    """Schema para criar Produto."""
    categoria_id: UUID


class ProdutoUpdate(BaseModel):
    """Schema para atualizar Produto."""
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    categoria_id: UUID | None = None
    descricao: str | None = None
    ativo: bool | None = None


class ProdutoRead(ProdutoBase):
    """Schema para ler Produto."""
    id: UUID
    categoria_id: UUID
    categoria: CategoriaRead | None = None
    criado_em: datetime
    preco: Decimal = Field(default=Decimal("0.00"), description="Preço de venda")
    custo: Decimal = Field(default=Decimal("0.00"), description="Custo de aquisição")
    preco_promocional: Decimal | None = Field(default=None, description="Preço promocional")
    codigo_barras: str | None = Field(default=None, description="Código de barras/EAN")
    sku: str | None = Field(default=None, description="SKU interno")
    unidade_medida: str = Field(default="UN", description="UN, KG, LT, etc")
    variantes: list[VarianteRead] = Field(default_factory=list)
    loja_online_config: LojaOnlineConfigRead | None = None
    loja_online_fotos: list[LojaOnlineFotoRead] = Field(default_factory=list)
    fornecedores: list[FornecedorProdutoRead] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class ProdutoReadSimples(ProdutoBase):
    """Schema simplificado para ler Produto."""
    id: UUID
    categoria_id: UUID
    criado_em: datetime
    preco: Decimal = Field(default=Decimal("0.00"), description="Preço de venda")
    preco_promocional: Decimal | None = Field(default=None, description="Preço promocional")
    
    model_config = ConfigDict(from_attributes=True)


# ======================== SCHEMAS LOJA ONLINE PÚBLICA ========================

class VarianteLojaOnlineRead(BaseModel):
    """Schema de variante para a loja online pública (sem dados internos)."""
    id: UUID
    sku: str
    preco_venda: Decimal
    ativo: bool
    atributos: list[AtributoVarianteBase] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProdutoLojaOnlineRead(BaseModel):
    """Schema de produto para a loja online pública (sem custo, markup, fornecedores)."""
    id: UUID
    nome: str
    descricao: str | None = None
    ativo: bool
    categoria_id: UUID
    categoria: CategoriaRead | None = None
    criado_em: datetime
    variantes: list[VarianteLojaOnlineRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
