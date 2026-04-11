from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.organization import Organization


class User(Base):
    """Utilisateur membre d'une organisation partenaire."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Organisation
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    organization: Mapped[Optional[Organization]] = relationship(back_populates="users")
    role: Mapped[str] = mapped_column(String(50), default="member")  # "admin" ou "member"

    # Super admin (accès complet à toutes les orgs)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stripe (retrocompat user sans org)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter")
    subscription_status: Mapped[str] = mapped_column(String(50), default="inactive")

    # Quotas (retrocompat user sans org)
    audits_this_month: Mapped[int] = mapped_column(Integer, default=0)
    audits_limit: Mapped[int] = mapped_column(Integer, default=1)
    audits_reset_month: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
