"""add campos essenciais produto

Revision ID: 20260612_add_campos_essenciais
Revises: add_deletado_em_to_produtos
Create Date: 2026-06-12 03:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260612_add_campos_essenciais'
down_revision: Union[str, None] = '20260609_multitenancy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona campos essenciais ao modelo Produto:
    - codigo_barras, sku, unidade_medida
    - preco, custo, preco_promocional
    - estoque_minimo, estoque_maximo
    - peso_bruto, peso_liquido
    """
    # Adicionar colunas
    op.add_column('produtos', sa.Column('codigo_barras', sa.String(length=50), nullable=True, comment='Código de barras/EAN'), schema='produtos')
    op.add_column('produtos', sa.Column('sku', sa.String(length=100), nullable=True, comment='SKU interno'), schema='produtos')
    op.add_column('produtos', sa.Column('unidade_medida', sa.String(length=10), nullable=False, server_default='UN', comment='UN, KG, LT, etc'), schema='produtos')
    
    op.add_column('produtos', sa.Column('preco', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00', comment='Preço de venda'), schema='produtos')
    op.add_column('produtos', sa.Column('custo', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00', comment='Custo de aquisição'), schema='produtos')
    op.add_column('produtos', sa.Column('preco_promocional', sa.Numeric(precision=10, scale=2), nullable=True, comment='Preço promocional'), schema='produtos')
    
    op.add_column('produtos', sa.Column('estoque_minimo', sa.Integer(), nullable=False, server_default='0', comment='Estoque mínimo para alerta'), schema='produtos')
    op.add_column('produtos', sa.Column('estoque_maximo', sa.Integer(), nullable=True, comment='Estoque máximo'), schema='produtos')
    
    op.add_column('produtos', sa.Column('peso_bruto', sa.Numeric(precision=10, scale=3), nullable=True, comment='Peso em KG'), schema='produtos')
    op.add_column('produtos', sa.Column('peso_liquido', sa.Numeric(precision=10, scale=3), nullable=True, comment='Peso líquido em KG'), schema='produtos')
    
    # Criar índices
    op.create_index('ix_produtos_codigo_barras', 'produtos', ['codigo_barras'], unique=False, schema='produtos')
    op.create_index('ix_produtos_sku', 'produtos', ['sku'], unique=False, schema='produtos')
    
    # Criar constraint única para empresa_id + codigo_barras
    op.create_unique_constraint('uq_produtos_empresa_codigo_barras', 'produtos', ['empresa_id', 'codigo_barras'], schema='produtos')


def downgrade() -> None:
    """Remove os campos adicionados."""
    # Remover constraint
    op.drop_constraint('uq_produtos_empresa_codigo_barras', 'produtos', schema='produtos', type_='unique')
    
    # Remover índices
    op.drop_index('ix_produtos_sku', table_name='produtos', schema='produtos')
    op.drop_index('ix_produtos_codigo_barras', table_name='produtos', schema='produtos')
    
    # Remover colunas
    op.drop_column('produtos', 'peso_liquido', schema='produtos')
    op.drop_column('produtos', 'peso_bruto', schema='produtos')
    op.drop_column('produtos', 'estoque_maximo', schema='produtos')
    op.drop_column('produtos', 'estoque_minimo', schema='produtos')
    op.drop_column('produtos', 'preco_promocional', schema='produtos')
    op.drop_column('produtos', 'custo', schema='produtos')
    op.drop_column('produtos', 'preco', schema='produtos')
    op.drop_column('produtos', 'unidade_medida', schema='produtos')
    op.drop_column('produtos', 'sku', schema='produtos')
    op.drop_column('produtos', 'codigo_barras', schema='produtos')
