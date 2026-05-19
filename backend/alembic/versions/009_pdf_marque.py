"""009_pdf_marque

Ajoute les colonnes `pdf_marque_url` et `pdf_marque_sha256` sur la table audits
pour stocker le rapport commercial marque (livrable payant, brandé GreenAudit).

Revision ID: 009_pdf_marque
Revises: 008_source_url
Create Date: 2026-05-19
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "009_pdf_marque"
down_revision = "008_source_url"
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
    if not _column_exists("audits", "pdf_marque_url"):
        op.add_column("audits", sa.Column("pdf_marque_url", sa.Text, nullable=True))
    if not _column_exists("audits", "pdf_marque_sha256"):
        op.add_column("audits", sa.Column("pdf_marque_sha256", sa.String(64), nullable=True))


def downgrade() -> None:
    if _column_exists("audits", "pdf_marque_sha256"):
        op.drop_column("audits", "pdf_marque_sha256")
    if _column_exists("audits", "pdf_marque_url"):
        op.drop_column("audits", "pdf_marque_url")
