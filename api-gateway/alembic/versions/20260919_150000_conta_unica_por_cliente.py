"""uma conta de login por cliente

Revision ID: 20260919_cli_unico
Revises: 20260828_assin
Create Date: 2026-09-19

email já era único; cliente_id não era. Duas contas com emails diferentes
podiam apontar para o mesmo cliente do serviço clientes, e daí em diante as
duas viam os mesmos pedidos, os mesmos endereços e o mesmo crédito.

O dedupe roda aqui dentro, antes do UNIQUE, e não num script à parte: esta
revision sobe no boot do gateway, e uma constraint que falha vira crashloop
que derruba o sistema inteiro. Prod está com zero duplicatas hoje, mas o que
torna a revision segura em QUALQUER banco (staging, a máquina de alguém, um
restore antigo) é ela mesma limpar o que impediria a constraint.

Sobrevive a linha MAIS ANTIGA por cliente_id. É a conta do cadastro original —
a que já tem senha conhecida do comprador, a que o login por email resolve e a
que os refresh tokens no Redis referenciam (chave `refresh:cliente:<id>`). A
duplicata é sempre o insert posterior. Mesma regra que o UNIQUE do email já
aplica na prática: a primeira ganha.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260919_cli_unico'
down_revision = '20260828_assin'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # (criado_em, id) desempata: criado_em pode empatar num insert em lote, e um
    # dedupe não determinístico deixaria dois nós do mesmo deploy escolherem
    # linhas diferentes.
    removidas = op.get_bind().execute(sa.text("""
        DELETE FROM gateway.clientes_auth a
        USING gateway.clientes_auth b
        WHERE a.cliente_id = b.cliente_id
          AND (b.criado_em, b.id) < (a.criado_em, a.id)
        RETURNING a.id, a.email, a.cliente_id
    """)).fetchall()

    # Sai no log do boot: apagar um login em silêncio é como o suporte descobre
    # o problema pelo cliente, e não pelo deploy.
    for linha in removidas:
        print(
            f"[{revision}] conta duplicada removida: "
            f"id={linha.id} email={linha.email} cliente_id={linha.cliente_id}"
        )

    op.create_unique_constraint(
        'uq_clientes_auth_cliente_id',
        'clientes_auth',
        ['cliente_id'],
        schema='gateway',
    )


def downgrade() -> None:
    """Solta a constraint. As linhas apagadas no upgrade não voltam."""
    op.drop_constraint(
        'uq_clientes_auth_cliente_id',
        'clientes_auth',
        schema='gateway',
        type_='unique',
    )
