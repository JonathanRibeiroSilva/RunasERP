"""add baixas_venda_processadas ledger for inventory deduction idempotency

Revision ID: 20260627_baixa_idem
Revises: 20260609_multitenancy
Create Date: 2026-06-27

C1 — Inventory deduction idempotency. Ledger keyed by (empresa_id, documento) where
documento == numero_venda. The unique constraint is the DB-level idempotency gate that
guarantees a sale's stock is deducted exactly once under concurrency.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260627_baixa_idem'
down_revision = '20260609_multitenancy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'baixas_venda_processadas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('documento', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('empresa_id', 'documento', name='uq_baixa_venda_empresa_documento'),
        schema='estoque'
    )
    op.create_index(
        'ix_baixa_venda_empresa_documento',
        'baixas_venda_processadas',
        ['empresa_id', 'documento'],
        schema='estoque'
    )


def downgrade() -> None:
    op.drop_index('ix_baixa_venda_empresa_documento',
                  table_name='baixas_venda_processadas', schema='estoque')
    op.drop_table('baixas_venda_processadas', schema='estoque')
