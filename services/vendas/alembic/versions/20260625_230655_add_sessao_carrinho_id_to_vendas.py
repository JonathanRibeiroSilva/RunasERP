"""add sessao_carrinho_id to vendas

Revision ID: 20260625_230655
Revises: 20260622_175701
Create Date: 2026-06-25 23:06:55

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260625_230655'
down_revision = '20260622_175701'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona campo sessao_carrinho_id à tabela vendas.
    
    Este campo armazena o ID da sessão do carrinho Redis que originou a venda.
    Permite limpar o carrinho correto quando o pagamento for confirmado via webhook.
    """
    op.add_column(
        'vendas',
        sa.Column(
            'sessao_carrinho_id',
            sa.String(100),
            nullable=True,
            comment='ID da sessão do carrinho Redis'
        ),
        schema='vendas'
    )


def downgrade() -> None:
    """Remove campo sessao_carrinho_id da tabela vendas."""
    op.drop_column('vendas', 'sessao_carrinho_id', schema='vendas')
