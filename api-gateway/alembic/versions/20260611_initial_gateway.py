"""initial gateway

Revision ID: 20260611_gateway
Revises: 
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260611_gateway'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Cria a tabela gateway.usuarios.

    Em bancos criados antes desta migration (via create_all legado) a tabela
    já existe e este passo vira no-op; em um banco novo (ex.: deploy em VPS)
    a tabela é criada aqui, evitando falha na migration seguinte.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names(schema='gateway')

    if 'usuarios' not in existing_tables:
        role_enum = postgresql.ENUM('ADMIN', 'OPERADOR', name='roleenum')
        role_enum.create(conn, checkfirst=True)

        op.create_table(
            'usuarios',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('nome', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('senha_hash', sa.String(length=255), nullable=False),
            sa.Column('role', postgresql.ENUM('ADMIN', 'OPERADOR', name='roleenum', create_type=False), nullable=False),
            sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            schema='gateway'
        )
        op.create_index(op.f('ix_gateway_usuarios_email'), 'usuarios', ['email'], unique=True, schema='gateway')


def downgrade() -> None:
    """Remove a tabela gateway.usuarios (se existir)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names(schema='gateway')

    if 'usuarios' in existing_tables:
        op.drop_index(op.f('ix_gateway_usuarios_email'), table_name='usuarios', schema='gateway')
        op.drop_table('usuarios', schema='gateway')
        postgresql.ENUM(name='roleenum').drop(conn, checkfirst=True)
