from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ClaimResultResponse(BaseModel):
    """Résultat détaillé d'un critère d'analyse."""
    id: UUID
    claim_id: UUID
    criterion: str
    verdict: str
    explanation: str
    recommendation: Optional[str] = None
    regulation_reference: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimWithResultsResponse(BaseModel):
    """Claim avec tous ses résultats d'analyse."""
    id: UUID
    claim_text: str
    support_type: str
    scope: str
    product_name: Optional[str] = None
    overall_verdict: Optional[str] = None
    results: List[ClaimResultResponse] = []

    model_config = {"from_attributes": True}


class AuditResultsResponse(BaseModel):
    """Résultats complets d'un audit après analyse."""
    audit_id: UUID
    company_name: str
    status: str
    total_claims: int
    conforming_claims: int
    non_conforming_claims: int
    at_risk_claims: int
    global_score: Optional[float] = None
    risk_level: Optional[str] = None
    claims: List[ClaimWithResultsResponse] = []
