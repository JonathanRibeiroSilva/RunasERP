"""
Modelo de Produto.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, Integer, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# O Brasil não tem horário de verão desde 2019, então o offset é fixo e não
# precisa da base de fusos do sistema — a imagem é python:3.12-slim, que pode
# subir sem tzdata. Se o horário de verão voltar, é esta linha que muda.
FUSO_LOJA = timezone(timedelta(hours=-3))


def hoje_na_loja() -> date:
    """Data de hoje para o lojista, não para o servidor.

    Comparar promoção contra a data em UTC encerraria uma promoção que "vale
    até dia 30" às 21h do dia 30 — justamente as horas de melhor venda do
    último dia.
    """
    return datetime.now(FUSO_LOJA).date()


class Produto(Base):
    """Modelo de Produto."""
    
    __tablename__ = "produtos"
    __table_args__ = (
        Index('ix_produtos_empresa_id_ativo', 'empresa_id', 'ativo'),
        Index('ix_produtos_empresa_id_nome', 'empresa_id', 'nome'),
        UniqueConstraint('empresa_id', 'codigo_barras', name='uq_produtos_empresa_codigo_barras'),
        {"schema": "produtos"}
    )
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Multi-tenancy
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="ID da empresa (multi-tenancy)"
    )
    
    categoria_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.categorias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    
    # Campos essenciais de produto
    codigo_barras: Mapped[str | None] = mapped_column(String(50), index=True, comment="Código de barras/EAN")
    sku: Mapped[str | None] = mapped_column(String(100), index=True, comment="SKU interno")
    unidade_medida: Mapped[str] = mapped_column(String(10), default="UN", comment="UN, KG, LT, etc")
    
    # Preços e custos
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), comment="Preço de venda")
    custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), comment="Custo de aquisição")
    preco_promocional: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="Preço promocional")
    promocao_fim: Mapped[date | None] = mapped_column(
        Date,
        comment="Último dia da promoção, inclusive. Sem data, a promoção não vale.",
    )
    
    # Estoque
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=0, comment="Estoque mínimo para alerta")
    estoque_maximo: Mapped[int | None] = mapped_column(Integer, comment="Estoque máximo")
    
    # Características físicas
    peso_bruto: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), comment="Peso em KG")
    peso_liquido: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), comment="Peso líquido em KG")
    
    # Controle
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deletado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    
    # Relacionamentos
    categoria: Mapped["Categoria"] = relationship("Categoria", back_populates="produtos")
    variantes: Mapped[list["Variante"]] = relationship(
        "Variante",
        back_populates="produto",
        cascade="all, delete-orphan"
    )
    loja_online_config: Mapped["LojaOnlineConfig"] = relationship(
        "LojaOnlineConfig",
        back_populates="produto",
        uselist=False,
        cascade="all, delete-orphan"
    )
    loja_online_fotos: Mapped[list["LojaOnlineFoto"]] = relationship(
        "LojaOnlineFoto",
        back_populates="produto",
        cascade="all, delete-orphan",
        order_by="LojaOnlineFoto.ordem"
    )
    fornecedores: Mapped[list["FornecedorProduto"]] = relationship(
        "FornecedorProduto",
        back_populates="produto",
        cascade="all, delete-orphan"
    )

    @property
    def preco_efetivo(self) -> Decimal:
        """O preço que a vitrine anuncia e o carrinho cobra.

        Existe porque a regra estava escrita duas vezes: o card da loja em
        TypeScript decidia `promo > 0 ? promo : preco`, e o carrinho em Python
        lia `preco` e só. As duas se desencontraram — a loja anunciava R$ 8 e
        cobrava R$ 10. Agora a regra é uma só, calculada aqui, e quem exibe e
        quem cobra leem o mesmo campo.

        Promoção sem data de fim não vale: a data é obrigatória na escrita, e
        linha antiga sem data cobra o preço normal, que é o lado seguro — o
        anunciado e o cobrado continuam batendo de qualquer forma.
        """
        if self.preco_promocional and self.promocao_fim and self.promocao_fim >= hoje_na_loja():
            return self.preco_promocional
        return self.preco

    @property
    def promocao_ativa(self) -> bool:
        """Para a tela distinguir 'promoção expirada' de 'sem promoção'."""
        return self.preco_efetivo != self.preco

    def __repr__(self) -> str:
        return f"<Produto(id={self.id}, nome={self.nome}, preco={self.preco})>"
