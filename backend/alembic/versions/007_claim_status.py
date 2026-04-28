"""007_claim_status

Ajoute la colonne `status` sur la table claims pour le suivi du cycle de traitement.

Valeurs possibles : 'À traiter' | 'En cours' | 'Corrigé' | 'À valider'

Revision ID: 007_claim_status
Revises: 006_regulatory_classification
Create Date: 2026-04-19
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "007_claim_status"
down_revision = "006_regulatory_classification"
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
    if not _column_exists("claims", "status"):
        op.add_column(
            "claims",
            sa.Column(
                "status",
                sa.String(20),
                nullable=False,
                server_default="À traiter",
            ),
        )


def downgrade() -> None:
    if _column_exists("claims", "status"):
        op.drop_column("claims", "status")
