"""ledger de idempotência da entrada de estoque por NF-e

Revision ID: 20261022_entrada_nfe
Revises: 20260919_qtd_nao_neg
Create Date: 2026-10-22

Só CREATE TABLE: a tabela é nova, então não há linha legado que a constraint
possa violar — nada aqui pode virar crashloop no boot. A unique constraint já
indexa (empresa_id, chave); índice à parte em empresa_id seria redundante.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20261022_entrada_nfe'
down_revision = '20260919_qtd_nao_neg'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'entradas_nfe_processadas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('chave', sa.String(length=44), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('empresa_id', 'chave', name='uq_entrada_nfe_empresa_chave'),
        schema='estoque',
    )


def downgrade() -> None:
    op.drop_table('entradas_nfe_processadas', schema='estoque')
