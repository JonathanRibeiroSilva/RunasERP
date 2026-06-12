"""add cliente_auth table

Revision ID: 20260612_120000
Revises: 20260612_020300
Create Date: 2026-06-12 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '20260612_120000'
down_revision = '20260612_020300'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria tabela de autenticação de clientes (compradores)."""
    op.create_table(
        'clientes_auth',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('senha_hash', sa.String(255), nullable=False, comment='Hash da senha ou vazio para OAuth'),
        sa.Column('cliente_id', UUID(as_uuid=True), nullable=False, comment='ID do cliente no serviço clientes'),
        sa.Column('empresa_id', sa.Integer(), nullable=False, index=True, comment='ID da loja onde o cliente se cadastrou'),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        schema='gateway'
    )


def downgrade() -> None:
    """Remove tabela de autenticação de clientes."""
    op.drop_table('clientes_auth', schema='gateway')
