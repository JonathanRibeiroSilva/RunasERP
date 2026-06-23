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
    Migration inicial do Gateway.
    
    A tabela 'usuarios' já existe (foi criada via create_all anteriormente).
    Esta migration apenas marca o estado inicial do schema.
    """
    pass


def downgrade() -> None:
    """Rollback não suportado para migration inicial."""
    pass
