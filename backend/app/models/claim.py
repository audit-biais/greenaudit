from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.audit import Audit
    from app.models.claim_result import ClaimResult


class Claim(Base):
    """Allégation environnementale à auditer."""

    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )

    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    support_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Preuves déclarées
    has_proof: Mapped[bool] = mapped_column(Boolean, default=False)
    proof_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proof_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Labels
    has_label: Mapped[bool] = mapped_column(Boolean, default=False)
    label_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    label_is_certified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Engagement futur
    is_future_commitment: Mapped[bool] = mapped_column(Boolean, default=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    has_independent_verification: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    # Résultat global
    overall_verdict: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    audit: Mapped[Audit] = relationship(back_populates="claims")
    results: Mapped[List[ClaimResult]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
