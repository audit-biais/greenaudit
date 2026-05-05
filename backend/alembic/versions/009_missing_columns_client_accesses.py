"""009_missing_columns_client_accesses

Ajoute les colonnes manquantes sur audits et crée la table client_accesses :
- audits.rules_version (VARCHAR(20) NULL)
- audits.created_by_user_id (UUID FK → users.id ON DELETE SET NULL)
- audits.pdf_sha256 (VARCHAR(64) NULL)
- audits.share_token_expires_at (TIMESTAMPTZ NULL)
- table client_accesses (coffre-fort accès client)
- data : renomme plan 'free' → 'starter' sur organizations

Revision ID: 009_missing_columns_client_accesses
Revises: 008_source_url
Create Date: 2026-05-04
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "009_missing_columns_client_accesses"
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


def _table_exists(table: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
    ), {"t": table})
    return result.scalar()


def upgrade() -> None:
    # --- audits.rules_version ---
    if not _column_exists("audits", "rules_version"):
        op.add_column("audits", sa.Column("rules_version", sa.String(20), nullable=True))

    # --- audits.created_by_user_id ---
    if not _column_exists("audits", "created_by_user_id"):
        op.add_column("audits", sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ))

    # --- audits.pdf_sha256 ---
    if not _column_exists("audits", "pdf_sha256"):
        op.add_column("audits", sa.Column("pdf_sha256", sa.String(64), nullable=True))

    # --- audits.share_token_expires_at ---
    if not _column_exists("audits", "share_token_expires_at"):
        op.add_column("audits", sa.Column(
            "share_token_expires_at", sa.DateTime(timezone=True), nullable=True
        ))

    # --- table client_accesses ---
    if not _table_exists("client_accesses"):
        op.create_table(
            "client_accesses",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "audit_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("audits.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("token", sa.String(200), nullable=False, unique=True),
            sa.Column("client_email", sa.String(255), nullable=False),
            sa.Column("validity_days", sa.Integer, nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_revoked", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("pdf_downloaded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("zip_downloaded_at", sa.DateTime(timezone=True), nullable=True),
        )

    # --- data : free → starter ---
    op.get_bind().execute(sa.text(
        "UPDATE organizations SET subscription_plan = 'starter' "
        "WHERE subscription_plan = 'free'"
    ))


def downgrade() -> None:
    if _table_exists("client_accesses"):
        op.drop_table("client_accesses")
    for col in ("share_token_expires_at", "pdf_sha256", "created_by_user_id", "rules_version"):
        if _column_exists("audits", col):
            op.drop_column("audits", col)
