"""add loja online mvp infrastructure

Revision ID: 20260611_loja_mvp
Revises: 20260609_initial
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '20260611_loja_mvp'
down_revision = '20260609_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adiciona infraestrutura para Loja Online MVP."""
    
    # ========== ALTERAR TABELA VENDAS ==========
    # Adicionar novos campos para Mercado Pago
    op.add_column('vendas', sa.Column('mercadopago_preference_id', sa.String(100), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('mercadopago_payment_id', sa.String(100), nullable=True), schema='vendas')
    
    # Adicionar valor do frete
    op.add_column('vendas', sa.Column('valor_frete', sa.Numeric(10, 2), nullable=False, server_default='0.0'), schema='vendas')
    
    # Adicionar dados do cliente convidado
    op.add_column('vendas', sa.Column('cliente_convidado_nome', sa.String(200), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('cliente_convidado_telefone', sa.String(20), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('cliente_convidado_email', sa.String(200), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('cliente_convidado_cpf', sa.String(11), nullable=True), schema='vendas')
    
    # Adicionar endereço de entrega
    op.add_column('vendas', sa.Column('endereco_logradouro', sa.String(200), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('endereco_numero', sa.String(20), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('endereco_complemento', sa.String(100), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('endereco_bairro', sa.String(100), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('endereco_cidade', sa.String(100), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('endereco_estado', sa.String(2), nullable=True), schema='vendas')
    op.add_column('vendas', sa.Column('endereco_cep', sa.String(8), nullable=True), schema='vendas')
    
    # Criar índices para novos campos
    op.create_index('ix_vendas_mp_preference', 'vendas', ['mercadopago_preference_id'], schema='vendas')
    op.create_index('ix_vendas_mp_payment', 'vendas', ['mercadopago_payment_id'], schema='vendas')
    
    # ========== CRIAR TABELA RESERVAS_TEMPORARIAS ==========
    op.create_table(
        'reservas_temporarias',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('produto_id', UUID(as_uuid=True), nullable=False),
        sa.Column('variante_id', UUID(as_uuid=True), nullable=True),
        sa.Column('quantidade', sa.Numeric(10, 3), nullable=False),
        sa.Column('sessao_id', sa.String(255), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('expira_em', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='vendas'
    )
    
    # Índices
    op.create_index('ix_reservas_temp_id', 'reservas_temporarias', ['id'], schema='vendas')
    op.create_index('ix_reservas_temp_produto', 'reservas_temporarias', ['produto_id', 'variante_id'], schema='vendas')
    op.create_index('ix_reservas_temp_sessao', 'reservas_temporarias', ['sessao_id'], schema='vendas')
    op.create_index('ix_reservas_temp_expira', 'reservas_temporarias', ['expira_em'], schema='vendas')
    op.create_index('ix_reservas_temp_empresa', 'reservas_temporarias', ['empresa_id'], schema='vendas')
    
    # ========== CRIAR TABELA WEBHOOKS_PROCESSADOS ==========
    op.create_table(
        'webhooks_processados',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_id', sa.String(100), nullable=False, unique=True),
        sa.Column('tipo_evento', sa.String(50), nullable=False),
        sa.Column('venda_id', UUID(as_uuid=True), nullable=True),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('processado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='vendas'
    )
    
    # Índices
    op.create_index('ix_webhooks_id', 'webhooks_processados', ['id'], schema='vendas')
    op.create_index('ix_webhooks_payment_id', 'webhooks_processados', ['payment_id'], schema='vendas', unique=True)
    op.create_index('ix_webhooks_tipo', 'webhooks_processados', ['tipo_evento'], schema='vendas')
    op.create_index('ix_webhooks_venda', 'webhooks_processados', ['venda_id'], schema='vendas')
    
    # ========== CRIAR TABELA CONFIGURACOES_PAGAMENTO ==========
    op.create_table(
        'configuracoes_pagamento',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('mercadopago_access_token', sa.String(255), nullable=True),
        sa.Column('mercadopago_public_key', sa.String(255), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='vendas'
    )
    
    # Índices
    op.create_index('ix_config_pag_id', 'configuracoes_pagamento', ['id'], schema='vendas')
    op.create_index('ix_config_pag_empresa', 'configuracoes_pagamento', ['empresa_id'], schema='vendas', unique=True)
    
    # ========== CRIAR TABELA FAIXAS_ENTREGA ==========
    op.create_table(
        'faixas_entrega',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('bairro', sa.String(100), nullable=False),
        sa.Column('taxa', sa.Numeric(10, 2), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='vendas'
    )
    
    # Unique constraint
    op.create_unique_constraint(
        'uq_faixa_empresa_bairro',
        'faixas_entrega',
        ['empresa_id', 'bairro'],
        schema='vendas'
    )
    
    # Índices
    op.create_index('ix_faixa_id', 'faixas_entrega', ['id'], schema='vendas')
    op.create_index('ix_faixa_empresa', 'faixas_entrega', ['empresa_id'], schema='vendas')
    op.create_index('ix_faixa_bairro', 'faixas_entrega', ['bairro'], schema='vendas')
    
    # ========== CRIAR TABELA CONFIGURACOES_LOJA ==========
    op.create_table(
        'configuracoes_loja',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('taxa_entrega_padrao', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('cobrar_taxa_entrega', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='vendas'
    )
    
    # Índices
    op.create_index('ix_config_loja_id', 'configuracoes_loja', ['id'], schema='vendas')
    op.create_index('ix_config_loja_empresa', 'configuracoes_loja', ['empresa_id'], schema='vendas', unique=True)
    
    # ========== CRIAR TABELA HISTORICO_STATUS_VENDA ==========
    op.create_table(
        'historico_status_venda',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('venda_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status_anterior', sa.String(20), nullable=True),
        sa.Column('status_novo', sa.String(20), nullable=False),
        sa.Column('alterado_por', UUID(as_uuid=True), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('alterado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='vendas'
    )
    
    # Índices
    op.create_index('ix_historico_id', 'historico_status_venda', ['id'], schema='vendas')
    op.create_index('ix_historico_venda', 'historico_status_venda', ['venda_id'], schema='vendas')
    op.create_index('ix_historico_data', 'historico_status_venda', ['alterado_em'], schema='vendas')


def downgrade() -> None:
    """Remove infraestrutura da Loja Online MVP."""
    
    # ========== REMOVER TABELAS ==========
    op.drop_table('historico_status_venda', schema='vendas')
    op.drop_table('configuracoes_loja', schema='vendas')
    op.drop_table('faixas_entrega', schema='vendas')
    op.drop_table('configuracoes_pagamento', schema='vendas')
    op.drop_table('webhooks_processados', schema='vendas')
    op.drop_table('reservas_temporarias', schema='vendas')
    
    # ========== REMOVER COLUNAS DA TABELA VENDAS ==========
    op.drop_index('ix_vendas_mp_payment', table_name='vendas', schema='vendas')
    op.drop_index('ix_vendas_mp_preference', table_name='vendas', schema='vendas')
    
    op.drop_column('vendas', 'endereco_cep', schema='vendas')
    op.drop_column('vendas', 'endereco_estado', schema='vendas')
    op.drop_column('vendas', 'endereco_cidade', schema='vendas')
    op.drop_column('vendas', 'endereco_bairro', schema='vendas')
    op.drop_column('vendas', 'endereco_complemento', schema='vendas')
    op.drop_column('vendas', 'endereco_numero', schema='vendas')
    op.drop_column('vendas', 'endereco_logradouro', schema='vendas')
    op.drop_column('vendas', 'cliente_convidado_cpf', schema='vendas')
    op.drop_column('vendas', 'cliente_convidado_email', schema='vendas')
    op.drop_column('vendas', 'cliente_convidado_telefone', schema='vendas')
    op.drop_column('vendas', 'cliente_convidado_nome', schema='vendas')
    op.drop_column('vendas', 'valor_frete', schema='vendas')
    op.drop_column('vendas', 'mercadopago_payment_id', schema='vendas')
    op.drop_column('vendas', 'mercadopago_preference_id', schema='vendas')
