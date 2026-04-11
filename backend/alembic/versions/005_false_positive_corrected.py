"""005_false_positive_corrected

Ajoute les colonnes manquantes sur la table claims :
- is_corrected (BOOLEAN DEFAULT FALSE)
- corrected_at (TIMESTAMPTZ nullable)
- is_false_positive (BOOLEAN DEFAULT FALSE)
- false_positive_reason (VARCHAR(100) nullable)

Revision ID: 005_false_positive_corrected
Revises: 004_ecolabel_country
Create Date: 2026-04-11
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "005_false_positive_corrected"
down_revision = "004_ecolabel_country"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.scalar() > 0


def upgrade() -> None:
    if not _column_exists("claims", "is_corrected"):
        op.add_column(
            "claims",
            sa.Column("is_corrected", sa.Boolean(), nullable=False, server_default="false"),
        )
    if not _column_exists("claims", "corrected_at"):
        op.add_column(
            "claims",
            sa.Column("corrected_at", sa.TIMESTAMP(timezone=True), nullable=True),
        )
    if not _column_exists("claims", "is_false_positive"):
        op.add_column(
            "claims",
            sa.Column("is_false_positive", sa.Boolean(), nullable=False, server_default="false"),
        )
    if not _column_exists("claims", "false_positive_reason"):
        op.add_column(
            "claims",
            sa.Column("false_positive_reason", sa.String(100), nullable=True),
        )


def downgrade() -> None:
    for col in ("false_positive_reason", "is_false_positive", "corrected_at", "is_corrected"):
        if _column_exists("claims", col):
            op.drop_column("claims", col)
