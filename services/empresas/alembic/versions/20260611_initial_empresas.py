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
    Cria a tabela empresas no schema empresas.
    """
    op.create_table(
        'empresas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False, comment='Slug único para URL do catálogo'),
        sa.Column('razao_social', sa.String(length=200), nullable=False, comment='Razão social da empresa'),
        sa.Column('nome_fantasia', sa.String(length=200), nullable=False, comment='Nome fantasia da empresa'),
        sa.Column('tipo', sa.String(length=20), nullable=False, server_default='MATRIZ'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ATIVA'),
        sa.Column('cnpj', sa.String(length=18), nullable=False, comment='CNPJ formatado'),
        sa.Column('inscricao_estadual', sa.String(length=20), nullable=True),
        sa.Column('inscricao_municipal', sa.String(length=20), nullable=True),
        sa.Column('regime_tributario', sa.String(length=50), nullable=False, server_default='SIMPLES_NACIONAL'),
        sa.Column('cep', sa.String(length=9), nullable=False),
        sa.Column('logradouro', sa.String(length=200), nullable=False),
        sa.Column('numero', sa.String(length=20), nullable=False),
        sa.Column('complemento', sa.String(length=100), nullable=True),
        sa.Column('bairro', sa.String(length=100), nullable=False),
        sa.Column('cidade', sa.String(length=100), nullable=False),
        sa.Column('uf', sa.String(length=2), nullable=False),
        sa.Column('telefone', sa.String(length=20), nullable=True),
        sa.Column('celular', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('site', sa.String(length=200), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True, comment='URL da logo da empresa'),
        sa.Column('cor_primaria', sa.String(length=7), nullable=True, server_default='#3B82F6'),
        sa.Column('cor_secundaria', sa.String(length=7), nullable=True, server_default='#10B981'),
        sa.Column('catalogo_ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('catalogo_titulo', sa.String(length=200), nullable=True),
        sa.Column('catalogo_descricao', sa.Text(), nullable=True),
        sa.Column('catalogo_whatsapp', sa.String(length=20), nullable=True),
        sa.Column('plano', sa.String(length=50), nullable=False, server_default='BASICO'),
        sa.Column('max_usuarios', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_produtos', sa.Integer(), nullable=True),
        sa.Column('max_lojas', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('empresa_matriz_id', sa.Integer(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('criado_por', sa.Integer(), nullable=True),
        sa.Column('atualizado_por', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('cnpj'),
        schema='empresas'
    )
    op.create_index(op.f('ix_empresas_empresas_slug'), 'empresas', ['slug'], unique=False, schema='empresas')
    op.create_index(op.f('ix_empresas_empresas_cnpj'), 'empresas', ['cnpj'], unique=False, schema='empresas')
    op.create_index(op.f('ix_empresas_empresas_ativo'), 'empresas', ['ativo'], unique=False, schema='empresas')


def downgrade() -> None:
    """Rollback da migration inicial."""
    op.drop_index(op.f('ix_empresas_empresas_ativo'), table_name='empresas', schema='empresas')
    op.drop_index(op.f('ix_empresas_empresas_cnpj'), table_name='empresas', schema='empresas')
    op.drop_index(op.f('ix_empresas_empresas_slug'), table_name='empresas', schema='empresas')
    op.drop_table('empresas', schema='empresas')
