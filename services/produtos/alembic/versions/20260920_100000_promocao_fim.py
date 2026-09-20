"""promoção passa a ter último dia

Revision ID: 20260920_promo_fim
Revises: 20260828_aud_produt
Create Date: 2026-09-20

A promoção não tinha prazo: preenchida uma vez, valia para sempre, e o lojista
que esquecesse de tirar continuava dando desconto sem saber. A coluna é o que
permite ao preço_efetivo parar de valer sozinho, sem job e sem ninguém lembrar.

Anulável porque linha antiga não tem data. Promoção sem data não vale (ver
Produto.preco_efetivo): o produto volta a ser cobrado pelo preço normal, e é o
lado seguro — anunciado e cobrado continuam batendo. Daqui para a frente o
serviço exige a data junto do preço promocional, então a ausência só existe em
linha anterior a esta revision.

Sem backfill: não há data certa para inventar em promoção que alguém criou sem
prazo, e escolher uma por conta própria mudaria preço de produto vivo em
silêncio. Prod tem zero promoções hoje.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260920_promo_fim'
down_revision = '20260828_aud_produt'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'produtos',
        sa.Column(
            'promocao_fim',
            sa.Date(),
            nullable=True,
            comment='Último dia da promoção, inclusive. Sem data, a promoção não vale.',
        ),
        schema='produtos',
    )


def downgrade() -> None:
    op.drop_column('produtos', 'promocao_fim', schema='produtos')
