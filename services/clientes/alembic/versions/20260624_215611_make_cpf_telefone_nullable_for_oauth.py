"""make cpf and telefone nullable for oauth

Revision ID: 20260624_215611
Revises: 20260622_175701
Create Date: 2026-06-24 21:56:11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260624_215611'
down_revision = '20260622_175701'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Torna CPF e telefone opcionais para suportar clientes OAuth."""
    # Tornar cpf nullable
    op.alter_column(
        'clientes',
        'cpf',
        existing_type=sa.String(11),
        nullable=True,
        schema='clientes'
    )
    
    # Tornar telefone nullable
    op.alter_column(
        'clientes',
        'telefone',
        existing_type=sa.String(20),
        nullable=True,
        schema='clientes'
    )
    
    # Remover a constraint única de empresa_id + cpf e recriar permitindo NULL
    op.drop_constraint('uq_clientes_empresa_cpf', 'clientes', schema='clientes', type_='unique')
    
    # Recriar a constraint única apenas para cpf não-nulos
    # Nota: PostgreSQL trata NULL como valores distintos em unique constraints,
    # então múltiplos clientes OAuth (cpf=NULL) da mesma empresa são permitidos
    op.create_unique_constraint(
        'uq_clientes_empresa_cpf',
        'clientes',
        ['empresa_id', 'cpf'],
        schema='clientes'
    )


def downgrade() -> None:
    """Reverte CPF e telefone para obrigatórios."""
    # Nota: Este downgrade falhará se houver clientes OAuth com cpf/telefone NULL
    op.alter_column(
        'clientes',
        'cpf',
        existing_type=sa.String(11),
        nullable=False,
        schema='clientes'
    )
    
    op.alter_column(
        'clientes',
        'telefone',
        existing_type=sa.String(20),
        nullable=False,
        schema='clientes'
    )
