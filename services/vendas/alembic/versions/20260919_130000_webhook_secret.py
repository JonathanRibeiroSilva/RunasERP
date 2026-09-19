"""segredo de assinatura do webhook do Mercado Pago, por tenant

Revision ID: 20260919_wh_secret
Revises: 20260828_aud_vendas
Create Date: 2026-09-19

Coluna nova, anulável, sem backfill: ninguém tem o segredo ainda. Enquanto
estiver vazia a rota do webhook segue aberta (routers/webhook.py) — fechar
para todo mundo de uma vez derrubaria a confirmação de pagamento de quem
ainda não colou o segredo do painel do MP.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260919_wh_secret'
down_revision = '20260828_aud_vendas'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'configuracoes_pagamento',
        sa.Column('mercadopago_webhook_secret_enc', sa.Text(), nullable=True),
        schema='vendas',
    )


def downgrade() -> None:
    op.drop_column('configuracoes_pagamento', 'mercadopago_webhook_secret_enc', schema='vendas')
