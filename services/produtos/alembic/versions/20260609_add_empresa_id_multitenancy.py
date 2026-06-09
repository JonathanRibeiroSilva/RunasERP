"""add empresa_id for multi-tenancy

Revision ID: 20260609_multitenancy
Revises: add_deletado_em
Create Date: 2026-06-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260609_multitenancy'
down_revision = 'add_deletado_em'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adiciona empresa_id para multi-tenancy em todas as tabelas principais."""
    
    # ========== ADICIONAR COLUNA empresa_id ==========
    
    # Produtos
    op.add_column(
        'produtos',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1'),
        schema='produtos'
    )
    
    # Categorias
    op.add_column(
        'categorias',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1'),
        schema='produtos'
    )
    
    # Variantes
    op.add_column(
        'variantes',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1'),
        schema='produtos'
    )
    
    # Fornecedores
    op.add_column(
        'fornecedores',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1'),
        schema='produtos'
    )
    
    # ========== REMOVER SERVER DEFAULT (após popular dados) ==========
    
    op.alter_column('produtos', 'empresa_id', server_default=None, schema='produtos')
    op.alter_column('categorias', 'empresa_id', server_default=None, schema='produtos')
    op.alter_column('variantes', 'empresa_id', server_default=None, schema='produtos')
    op.alter_column('fornecedores', 'empresa_id', server_default=None, schema='produtos')
    
    # ========== REMOVER CONSTRAINTS GLOBAIS ÚNICOS ==========
    
    # Categorias: remover unique global em nome (se existir)
    # Nota: verificar se constraint existe antes de dropar
    op.drop_constraint('uq_categorias_nome', 'categorias', schema='produtos', type_='unique')
    
    # Variantes: remover unique global em sku (se existir)
    op.drop_constraint('uq_variantes_sku', 'variantes', schema='produtos', type_='unique')
    
    # Fornecedores: remover unique global em cnpj e email (se existirem)
    op.drop_constraint('fornecedores_cnpj_key', 'fornecedores', schema='produtos', type_='unique')
    op.drop_constraint('fornecedores_email_key', 'fornecedores', schema='produtos', type_='unique')
    
    # ========== CRIAR CONSTRAINTS COMPOSTOS (empresa_id, field) ==========
    
    # Categorias: unique por empresa
    op.create_unique_constraint(
        'uq_categorias_empresa_nome',
        'categorias',
        ['empresa_id', 'nome'],
        schema='produtos'
    )
    
    # Variantes: unique por empresa
    op.create_unique_constraint(
        'uq_variantes_empresa_sku',
        'variantes',
        ['empresa_id', 'sku'],
        schema='produtos'
    )
    
    # Fornecedores: unique por empresa
    op.create_unique_constraint(
        'uq_fornecedores_empresa_cnpj',
        'fornecedores',
        ['empresa_id', 'cnpj'],
        schema='produtos'
    )
    
    # ========== CRIAR INDEXES PARA PERFORMANCE ==========
    
    # Produtos
    op.create_index(
        'ix_produtos_empresa_id',
        'produtos',
        ['empresa_id'],
        schema='produtos'
    )
    op.create_index(
        'ix_produtos_empresa_id_ativo',
        'produtos',
        ['empresa_id', 'ativo'],
        schema='produtos'
    )
    op.create_index(
        'ix_produtos_empresa_id_nome',
        'produtos',
        ['empresa_id', 'nome'],
        schema='produtos'
    )
    
    # Categorias
    op.create_index(
        'ix_categorias_empresa_id',
        'categorias',
        ['empresa_id'],
        schema='produtos'
    )
    
    # Variantes
    op.create_index(
        'ix_variantes_empresa_id_ativo',
        'variantes',
        ['empresa_id', 'ativo'],
        schema='produtos'
    )
    
    # Fornecedores
    op.create_index(
        'ix_fornecedores_empresa_id',
        'fornecedores',
        ['empresa_id'],
        schema='produtos'
    )
    op.create_index(
        'ix_fornecedores_empresa_id_ativo',
        'fornecedores',
        ['empresa_id', 'ativo'],
        schema='produtos'
    )


def downgrade() -> None:
    """Remove empresa_id e restaura constraints globais."""
    
    # ========== REMOVER INDEXES ==========
    
    op.drop_index('ix_fornecedores_empresa_id_ativo', table_name='fornecedores', schema='produtos')
    op.drop_index('ix_fornecedores_empresa_id', table_name='fornecedores', schema='produtos')
    op.drop_index('ix_variantes_empresa_id_ativo', table_name='variantes', schema='produtos')
    op.drop_index('ix_categorias_empresa_id', table_name='categorias', schema='produtos')
    op.drop_index('ix_produtos_empresa_id_nome', table_name='produtos', schema='produtos')
    op.drop_index('ix_produtos_empresa_id_ativo', table_name='produtos', schema='produtos')
    op.drop_index('ix_produtos_empresa_id', table_name='produtos', schema='produtos')
    
    # ========== REMOVER UNIQUE CONSTRAINTS COMPOSTOS ==========
    
    op.drop_constraint('uq_fornecedores_empresa_cnpj', 'fornecedores', schema='produtos', type_='unique')
    op.drop_constraint('uq_variantes_empresa_sku', 'variantes', schema='produtos', type_='unique')
    op.drop_constraint('uq_categorias_empresa_nome', 'categorias', schema='produtos', type_='unique')
    
    # ========== RECRIAR UNIQUE CONSTRAINTS GLOBAIS ==========
    
    op.create_unique_constraint('fornecedores_email_key', 'fornecedores', ['email'], schema='produtos')
    op.create_unique_constraint('fornecedores_cnpj_key', 'fornecedores', ['cnpj'], schema='produtos')
    op.create_unique_constraint('uq_variantes_sku', 'variantes', ['sku'], schema='produtos')
    op.create_unique_constraint('uq_categorias_nome', 'categorias', ['nome'], schema='produtos')
    
    # ========== REMOVER COLUNA empresa_id ==========
    
    op.drop_column('fornecedores', 'empresa_id', schema='produtos')
    op.drop_column('variantes', 'empresa_id', schema='produtos')
    op.drop_column('categorias', 'empresa_id', schema='produtos')
    op.drop_column('produtos', 'empresa_id', schema='produtos')
