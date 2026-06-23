"""rename catalogo to loja_online

Revision ID: 20260623_loja_online
Revises: 20260612_add_campos_essenciais
Create Date: 2026-06-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260623_loja_online'
down_revision = '20260612_add_campos_essenciais'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Renomeia tabelas e relacionamentos de 'catalogo' para 'loja_online'.
    
    Mudanças:
    1. Renomeia tabela catalogo_config para loja_online_config
    2. Renomeia tabela catalogo_fotos para loja_online_fotos
    """
    # Renomear tabelas
    op.rename_table(
        'catalogo_config',
        'loja_online_config',
        schema='produtos'
    )
    
    op.rename_table(
        'catalogo_fotos',
        'loja_online_fotos',
        schema='produtos'
    )
    
    print("✅ Tabelas renomeadas: catalogo_* → loja_online_*")


def downgrade() -> None:
    """
    Reverte as mudanças renomeando de volta para 'catalogo'.
    """
    # Renomear de volta
    op.rename_table(
        'loja_online_fotos',
        'catalogo_fotos',
        schema='produtos'
    )
    
    op.rename_table(
        'loja_online_config',
        'catalogo_config',
        schema='produtos'
    )
    
    print("⚠️  Tabelas revertidas: loja_online_* → catalogo_*")
