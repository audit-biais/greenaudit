from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.audit import Audit
    from app.models.user import User


class Organization(Base):
    """Organisation partenaire white-label (agence com, cabinet RSE, avocat)."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Branding white-label
    brand_primary_color: Mapped[str] = mapped_column(String(7), default="#1B5E20")
    brand_secondary_color: Mapped[str] = mapped_column(String(7), default="#2E7D32")
    logo_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    logo_content_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Abonnement Stripe (au niveau org — pool partagé)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter")
    subscription_status: Mapped[str] = mapped_column(String(50), default="inactive")

    # Quotas d'audits (pool partagé entre tous les membres)
    audits_this_month: Mapped[int] = mapped_column(Integer, default=0)
    audits_limit: Mapped[int] = mapped_column(Integer, default=1)
    audits_reset_month: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    # Relations
    users: Mapped[List[User]] = relationship(back_populates="organization")
    audits: Mapped[List[Audit]] = relationship(back_populates="organization", cascade="all, delete-orphan")
