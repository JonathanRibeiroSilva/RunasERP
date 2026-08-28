"""add SUPER_ADMIN role and make usuarios.empresa_id nullable

Revision ID: 20260828_100000
Revises: 20260612_120000
Create Date: 2026-08-28 10:00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260828_100000'
down_revision = '20260612_120000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """SUPER_ADMIN não tem tenant: empresa_id nulo é a marca dele.

    O valor novo do ENUM não pode ser usado na mesma transação que o adiciona
    (PG>=12); esta migration só declara — o seed do super admin roda depois,
    no startup, fora desta transação.
    """
    op.execute("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")
    op.alter_column('usuarios', 'empresa_id', schema='gateway', nullable=True)


def downgrade() -> None:
    """Só reverte a nulabilidade: remover valor de ENUM exige recriar o tipo."""
    op.alter_column('usuarios', 'empresa_id', schema='gateway', nullable=False)
