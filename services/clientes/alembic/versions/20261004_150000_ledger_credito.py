"""ledger de crédito: clientes.movimentos_credito (C1+C2+C3, Onda 6)

Revision ID: 20261004_credito_ledger
Revises: 20260828_aud_client
Create Date: 2026-10-04

`credito_disponivel` era um campo mutado direto, sem histórico: `atualizar_credito`
zerava o saldo devedor a cada edição de limite (C1), `ajustar_credito_disponivel`
não tinha lock nem idempotência (C2), e nada em `vendas` checava o teto antes de
fechar uma venda fiada (C3) — o próprio `/credito/ajustar` não tem UM chamador no
repo hoje. Este ledger substitui o campo mutável como fonte de verdade.

Backfill: uma linha ABERTURA por cliente, valor = `credito_disponivel` de hoje. Não
reconstrói o histórico perdido — veda o saldo atual como ponto de partida, para a
soma do ledger bater com o campo cache a partir de agora.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20261004_credito_ledger'
down_revision = '20260828_aud_client'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'movimentos_credito',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.UUID(), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('valor', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('documento', sa.String(length=100), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.clientes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'empresa_id', 'documento', 'tipo',
            name='uq_movimentos_credito_empresa_documento_tipo'
        ),
        schema='clientes'
    )
    op.create_index(
        'ix_movimentos_credito_empresa_id', 'movimentos_credito', ['empresa_id'],
        unique=False, schema='clientes'
    )
    op.create_index(
        'ix_movimentos_credito_cliente_id', 'movimentos_credito', ['cliente_id'],
        unique=False, schema='clientes'
    )

    # Backfill: linha ABERTURA por cliente. documento determinístico por cliente_id
    # (não por sequência) — reexecutar esta migration numa base que já tem as linhas
    # colide na unique constraint em vez de duplicar saldo de abertura.
    op.execute(
        "INSERT INTO clientes.movimentos_credito "
        "(id, empresa_id, cliente_id, tipo, valor, documento, criado_em) "
        "SELECT gen_random_uuid(), empresa_id, id, 'ABERTURA', credito_disponivel, "
        "'ABERTURA-' || id::text, now() "
        "FROM clientes.clientes"
    )

    op.execute(
        'CREATE TRIGGER trg_auditoria '
        'AFTER INSERT OR UPDATE OR DELETE ON clientes.movimentos_credito '
        'FOR EACH ROW EXECUTE FUNCTION gateway.auditar_registro()'
    )


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS trg_auditoria ON clientes.movimentos_credito')
    op.drop_index('ix_movimentos_credito_cliente_id', table_name='movimentos_credito', schema='clientes')
    op.drop_index('ix_movimentos_credito_empresa_id', table_name='movimentos_credito', schema='clientes')
    op.drop_table('movimentos_credito', schema='clientes')
