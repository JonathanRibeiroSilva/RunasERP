"""initial empresas state

Revision ID: 20260611_empresas
Revises: 
Create Date: 2026-06-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260611_empresas'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migration inicial do serviço Empresas.
    
    Esta migration apenas marca o estado inicial do banco.
    A tabela empresas já existe no schema public (criada por create_all()).
    
    Futuras alterações devem ser feitas através de migrations incrementais.
    """
    pass


def downgrade() -> None:
    """Rollback não suportado para migration inicial."""
    pass
