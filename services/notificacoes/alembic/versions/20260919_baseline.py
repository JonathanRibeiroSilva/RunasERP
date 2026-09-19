"""baseline: first revision of the notificacoes chain, no tables yet

Revision ID: 20260919_baseline
Revises:
Create Date: 2026-09-19

The service has no models, so there is nothing to create. The revision exists so
the chain is not empty: `alembic upgrade head` exits 0 both when it applies
nothing because the database is at head and when the image shipped without a
single revision, and database.py now refuses to boot on the second. Without this
file that guard would crashloop the service.

This directory did not exist in git before — an empty directory is not tracked,
so no image ever had one. Production already has `notificacoes.alembic_version`,
empty — left there by the upgrade that found no revisions. This file writes the
first row into it and runs no DDL. The first real table (the consumer's dedupe
ledger, when there is a consumer) goes on top as an ordinary revision.
"""
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision = "20260919_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
