"""004_ecolabel_country

Ajoute :
- audits.country (VARCHAR(5) DEFAULT 'fr') — pour le filtre AGEC France
- evidence_files.document_type (VARCHAR(50) DEFAULT 'autre') — filtre Écolabel

Revision ID: 004_ecolabel_country
Revises: 003_multitenant
Create Date: 2026-04-04
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "004_ecolabel_country"
down_revision = "003_multitenant"
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
    # audits.country
    if not _column_exists("audits", "country"):
        op.add_column(
            "audits",
            sa.Column("country", sa.String(5), nullable=False, server_default="fr"),
        )

    # evidence_files.document_type
    if not _column_exists("evidence_files", "document_type"):
        op.add_column(
            "evidence_files",
            sa.Column("document_type", sa.String(50), nullable=False, server_default="autre"),
        )


def downgrade() -> None:
    if _column_exists("evidence_files", "document_type"):
        op.drop_column("evidence_files", "document_type")
    if _column_exists("audits", "country"):
        op.drop_column("audits", "country")
