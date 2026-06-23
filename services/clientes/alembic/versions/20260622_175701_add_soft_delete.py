"""add soft delete to clientes

Revision ID: 20260622_175701
Revises: 20260612_020300
Create Date: 2026-06-22 17:57:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260622_175701'
down_revision = '001_multitenancy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona colunas de soft delete para clientes.
    Permite manter histórico de clientes deletados.
    """
    # Verificar se colunas já existem
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('clientes', schema='clientes')]
    
    # Adicionar colunas apenas se não existirem
    if 'deletado_em' not in columns:
        op.add_column(
            'clientes',
            sa.Column('deletado_em', sa.TIMESTAMP, nullable=True),
            schema='clientes'
        )
    
    if 'deletado_por' not in columns:
        op.add_column(
            'clientes',
            sa.Column('deletado_por', postgresql.UUID(as_uuid=True), nullable=True),
            schema='clientes'
        )
    
    if 'motivo_exclusao' not in columns:
        op.add_column(
            'clientes',
            sa.Column('motivo_exclusao', sa.Text, nullable=True),
            schema='clientes'
        )
    
    # Criar índices para performance (apenas clientes ativos)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('clientes', schema='clientes')]
    
    if 'ix_clientes_deletado_em' not in existing_indexes:
        op.create_index(
            'ix_clientes_deletado_em',
            'clientes',
            ['deletado_em'],
            schema='clientes',
            postgresql_where=sa.text('deletado_em IS NULL')
        )
    
    if 'ix_clientes_empresa_ativo' not in existing_indexes:
        op.create_index(
            'ix_clientes_empresa_ativo',
            'clientes',
            ['empresa_id', 'ativo'],
            schema='clientes',
            postgresql_where=sa.text('deletado_em IS NULL')
        )


def downgrade() -> None:
    """Remove colunas de soft delete."""
    op.drop_index('ix_clientes_empresa_ativo', table_name='clientes', schema='clientes')
    op.drop_index('ix_clientes_deletado_em', table_name='clientes', schema='clientes')
    op.drop_column('clientes', 'motivo_exclusao', schema='clientes')
    op.drop_column('clientes', 'deletado_por', schema='clientes')
    op.drop_column('clientes', 'deletado_em', schema='clientes')
