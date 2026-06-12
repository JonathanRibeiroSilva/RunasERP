"""add deletado_em to produtos

Revision ID: add_deletado_em
Revises: 
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_deletado_em'
down_revision = None  # Ajuste conforme a última migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adiciona campo deletado_em para soft delete."""
    # Verificar se coluna deletado_em já existe
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('produtos', schema='produtos')]
    
    if 'deletado_em' not in columns:
        op.add_column(
            'produtos',
            sa.Column('deletado_em', sa.DateTime(), nullable=True),
            schema='produtos'
        )
    
    # Adiciona índice para melhorar performance de queries (se não existir)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('produtos', schema='produtos')]
    
    if 'ix_produtos_deletado_em' not in existing_indexes:
        op.create_index(
            'ix_produtos_deletado_em',
            'produtos',
            ['deletado_em'],
            schema='produtos'
        )


def downgrade() -> None:
    """Remove campo deletado_em."""
    op.drop_index('ix_produtos_deletado_em', table_name='produtos', schema='produtos')
    op.drop_column('produtos', 'deletado_em', schema='produtos')
