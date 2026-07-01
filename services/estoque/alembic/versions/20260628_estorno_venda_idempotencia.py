"""add estornos_venda_processados ledger for inventory reversal idempotency

Revision ID: 20260628_estorno_idem
Revises: 20260627_baixa_idem
Create Date: 2026-06-28

D2 — Inventory reversal (refund) idempotency. Ledger keyed by (empresa_id, documento)
where documento == numero_venda. The unique constraint is the DB-level idempotency gate
that guarantees a refunded sale's stock is restored exactly once under concurrency
(duplicate/redelivered Mercado Pago refund webhooks collide on the unique index).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260628_estorno_idem'
down_revision = '20260627_baixa_idem'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'estornos_venda_processados',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('documento', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('empresa_id', 'documento', name='uq_estorno_venda_empresa_documento'),
        schema='estoque'
    )
    op.create_index(
        'ix_estorno_venda_empresa_documento',
        'estornos_venda_processados',
        ['empresa_id', 'documento'],
        schema='estoque'
    )


def downgrade() -> None:
    op.drop_index('ix_estorno_venda_empresa_documento',
                  table_name='estornos_venda_processados', schema='estoque')
    op.drop_table('estornos_venda_processados', schema='estoque')
