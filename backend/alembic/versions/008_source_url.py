"""008_source_url

Ajoute la colonne `source_url` sur la table claims pour tracer
la page d'où chaque allégation a été extraite lors du scan.

Revision ID: 008_source_url
Revises: 007_claim_status
Create Date: 2026-05-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "008_source_url"
down_revision = "007_claim_status"
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
    if not _column_exists("claims", "source_url"):
        op.add_column(
            "claims",
            sa.Column("source_url", sa.String(500), nullable=True),
        )


def downgrade() -> None:
    if _column_exists("claims", "source_url"):
        op.drop_column("claims", "source_url")
