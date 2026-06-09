"""initial vendas with multi-tenancy

Revision ID: 20260609_initial
Revises: 
Create Date: 2026-06-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '20260609_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria schema e tabelas de vendas com multi-tenancy."""
    
    # ========== CRIAR SCHEMA ==========
    op.execute('CREATE SCHEMA IF NOT EXISTS vendas')
    
    # ========== CRIAR TABELA VENDAS ==========
    op.create_table(
        'vendas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('numero_venda', sa.String(50), nullable=False),
        sa.Column('cliente_id', UUID(as_uuid=True), nullable=True),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('desconto_tipo', sa.String(20), nullable=True),
        sa.Column('desconto_valor', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('valor_total', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='PEDIDO'),
        sa.Column('tipo_entrega', sa.String(20), nullable=False, server_default='RETIRADA'),
        sa.Column('data_pedido', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('data_confirmacao', sa.DateTime(), nullable=True),
        sa.Column('data_separacao', sa.DateTime(), nullable=True),
        sa.Column('data_entregue', sa.DateTime(), nullable=True),
        sa.Column('data_finalizada', sa.DateTime(), nullable=True),
        sa.Column('data_cancelada', sa.DateTime(), nullable=True),
        sa.Column('motivo_cancelamento', sa.Text(), nullable=True),
        sa.Column('cancelada_por', UUID(as_uuid=True), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='vendas'
    )
    
    # ========== CRIAR TABELA ITENS_VENDA ==========
    op.create_table(
        'itens_venda',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('venda_id', UUID(as_uuid=True), nullable=False),
        sa.Column('produto_id', UUID(as_uuid=True), nullable=False),
        sa.Column('variante_id', UUID(as_uuid=True), nullable=True),
        sa.Column('codigo_produto', sa.String(100), nullable=True),
        sa.Column('descricao_produto', sa.String(500), nullable=False),
        sa.Column('quantidade', sa.Numeric(10, 3), nullable=False),
        sa.Column('preco_unitario', sa.Numeric(10, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('estoque_reservado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('estoque_baixado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['venda_id'], ['vendas.vendas.id'], ondelete='CASCADE'),
        schema='vendas'
    )
    
    # ========== CRIAR TABELA PAGAMENTOS_VENDA ==========
    op.create_table(
        'pagamentos_venda',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('venda_id', UUID(as_uuid=True), nullable=False),
        sa.Column('forma_pagamento', sa.String(20), nullable=False),
        sa.Column('valor_pago', sa.Numeric(10, 2), nullable=False),
        sa.Column('valor_recebido', sa.Numeric(10, 2), nullable=True),
        sa.Column('valor_troco', sa.Numeric(10, 2), nullable=True),
        sa.Column('gera_conta_receber', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('conta_receber_id', UUID(as_uuid=True), nullable=True),
        sa.Column('comprovante', sa.String(200), nullable=True),
        sa.Column('data_pagamento', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['venda_id'], ['vendas.vendas.id'], ondelete='CASCADE'),
        schema='vendas'
    )
    
    # ========== CRIAR TABELA RESERVAS_ESTOQUE_VENDA ==========
    op.create_table(
        'reservas_estoque_venda',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('venda_id', UUID(as_uuid=True), nullable=False),
        sa.Column('item_venda_id', UUID(as_uuid=True), nullable=False),
        sa.Column('produto_id', UUID(as_uuid=True), nullable=False),
        sa.Column('variante_id', UUID(as_uuid=True), nullable=True),
        sa.Column('quantidade_reservada', sa.Numeric(10, 3), nullable=False),
        sa.Column('reservada_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('liberada_em', sa.DateTime(), nullable=True),
        sa.Column('baixada_em', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='RESERVADA'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['venda_id'], ['vendas.vendas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_venda_id'], ['vendas.itens_venda.id'], ondelete='CASCADE'),
        schema='vendas'
    )
    
    # ========== CRIAR UNIQUE CONSTRAINTS ==========
    op.create_unique_constraint(
        'uq_vendas_empresa_numero',
        'vendas',
        ['empresa_id', 'numero_venda'],
        schema='vendas'
    )
    
    # ========== CRIAR INDEXES PARA PERFORMANCE ==========
    
    # Vendas
    op.create_index('ix_vendas_empresa_id', 'vendas', ['empresa_id'], schema='vendas')
    op.create_index('ix_vendas_empresa_id_status', 'vendas', ['empresa_id', 'status'], schema='vendas')
    op.create_index('ix_vendas_empresa_id_cliente', 'vendas', ['empresa_id', 'cliente_id'], schema='vendas')
    op.create_index('ix_vendas_empresa_id_data', 'vendas', ['empresa_id', 'data_pedido'], schema='vendas')
    op.create_index('ix_vendas_id', 'vendas', ['id'], schema='vendas')
    op.create_index('ix_vendas_numero', 'vendas', ['numero_venda'], schema='vendas')
    op.create_index('ix_vendas_status', 'vendas', ['status'], schema='vendas')
    op.create_index('ix_vendas_cliente', 'vendas', ['cliente_id'], schema='vendas')
    
    # Itens Venda
    op.create_index('ix_itens_venda_id', 'itens_venda', ['id'], schema='vendas')
    op.create_index('ix_itens_venda_venda_id', 'itens_venda', ['venda_id'], schema='vendas')
    op.create_index('ix_itens_venda_produto', 'itens_venda', ['produto_id'], schema='vendas')
    op.create_index('ix_itens_venda_variante', 'itens_venda', ['variante_id'], schema='vendas')
    
    # Pagamentos Venda
    op.create_index('ix_pagamentos_venda_id', 'pagamentos_venda', ['id'], schema='vendas')
    op.create_index('ix_pagamentos_venda_venda_id', 'pagamentos_venda', ['venda_id'], schema='vendas')
    op.create_index('ix_pagamentos_forma', 'pagamentos_venda', ['forma_pagamento'], schema='vendas')
    
    # Reservas Estoque
    op.create_index('ix_reservas_id', 'reservas_estoque_venda', ['id'], schema='vendas')
    op.create_index('ix_reservas_venda_id', 'reservas_estoque_venda', ['venda_id'], schema='vendas')
    op.create_index('ix_reservas_item_venda_id', 'reservas_estoque_venda', ['item_venda_id'], schema='vendas')
    op.create_index('ix_reservas_produto', 'reservas_estoque_venda', ['produto_id', 'variante_id'], schema='vendas')
    op.create_index('ix_reservas_status', 'reservas_estoque_venda', ['status'], schema='vendas')


def downgrade() -> None:
    """Remove schema e tabelas de vendas."""
    
    # ========== REMOVER INDEXES ==========
    op.drop_index('ix_reservas_status', table_name='reservas_estoque_venda', schema='vendas')
    op.drop_index('ix_reservas_produto', table_name='reservas_estoque_venda', schema='vendas')
    op.drop_index('ix_reservas_item_venda_id', table_name='reservas_estoque_venda', schema='vendas')
    op.drop_index('ix_reservas_venda_id', table_name='reservas_estoque_venda', schema='vendas')
    op.drop_index('ix_reservas_id', table_name='reservas_estoque_venda', schema='vendas')
    
    op.drop_index('ix_pagamentos_forma', table_name='pagamentos_venda', schema='vendas')
    op.drop_index('ix_pagamentos_venda_venda_id', table_name='pagamentos_venda', schema='vendas')
    op.drop_index('ix_pagamentos_venda_id', table_name='pagamentos_venda', schema='vendas')
    
    op.drop_index('ix_itens_venda_variante', table_name='itens_venda', schema='vendas')
    op.drop_index('ix_itens_venda_produto', table_name='itens_venda', schema='vendas')
    op.drop_index('ix_itens_venda_venda_id', table_name='itens_venda', schema='vendas')
    op.drop_index('ix_itens_venda_id', table_name='itens_venda', schema='vendas')
    
    op.drop_index('ix_vendas_cliente', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_status', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_numero', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_id', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_empresa_id_data', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_empresa_id_cliente', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_empresa_id_status', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_empresa_id', table_name='vendas', schema='vendas')
    
    # ========== REMOVER UNIQUE CONSTRAINTS ==========
    op.drop_constraint('uq_vendas_empresa_numero', 'vendas', schema='vendas', type_='unique')
    
    # ========== REMOVER TABELAS ==========
    op.drop_table('reservas_estoque_venda', schema='vendas')
    op.drop_table('pagamentos_venda', schema='vendas')
    op.drop_table('itens_venda', schema='vendas')
    op.drop_table('vendas', schema='vendas')
    
    # ========== REMOVER SCHEMA ==========
    op.execute('DROP SCHEMA IF EXISTS vendas CASCADE')
