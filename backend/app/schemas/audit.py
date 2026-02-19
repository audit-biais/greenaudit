from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Request schemas ---

class AuditCreate(BaseModel):
    """Création d'un nouvel audit (draft)."""
    company_name: str = Field(min_length=1, max_length=255)
    sector: str = Field(
        min_length=1,
        max_length=100,
        description="e-commerce, cosmetiques, alimentaire, textile, services, autre",
    )
    website_url: Optional[str] = None
    contact_email: Optional[EmailStr] = None


# --- Response schemas ---

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

    model_config = {"from_attributes": True}


class AuditDetailResponse(BaseModel):
    """Détail complet d'un audit."""
    id: UUID
    partner_id: UUID
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
