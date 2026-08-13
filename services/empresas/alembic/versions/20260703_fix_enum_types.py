"""fix tipo/status/regime_tributario to use native postgres enum types

Revision ID: 20260703_fix_enums
Revises: 20260611_empresas
Create Date: 2026-07-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260703_fix_enums'
down_revision = '20260611_empresas'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    O model SQLAlchemy declara `tipo`, `status` e `regime_tributario` como
    Enum nativo do Postgres, mas a migration inicial criou essas colunas
    como VARCHAR simples — os tipos nunca existiram no banco, causando
    UndefinedObjectError ao inserir/atualizar uma empresa. Cria os tipos e
    migra as colunas, reaproveitando os valores de texto já existentes.
    """
    conn = op.get_bind()

    tipo_empresa_enum = postgresql.ENUM('MATRIZ', 'FILIAL', name='tipoempresa', schema='empresas')
    status_empresa_enum = postgresql.ENUM('ATIVA', 'INATIVA', 'SUSPENSA', name='statusempresa', schema='empresas')
    regime_tributario_enum = postgresql.ENUM(
        'SIMPLES_NACIONAL', 'LUCRO_PRESUMIDO', 'LUCRO_REAL', 'MEI',
        name='regimetributario', schema='empresas'
    )
    tipo_empresa_enum.create(conn, checkfirst=True)
    status_empresa_enum.create(conn, checkfirst=True)
    regime_tributario_enum.create(conn, checkfirst=True)

    # server_default é texto simples ('MATRIZ', 'ATIVA', ...) — precisa cair antes do
    # ALTER TYPE (Postgres não converte o default automaticamente) e voltar já tipado.
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN tipo DROP DEFAULT")
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN regime_tributario DROP DEFAULT")

    op.execute(
        "ALTER TABLE empresas.empresas ALTER COLUMN tipo TYPE empresas.tipoempresa "
        "USING tipo::text::empresas.tipoempresa"
    )
    op.execute(
        "ALTER TABLE empresas.empresas ALTER COLUMN status TYPE empresas.statusempresa "
        "USING status::text::empresas.statusempresa"
    )
    op.execute(
        "ALTER TABLE empresas.empresas ALTER COLUMN regime_tributario TYPE empresas.regimetributario "
        "USING regime_tributario::text::empresas.regimetributario"
    )

    op.execute(
        "ALTER TABLE empresas.empresas ALTER COLUMN tipo SET DEFAULT 'MATRIZ'::empresas.tipoempresa"
    )
    op.execute(
        "ALTER TABLE empresas.empresas ALTER COLUMN status SET DEFAULT 'ATIVA'::empresas.statusempresa"
    )
    op.execute(
        "ALTER TABLE empresas.empresas ALTER COLUMN regime_tributario "
        "SET DEFAULT 'SIMPLES_NACIONAL'::empresas.regimetributario"
    )


def downgrade() -> None:
    """Reverte as colunas para VARCHAR e remove os tipos enum."""
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN tipo DROP DEFAULT")
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN regime_tributario DROP DEFAULT")

    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN tipo TYPE VARCHAR(20) USING tipo::text")
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN status TYPE VARCHAR(20) USING status::text")
    op.execute(
        "ALTER TABLE empresas.empresas ALTER COLUMN regime_tributario TYPE VARCHAR(50) USING regime_tributario::text"
    )

    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN tipo SET DEFAULT 'MATRIZ'")
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN status SET DEFAULT 'ATIVA'")
    op.execute("ALTER TABLE empresas.empresas ALTER COLUMN regime_tributario SET DEFAULT 'SIMPLES_NACIONAL'")

    conn = op.get_bind()
    postgresql.ENUM(name='tipoempresa', schema='empresas').drop(conn, checkfirst=True)
    postgresql.ENUM(name='statusempresa', schema='empresas').drop(conn, checkfirst=True)
    postgresql.ENUM(name='regimetributario', schema='empresas').drop(conn, checkfirst=True)
