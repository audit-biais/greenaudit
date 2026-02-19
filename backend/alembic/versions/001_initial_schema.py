"""Initial schema — 4 tables: partners, audits, claims, claim_results

Revision ID: 001
Revises: None
Create Date: 2026-02-19

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- partners ---
    op.create_table(
        "partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("logo_url", sa.Text, nullable=True),
        sa.Column("brand_primary_color", sa.String(7), server_default="#1B5E20"),
        sa.Column("brand_secondary_color", sa.String(7), server_default="#2E7D32"),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- audits ---
    op.create_table(
        "audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("website_url", sa.Text, nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("total_claims", sa.Integer, server_default="0"),
        sa.Column("conforming_claims", sa.Integer, server_default="0"),
        sa.Column("non_conforming_claims", sa.Integer, server_default="0"),
        sa.Column("at_risk_claims", sa.Integer, server_default="0"),
        sa.Column("global_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("pdf_url", sa.Text, nullable=True),
        sa.Column("share_token", sa.String(64), unique=True, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- claims ---
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_text", sa.Text, nullable=False),
        sa.Column("support_type", sa.String(50), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("has_proof", sa.Boolean, server_default=sa.text("false")),
        sa.Column("proof_description", sa.Text, nullable=True),
        sa.Column("proof_type", sa.String(100), nullable=True),
        sa.Column("has_label", sa.Boolean, server_default=sa.text("false")),
        sa.Column("label_name", sa.String(255), nullable=True),
        sa.Column("label_is_certified", sa.Boolean, nullable=True),
        sa.Column("is_future_commitment", sa.Boolean, server_default=sa.text("false")),
        sa.Column("target_date", sa.Date, nullable=True),
        sa.Column("has_independent_verification", sa.Boolean, server_default=sa.text("false")),
        sa.Column("overall_verdict", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- claim_results ---
    op.create_table(
        "claim_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("criterion", sa.String(50), nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("regulation_reference", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("claim_results")
    op.drop_table("claims")
    op.drop_table("audits")
    op.drop_table("partners")
