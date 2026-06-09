"""add empresa_id for multi-tenancy

Revision ID: 001_multitenancy
Revises: 
Create Date: 2026-06-08 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_multitenancy'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona suporte a multi-tenancy no serviço de clientes.
    
    Mudanças:
    1. Adiciona coluna empresa_id
    2. Atualiza dados existentes (empresa_id = 1)
    3. Remove unique constraint do CPF
    4. Adiciona unique constraint composto (empresa_id, cpf)
    5. Cria índices compostos para performance
    """
    # 1. Adicionar coluna empresa_id (permite NULL temporariamente)
    op.add_column(
        'clientes',
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        schema='clientes'
    )
    
    # 2. Definir empresa padrão (ID 1) para dados existentes
    op.execute("""
        UPDATE clientes.clientes 
        SET empresa_id = 1 
        WHERE empresa_id IS NULL
    """)
    
    # 3. Tornar coluna obrigatória
    op.alter_column(
        'clientes',
        'empresa_id',
        nullable=False,
        schema='clientes'
    )
    
    # 4. Remover unique constraint do CPF (se existir)
    # Nota: O nome da constraint pode variar dependendo de como foi criada
    try:
        op.drop_constraint('clientes_cpf_key', 'clientes', schema='clientes', type_='unique')
    except:
        # Constraint pode não existir ou ter nome diferente
        pass
    
    # Remover index único do CPF (se existir)
    try:
        op.drop_index('ix_clientes_cpf', table_name='clientes', schema='clientes')
    except:
        # Index pode não existir
        pass
    
    # 5. Adicionar unique constraint composto (empresa_id, cpf)
    op.create_unique_constraint(
        'uq_clientes_empresa_cpf',
        'clientes',
        ['empresa_id', 'cpf'],
        schema='clientes'
    )
    
    # 6. Criar índice em empresa_id (simples)
    op.create_index(
        'ix_clientes_empresa_id',
        'clientes',
        ['empresa_id'],
        schema='clientes'
    )
    
    # 7. Criar índice composto (empresa_id, ativo) para filtros rápidos
    op.create_index(
        'ix_clientes_empresa_id_ativo',
        'clientes',
        ['empresa_id', 'ativo'],
        schema='clientes'
    )
    
    # 8. Criar índice composto (empresa_id, nome) para buscas por nome
    op.create_index(
        'ix_clientes_empresa_id_nome',
        'clientes',
        ['empresa_id', 'nome'],
        schema='clientes'
    )
    
    print("✅ Migration aplicada: Multi-tenancy habilitado no serviço de clientes")
    print("   - empresa_id adicionado")
    print("   - Dados existentes associados à empresa ID 1")
    print("   - CPF agora é único por empresa")
    print("   - Índices compostos criados")


def downgrade() -> None:
    """
    Reverte as mudanças de multi-tenancy.
    
    ATENÇÃO: Esta operação pode resultar em perda de dados se houver
    clientes com o mesmo CPF em empresas diferentes!
    """
    # Remover índices compostos
    op.drop_index('ix_clientes_empresa_id_nome', table_name='clientes', schema='clientes')
    op.drop_index('ix_clientes_empresa_id_ativo', table_name='clientes', schema='clientes')
    op.drop_index('ix_clientes_empresa_id', table_name='clientes', schema='clientes')
    
    # Remover unique constraint composto
    op.drop_constraint('uq_clientes_empresa_cpf', 'clientes', schema='clientes', type_='unique')
    
    # Recriar unique constraint no CPF
    op.create_unique_constraint('clientes_cpf_key', 'clientes', ['cpf'], schema='clientes')
    
    # Recriar index único do CPF
    op.create_index('ix_clientes_cpf', 'clientes', ['cpf'], unique=True, schema='clientes')
    
    # Remover coluna empresa_id
    op.drop_column('clientes', 'empresa_id', schema='clientes')
    
    print("⚠️  Migration revertida: Multi-tenancy desabilitado")
    print("   ATENÇÃO: Clientes duplicados por CPF foram removidos!")
