"""reconciliação de crédito, separada da de estoque (C3, Onda 6)

Revision ID: 20261004_rec_credito
Revises: 20260919_wh_secret
Create Date: 2026-10-04

Mesmo desenho de `reconciliacao_estoque_pendente`/`reconciliacao_motivo`, mas
dedicada: uma venda fiada pode ficar com o débito de crédito indeterminado
(timeout/5xx do serviço de clientes) ao mesmo tempo que a baixa de estoque foi
clara, ou vice-versa — reusar o par de colunas de estoque sobrescreveria o
motivo de um com o do outro.

Colunas novas, não nulas com default, sem backfill de dado — nenhuma venda
existente tem um débito de crédito pendente de reconciliar.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20261004_rec_credito'
down_revision = '20260919_wh_secret'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'vendas',
        sa.Column('reconciliacao_credito_pendente', sa.Boolean(), nullable=False, server_default=sa.false()),
        schema='vendas',
    )
    op.add_column(
        'vendas',
        sa.Column('reconciliacao_credito_motivo', sa.Text(), nullable=True),
        schema='vendas',
    )


def downgrade() -> None:
    op.drop_column('vendas', 'reconciliacao_credito_motivo', schema='vendas')
    op.drop_column('vendas', 'reconciliacao_credito_pendente', schema='vendas')
