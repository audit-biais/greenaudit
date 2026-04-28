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
    from app.models.evidence import EvidenceFile


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

    # Suivi correction (Pro/Enterprise)
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    corrected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Faux positif
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    false_positive_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Classification du régime juridique EmpCo (renseigné par regulatory_classifier)
    # Valeurs regulatory_basis : annexe_I_2bis, annexe_I_4bis, annexe_I_4ter,
    #   annexe_I_4quater, annexe_I_10bis, article_6_1d, article_6_general
    # Valeurs regime : liste_noire, cas_par_cas
    regulatory_basis: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    regime: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Statut de traitement — "À traiter" | "En cours" | "Corrigé" | "À valider"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="À traiter"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    audit: Mapped[Audit] = relationship(back_populates="claims")
    results: Mapped[List[ClaimResult]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    evidence_files: Mapped[List[EvidenceFile]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
