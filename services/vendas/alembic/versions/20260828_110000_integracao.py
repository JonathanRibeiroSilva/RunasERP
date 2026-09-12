"""integrações por tenant + access token do Mercado Pago cifrado

Revision ID: 20260828_integ
Revises: 20260627_reconcil
Create Date: 2026-08-28

O access token vivia em texto plano em configuracoes_pagamento. Cifrar a coluna
nova e apagar a antiga na mesma revisão é de propósito: deixar as duas conviver
significaria uma janela em que o segredo em claro continua no banco enquanto
todo mundo acha que já está protegido.
"""
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260828_integ'
down_revision = '20260627_reconcil'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'configuracoes_integracao',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('evolution_url', sa.String(length=255), nullable=True),
        sa.Column('evolution_api_key_enc', sa.Text(), nullable=True),
        sa.Column('evolution_instance', sa.String(length=100), nullable=True),
        sa.Column('whatsapp_ativo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('smtp_host', sa.String(length=255), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=True),
        sa.Column('smtp_user', sa.String(length=255), nullable=True),
        sa.Column('smtp_password_enc', sa.Text(), nullable=True),
        sa.Column('smtp_from_name', sa.String(length=100), nullable=True),
        sa.Column('email_ativo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('empresa_id'),
        schema='vendas',
    )
    op.create_index(
        'ix_config_integ_empresa', 'configuracoes_integracao', ['empresa_id'],
        unique=False, schema='vendas',
    )

    # Access token do Mercado Pago: texto plano -> cifrado
    op.add_column(
        'configuracoes_pagamento',
        sa.Column('mercadopago_access_token_enc', sa.Text(), nullable=True),
        schema='vendas',
    )
    _cifrar_tokens_existentes()
    op.drop_column('configuracoes_pagamento', 'mercadopago_access_token', schema='vendas')


def _cifrar_tokens_existentes() -> None:
    """
    Cifra as linhas que já existem.

    Sem INTEGRACOES_SECRET_KEY_V2 não dá para cifrar, e seguir em frente apagaria
    a coluna antiga levando junto os tokens dos lojistas — o boot falha alto em
    vez de destruir credencial de produção.
    """
    conn = op.get_bind()
    linhas = conn.execute(sa.text(
        "SELECT id, mercadopago_access_token FROM vendas.configuracoes_pagamento "
        "WHERE mercadopago_access_token IS NOT NULL AND mercadopago_access_token <> ''"
    )).fetchall()
    if not linhas:
        return

    chave = os.getenv("INTEGRACOES_SECRET_KEY_V2", "")
    if not chave:
        raise RuntimeError(
            f"{len(linhas)} access token(s) do Mercado Pago para cifrar e "
            "INTEGRACOES_SECRET_KEY_V2 não está definida. Defina antes do deploy."
        )

    from cryptography.fernet import Fernet
    fernet = Fernet(chave.encode())
    for linha in linhas:
        conn.execute(
            sa.text(
                "UPDATE vendas.configuracoes_pagamento SET mercadopago_access_token_enc = :v "
                "WHERE id = :id"
            ),
            {"v": fernet.encrypt(linha[1].encode()).decode(), "id": linha[0]},
        )


def downgrade() -> None:
    op.add_column(
        'configuracoes_pagamento',
        sa.Column('mercadopago_access_token', sa.String(length=255), nullable=True),
        schema='vendas',
    )
    op.drop_column('configuracoes_pagamento', 'mercadopago_access_token_enc', schema='vendas')
    op.drop_index('ix_config_integ_empresa', 'configuracoes_integracao', schema='vendas')
    op.drop_table('configuracoes_integracao', schema='vendas')
