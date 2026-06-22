"""add historico status venda

Revision ID: 20260622_175701
Revises: 20260612_020300
Create Date: 2026-06-22 17:57:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260622_175701'
down_revision = '20260611_loja_mvp'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona tabela de histórico de status para auditoria completa
    de mudanças de status nas vendas.
    """
    # Criar tabela de histórico
    op.create_table(
        'historico_status_venda',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('venda_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status_anterior', sa.String(20), nullable=True),
        sa.Column('status_novo', sa.String(20), nullable=False),
        sa.Column('alterado_por', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alterado_em', sa.TIMESTAMP, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('observacao', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['venda_id'], ['vendas.id'], ondelete='CASCADE'),
        schema='vendas'
    )
    
    # Criar índices
    op.create_index(
        'ix_historico_status_venda_id',
        'historico_status_venda',
        ['venda_id'],
        schema='vendas'
    )
    op.create_index(
        'ix_historico_status_alterado_em',
        'historico_status_venda',
        ['alterado_em'],
        schema='vendas'
    )
    op.create_index(
        'ix_historico_status_status_novo',
        'historico_status_venda',
        ['status_novo'],
        schema='vendas'
    )


def downgrade() -> None:
    """Remove tabela de histórico de status."""
    op.drop_index('ix_historico_status_status_novo', table_name='historico_status_venda', schema='vendas')
    op.drop_index('ix_historico_status_alterado_em', table_name='historico_status_venda', schema='vendas')
    op.drop_index('ix_historico_status_venda_id', table_name='historico_status_venda', schema='vendas')
    op.drop_table('historico_status_venda', schema='vendas')
