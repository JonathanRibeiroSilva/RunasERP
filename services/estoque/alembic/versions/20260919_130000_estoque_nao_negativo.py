"""estoque nunca negativo: CHECK nas três quantidades

Revision ID: 20260919_qtd_nao_neg
Revises: 20260828_aud_estoqu
Create Date: 2026-09-19

A limpeza roda ANTES do ALTER de propósito. Um ALTER TABLE ... ADD CHECK falha
se uma única linha já viola a regra, e init_db mata o startup quando o alembic
sai diferente de zero: uma linha ruim em qualquer banco vira crashloop, não um
erro que alguém lê. O levantamento em prod achou zero linhas negativas — a
limpeza não é para prod hoje, é para o banco onde isto rodar amanhã.

Zerar, e não recalcular: uma quantidade negativa não é um número de unidades
que dê para consertar sozinho. Zero é a leitura conservadora — o produto para
de ser vendido até alguém contar a prateleira.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260919_qtd_nao_neg'
down_revision = '20260828_aud_estoqu'
branch_labels = None
depends_on = None

CONSTRAINT = 'ck_estoque_quantidades_nao_negativas'
REGRA = (
    'quantidade >= 0 AND quantidade_reservada >= 0 AND quantidade_disponivel >= 0'
)


def upgrade() -> None:
    # O WHERE não é otimização: estoque.estoque tem trg_auditoria (AFTER UPDATE
    # FOR EACH ROW), e um UPDATE sem filtro escreveria uma linha de auditoria
    # para cada produto do sistema — ruído que esconde o que a auditoria existe
    # para mostrar.
    op.execute(
        'UPDATE estoque.estoque SET '
        'quantidade = GREATEST(quantidade, 0), '
        'quantidade_reservada = GREATEST(quantidade_reservada, 0), '
        'quantidade_disponivel = GREATEST(quantidade_disponivel, 0) '
        'WHERE quantidade < 0 '
        'OR quantidade_reservada < 0 '
        'OR quantidade_disponivel < 0'
    )
    op.create_check_constraint(CONSTRAINT, 'estoque', REGRA, schema='estoque')


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT, 'estoque', schema='estoque', type_='check')
