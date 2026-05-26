"""Migração para UUID em todas as tabelas

Revision ID: 001_migrate_to_uuid
Revises: 
Create Date: 2026-05-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_migrate_to_uuid'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Migração para UUID."""
    
    # Habilitar extensão UUID se não estiver habilitada
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # ==================== CRIAR NOVAS TABELAS COM UUID ====================
    
    # Tabela: estoque
    op.create_table(
        'estoque',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('produto_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('variante_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('quantidade', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('quantidade_reservada', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('quantidade_disponivel', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('estoque_minimo', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('estoque_maximo', sa.Float(), nullable=True),
        sa.Column('localizacao', sa.String(100), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('ix_estoque_id', 'estoque', ['id'])
    op.create_index('ix_estoque_produto_id', 'estoque', ['produto_id'])
    op.create_index('ix_estoque_variante_id', 'estoque', ['variante_id'])
    
    # Tabela: lotes
    op.create_table(
        'lotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('estoque_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('estoque.id'), nullable=False, index=True),
        sa.Column('codigo', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('quantidade', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('quantidade_inicial', sa.Float(), nullable=False),
        sa.Column('data_fabricacao', sa.Date(), nullable=True),
        sa.Column('data_validade', sa.Date(), nullable=True, index=True),
        sa.Column('fornecedor', sa.String(200), nullable=True),
        sa.Column('nota_fiscal', sa.String(100), nullable=True),
        sa.Column('custo_unitario', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ATIVO', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('ix_lotes_id', 'lotes', ['id'])
    op.create_index('ix_lotes_estoque_id', 'lotes', ['estoque_id'])
    op.create_index('ix_lotes_codigo', 'lotes', ['codigo'])
    op.create_index('ix_lotes_data_validade', 'lotes', ['data_validade'])
    op.create_index('ix_lotes_status', 'lotes', ['status'])
    
    # Tabela: movimentacoes
    op.create_table(
        'movimentacoes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('estoque_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('estoque.id'), nullable=False, index=True),
        sa.Column('lote_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lotes.id'), nullable=True, index=True),
        sa.Column('tipo', sa.String(20), nullable=False, index=True),
        sa.Column('quantidade', sa.Float(), nullable=False),
        sa.Column('quantidade_anterior', sa.Float(), nullable=False),
        sa.Column('quantidade_posterior', sa.Float(), nullable=False),
        sa.Column('motivo', sa.String(200), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('documento', sa.String(100), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('custo_unitario', sa.Float(), nullable=True),
        sa.Column('custo_total', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True)
    )
    op.create_index('ix_movimentacoes_id', 'movimentacoes', ['id'])
    op.create_index('ix_movimentacoes_estoque_id', 'movimentacoes', ['estoque_id'])
    op.create_index('ix_movimentacoes_lote_id', 'movimentacoes', ['lote_id'])
    op.create_index('ix_movimentacoes_tipo', 'movimentacoes', ['tipo'])
    op.create_index('ix_movimentacoes_created_at', 'movimentacoes', ['created_at'])
    
    # Tabela: inventarios
    op.create_table(
        'inventarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('data_inventario', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
        sa.Column('responsavel', sa.String(200), nullable=False),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('finalizado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_finalizacao', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('ix_inventarios_id', 'inventarios', ['id'])
    op.create_index('ix_inventarios_data_inventario', 'inventarios', ['data_inventario'])
    
    # Tabela: itens_inventario
    op.create_table(
        'itens_inventario',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('inventario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventarios.id'), nullable=False, index=True),
        sa.Column('estoque_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('estoque.id'), nullable=False, index=True),
        sa.Column('quantidade_sistema', sa.Float(), nullable=False),
        sa.Column('quantidade_contada', sa.Float(), nullable=False),
        sa.Column('diferenca', sa.Float(), nullable=False),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('ajustado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('ix_itens_inventario_id', 'itens_inventario', ['id'])
    op.create_index('ix_itens_inventario_inventario_id', 'itens_inventario', ['inventario_id'])
    op.create_index('ix_itens_inventario_estoque_id', 'itens_inventario', ['estoque_id'])


def downgrade() -> None:
    """Reverter migração."""
    
    # Remover tabelas na ordem inversa (respeitando foreign keys)
    op.drop_table('itens_inventario')
    op.drop_table('inventarios')
    op.drop_table('movimentacoes')
    op.drop_table('lotes')
    op.drop_table('estoque')
