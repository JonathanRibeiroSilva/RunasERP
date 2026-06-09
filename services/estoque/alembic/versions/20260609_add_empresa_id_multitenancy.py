"""add empresa_id for multi-tenancy

Revision ID: 20260609_multitenancy
Revises: 
Create Date: 2026-06-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260609_multitenancy'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adiciona empresa_id para multi-tenancy em todas as tabelas principais."""
    
    # ========== ADICIONAR COLUNA empresa_id ==========
    
    # Estoque
    op.add_column(
        'estoque',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1'),
        schema='estoque'
    )
    
    # Lotes
    op.add_column(
        'lotes',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1'),
        schema='estoque'
    )
    
    # Inventários
    op.add_column(
        'inventarios',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1'),
        schema='estoque'
    )
    
    # ========== REMOVER SERVER DEFAULT (após popular dados) ==========
    
    op.alter_column('estoque', 'empresa_id', server_default=None, schema='estoque')
    op.alter_column('lotes', 'empresa_id', server_default=None, schema='estoque')
    op.alter_column('inventarios', 'empresa_id', server_default=None, schema='estoque')
    
    # ========== REMOVER CONSTRAINTS GLOBAIS ÚNICOS ==========
    
    # Lotes: remover unique global em codigo (se existir)
    try:
        op.drop_constraint('uq_lotes_codigo', 'lotes', schema='estoque', type_='unique')
    except:
        pass  # Constraint pode não existir
    
    # ========== CRIAR CONSTRAINTS COMPOSTOS (empresa_id, field) ==========
    
    # Estoque: unique por empresa + produto + variante
    op.create_unique_constraint(
        'uq_estoque_empresa_produto_variante',
        'estoque',
        ['empresa_id', 'produto_id', 'variante_id'],
        schema='estoque'
    )
    
    # Lotes: unique por empresa + codigo
    op.create_unique_constraint(
        'uq_lotes_empresa_codigo',
        'lotes',
        ['empresa_id', 'codigo'],
        schema='estoque'
    )
    
    # ========== CRIAR INDEXES PARA PERFORMANCE ==========
    
    # Estoque
    op.create_index(
        'ix_estoque_empresa_id',
        'estoque',
        ['empresa_id'],
        schema='estoque'
    )
    op.create_index(
        'ix_estoque_empresa_id_ativo',
        'estoque',
        ['empresa_id', 'ativo'],
        schema='estoque'
    )
    
    # Lotes
    op.create_index(
        'ix_lotes_empresa_id',
        'lotes',
        ['empresa_id'],
        schema='estoque'
    )
    
    # Inventários
    op.create_index(
        'ix_inventarios_empresa_id',
        'inventarios',
        ['empresa_id'],
        schema='estoque'
    )
    op.create_index(
        'ix_inventarios_empresa_id_data',
        'inventarios',
        ['empresa_id', 'data_inventario'],
        schema='estoque'
    )


def downgrade() -> None:
    """Remove empresa_id e restaura constraints globais."""
    
    # ========== REMOVER INDEXES ==========
    
    op.drop_index('ix_inventarios_empresa_id_data', table_name='inventarios', schema='estoque')
    op.drop_index('ix_inventarios_empresa_id', table_name='inventarios', schema='estoque')
    op.drop_index('ix_lotes_empresa_id', table_name='lotes', schema='estoque')
    op.drop_index('ix_estoque_empresa_id_ativo', table_name='estoque', schema='estoque')
    op.drop_index('ix_estoque_empresa_id', table_name='estoque', schema='estoque')
    
    # ========== REMOVER UNIQUE CONSTRAINTS COMPOSTOS ==========
    
    op.drop_constraint('uq_lotes_empresa_codigo', 'lotes', schema='estoque', type_='unique')
    op.drop_constraint('uq_estoque_empresa_produto_variante', 'estoque', schema='estoque', type_='unique')
    
    # ========== RECRIAR UNIQUE CONSTRAINTS GLOBAIS ==========
    
    # Lotes: recriar unique global em codigo
    op.create_unique_constraint('uq_lotes_codigo', 'lotes', ['codigo'], schema='estoque')
    
    # ========== REMOVER COLUNA empresa_id ==========
    
    op.drop_column('inventarios', 'empresa_id', schema='estoque')
    op.drop_column('lotes', 'empresa_id', schema='estoque')
    op.drop_column('estoque', 'empresa_id', schema='estoque')
