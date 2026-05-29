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
    op.add_column(
        'produtos',
        sa.Column('deletado_em', sa.DateTime(), nullable=True),
        schema='produtos'
    )
    
    # Adiciona índice para melhorar performance de queries
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
