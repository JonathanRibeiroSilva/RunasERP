"""triggers de auditoria de estado (empresas)

Revision ID: 20260828_aud_empres
Revises: 20260703_fix_enums
Create Date: 2026-08-28

Só o CREATE TRIGGER: a função gateway.auditar_registro() e as tabelas de
auditoria nascem no db-init / postgres/init-schemas.sql, que roda antes de
qualquer serviço. Sete Alembics independentes não têm ordem de boot entre si.

Escopo deliberado — as tabelas onde reverter tem consequência (dinheiro,
estoque, cadastro), não as ~30 do sistema. Log, cache, fila e webhook
processado ficam de fora: auditar tabela de webhook é auditar o auditor.
Escalar = nova migration com mais nomes nesta lista.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260828_aud_empres'
down_revision = '20260703_fix_enums'
branch_labels = None
depends_on = None

SCHEMA = 'empresas'
# ponytail: trigger nas tabelas onde reverter importa, não em todas. Numa VPS de
# 1 vCPU, ligar tudo antes de medir é apostar contra o disco — a tabela de
# auditoria cresce mais rápido que os próprios dados.
TABELAS = ['empresas']


def upgrade() -> None:
    for tabela in TABELAS:
        op.execute(
            f'DROP TRIGGER IF EXISTS trg_auditoria ON {SCHEMA}.{tabela}'
        )
        op.execute(
            f'CREATE TRIGGER trg_auditoria '
            f'AFTER INSERT OR UPDATE OR DELETE ON {SCHEMA}.{tabela} '
            f'FOR EACH ROW EXECUTE FUNCTION gateway.auditar_registro()'
        )


def downgrade() -> None:
    for tabela in TABELAS:
        op.execute(f'DROP TRIGGER IF EXISTS trg_auditoria ON {SCHEMA}.{tabela}')
