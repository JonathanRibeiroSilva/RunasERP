"""assinaturas da plataforma (Mercado Pago Preapproval)

Revision ID: 20260828_assin
Revises: 20260828_aud_gatewa
Create Date: 2026-08-28

Conta do MP do DONO DA PLATAFORMA, sem relação alguma com
vendas.configuracoes_pagamento, que é a conta de cada lojista. São dois
Mercado Pagos diferentes no mesmo sistema — o prefixo PLATAFORMA_ na
credencial e o schema gateway nesta tabela existem para ninguém confundir.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260828_assin'
down_revision = '20260828_aud_gatewa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'assinaturas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('plano', sa.String(length=50), nullable=False),
        sa.Column('valor', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('mp_preapproval_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDENTE'),
        sa.Column('vence_em', sa.Date(), nullable=True),
        # Depois de vence_em e antes de carencia_ate nada muda: um atraso de dois
        # dias não pode virar cancelamento de cliente.
        sa.Column('carencia_ate', sa.Date(), nullable=True),
        # Marca o estágio intermediário: lê tudo, não escreve nada.
        sa.Column('somente_leitura_desde', sa.Date(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('empresa_id'),
        schema='gateway',
    )

    # Idempotência do webhook, no mesmo espírito de vendas.webhooks_processados:
    # o MP reenvia o mesmo evento, e processar duas vezes empurraria o
    # vencimento duas vezes.
    op.create_table(
        'webhooks_plataforma',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evento_id', sa.String(length=100), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=True),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('processado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evento_id'),
        schema='gateway',
    )


def downgrade() -> None:
    op.drop_table('webhooks_plataforma', schema='gateway')
    op.drop_table('assinaturas', schema='gateway')
