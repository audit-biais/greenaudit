from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Request schemas ---

class AuditCreate(BaseModel):
    """Création d'un nouvel audit (draft)."""
    company_name: str = Field(min_length=1, max_length=255)
    sector: str = Field(
        min_length=1,
        max_length=100,
        description="e-commerce, cosmetiques, alimentaire, textile, services, autre",
    )
    website_url: Optional[str] = Field(None, max_length=2048)
    contact_email: Optional[EmailStr] = None
    country: str = Field(default="fr", max_length=5, description="Code pays ISO (fr, de, es...)")

    @field_validator("website_url")
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.startswith(("http://", "https://")):
            raise ValueError("website_url doit commencer par http:// ou https://")
        return v


# --- Response schemas ---

class ClientAccessSummary(BaseModel):
    """Résumé du coffre-fort client pour le dashboard."""
    exists: bool = False
    is_revoked: bool = False
    client_email: Optional[str] = None
    last_opened_at: Optional[datetime] = None
    pdf_downloaded_at: Optional[datetime] = None
    zip_downloaded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuditSummaryResponse(BaseModel):
    """Résumé d'un audit pour la liste du dashboard."""
    id: UUID
    company_name: str
    sector: str
    status: str
    total_claims: int
    global_score: Optional[Decimal] = None
    risk_level: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    client_access: Optional[ClientAccessSummary] = None

    model_config = {"from_attributes": True}


class AuditDetailResponse(BaseModel):
    """Détail complet d'un audit."""
    id: UUID
    organization_id: UUID
    company_name: str
    sector: str
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    status: str
    total_claims: int
    conforming_claims: int
    non_conforming_claims: int
    at_risk_claims: int
    global_score: Optional[Decimal] = None
    risk_level: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    claims: List[ClaimInAuditResponse] = []

    model_config = {"from_attributes": True}


class ClaimInAuditResponse(BaseModel):
    """Claim résumée dans la réponse d'un audit."""
    id: UUID
    claim_text: str
    support_type: str
    scope: str
    overall_verdict: Optional[str] = None

    model_config = {"from_attributes": True}


# Résoudre la forward reference
AuditDetailResponse.model_rebuild()
