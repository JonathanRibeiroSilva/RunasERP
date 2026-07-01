"""add reconciliacao_estoque fields to vendas

Revision ID: 20260627_reconcil
Revises: 20260625_230655
Create Date: 2026-06-27

C4 — Cross-service consistency. Quando o pagamento é aprovado mas a baixa de estoque
retorna resultado indeterminado (timeout/erro), a venda NÃO é cancelada: é marcada para
reconciliação assíncrona (job reconciliar_estoque_vendas).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260627_reconcil'
down_revision = '20260625_230655'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'vendas',
        sa.Column(
            'reconciliacao_estoque_pendente',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
        schema='vendas'
    )
    op.add_column(
        'vendas',
        sa.Column('reconciliacao_motivo', sa.Text(), nullable=True),
        schema='vendas'
    )
    # Index parcial: o job só varre vendas marcadas (poucas), evitando full scan.
    op.create_index(
        'ix_vendas_reconciliacao_pendente',
        'vendas',
        ['reconciliacao_estoque_pendente'],
        unique=False,
        schema='vendas',
        postgresql_where=sa.text('reconciliacao_estoque_pendente'),
    )


def downgrade() -> None:
    op.drop_index('ix_vendas_reconciliacao_pendente', table_name='vendas', schema='vendas')
    op.drop_column('vendas', 'reconciliacao_motivo', schema='vendas')
    op.drop_column('vendas', 'reconciliacao_estoque_pendente', schema='vendas')
