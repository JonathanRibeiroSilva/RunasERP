"""add empresa_id to usuario

Revision ID: 20260612_020300
Revises: 20260611_initial_gateway
Create Date: 2026-06-12 02:03:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260612_020300'
down_revision: Union[str, None] = '20260611_gateway'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona coluna empresa_id à tabela gateway.usuarios.
    Define empresa_id = 1 como padrão para todos os usuários existentes.
    """
    # Adicionar coluna empresa_id com valor padrão temporário
    op.add_column(
        'usuarios',
        sa.Column('empresa_id', sa.Integer(), nullable=True, comment='ID da empresa (multi-tenancy)'),
        schema='gateway'
    )
    
    # Atualizar registros existentes com empresa_id = 1 (empresa padrão)
    op.execute("UPDATE gateway.usuarios SET empresa_id = 1 WHERE empresa_id IS NULL")
    
    # Tornar a coluna NOT NULL
    op.alter_column(
        'usuarios',
        'empresa_id',
        nullable=False,
        schema='gateway'
    )
    
    # Criar índice na coluna empresa_id
    op.create_index(
        'ix_gateway_usuarios_empresa_id',
        'usuarios',
        ['empresa_id'],
        unique=False,
        schema='gateway'
    )


def downgrade() -> None:
    """Remove coluna empresa_id da tabela gateway.usuarios."""
    # Remover índice
    op.drop_index('ix_gateway_usuarios_empresa_id', table_name='usuarios', schema='gateway')
    
    # Remover coluna
    op.drop_column('usuarios', 'empresa_id', schema='gateway')
