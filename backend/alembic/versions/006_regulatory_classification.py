"""006_regulatory_classification

Ajoute deux colonnes à la table claims pour la classification du régime juridique EmpCo :
- regulatory_basis VARCHAR(50) NULL : base réglementaire précise (annexe_I_2bis, etc.)
- regime VARCHAR(20) NULL : régime applicable (liste_noire ou cas_par_cas)

Ces colonnes sont renseignées par le nouveau service regulatory_classifier.py
lors de chaque analyse, en amont des 8 règles existantes.

Revision ID: 006_regulatory_classification
Revises: 005_false_positive_corrected
Create Date: 2026-04-14
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "006_regulatory_classification"
down_revision = "005_false_positive_corrected"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.scalar() > 0


def _index_exists(index_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM pg_indexes WHERE indexname = :n"
    ), {"n": index_name})
    return result.scalar() > 0


def upgrade() -> None:
    if not _column_exists("claims", "regulatory_basis"):
        op.add_column(
            "claims",
            sa.Column("regulatory_basis", sa.String(50), nullable=True),
        )
    if not _column_exists("claims", "regime"):
        op.add_column(
            "claims",
            sa.Column("regime", sa.String(20), nullable=True),
        )
    if not _index_exists("ix_claims_regime"):
        op.create_index("ix_claims_regime", "claims", ["regime"])


def downgrade() -> None:
    if _index_exists("ix_claims_regime"):
        op.drop_index("ix_claims_regime", table_name="claims")
    for col in ("regime", "regulatory_basis"):
        if _column_exists("claims", col):
            op.drop_column("claims", col)
