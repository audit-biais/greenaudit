from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

from app.models.organization import Organization

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.monitoring_config import MonitoringConfig


class Audit(Base):
    """Audit de conformité anti-greenwashing pour une entreprise."""

    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )

    # Infos entreprise auditée
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    website_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Résultats
    status: Mapped[str] = mapped_column(String(50), default="draft")
    total_claims: Mapped[int] = mapped_column(Integer, default=0)
    conforming_claims: Mapped[int] = mapped_column(Integer, default=0)
    non_conforming_claims: Mapped[int] = mapped_column(Integer, default=0)
    at_risk_claims: Mapped[int] = mapped_column(Integer, default=0)
    global_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Pays (pour les règles nationales spécifiques, ex: loi AGEC France)
    country: Mapped[str] = mapped_column(String(5), nullable=False, server_default="fr")

    # Version du moteur de règles utilisée pour l'analyse (traçabilité EmpCo)
    rules_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Méta
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    share_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relations
    organization: Mapped[Organization] = relationship(back_populates="audits")
    claims: Mapped[List[Claim]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    monitoring_config: Mapped[Optional[MonitoringConfig]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", uselist=False
    )
