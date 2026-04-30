from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

SupportType = Literal["web", "packaging", "publicite", "reseaux_sociaux", "autre"]
ScopeType = Literal["produit", "entreprise"]
ProofType = Literal["certification_tierce", "rapport_interne", "donnees_fournisseur", "aucune"]


# --- Request schemas ---

class ClaimCreate(BaseModel):
    """Ajout d'une claim à un audit."""
    claim_text: str = Field(min_length=1, max_length=2000)
    support_type: SupportType
    scope: ScopeType
    product_name: Optional[str] = Field(None, max_length=255)

    # Preuves
    has_proof: bool = False
    proof_description: Optional[str] = Field(None, max_length=1000)
    proof_type: Optional[ProofType] = None

    # Labels
    has_label: bool = False
    label_name: Optional[str] = Field(None, max_length=255)
    label_is_certified: Optional[bool] = None

    # Engagement futur
    is_future_commitment: bool = False
    target_date: Optional[date] = None
    has_independent_verification: bool = False


class ClaimUpdate(BaseModel):
    """Modification d'une claim existante."""
    claim_text: Optional[str] = Field(None, min_length=1, max_length=2000)
    support_type: Optional[SupportType] = None
    scope: Optional[ScopeType] = None
    product_name: Optional[str] = Field(None, max_length=255)

    has_proof: Optional[bool] = None
    proof_description: Optional[str] = Field(None, max_length=1000)
    proof_type: Optional[ProofType] = None

    has_label: Optional[bool] = None
    label_name: Optional[str] = Field(None, max_length=255)
    label_is_certified: Optional[bool] = None

    is_future_commitment: Optional[bool] = None
    target_date: Optional[date] = None
    has_independent_verification: Optional[bool] = None


# --- Response schemas ---

class ClaimResponse(BaseModel):
    """Réponse complète d'une claim."""
    id: UUID
    audit_id: UUID
    claim_text: str
    support_type: str
    scope: str
    product_name: Optional[str] = None

    has_proof: bool
    proof_description: Optional[str] = None
    proof_type: Optional[str] = None

    has_label: bool
    label_name: Optional[str] = None
    label_is_certified: Optional[bool] = None

    is_future_commitment: bool
    target_date: Optional[date] = None
    has_independent_verification: bool

    overall_verdict: Optional[str] = None
    is_corrected: bool = False
    corrected_at: Optional[datetime] = None
    is_false_positive: bool = False
    false_positive_reason: Optional[str] = None

    regulatory_basis: Optional[str] = None
    regime: Optional[str] = None
    status: str = "À traiter"

    created_at: datetime

    results: List[ClaimResultInClaimResponse] = []

    model_config = {"from_attributes": True}


class ClaimResultInClaimResponse(BaseModel):
    """Résultat d'un critère inclus dans la réponse d'une claim."""
    id: UUID
    criterion: str
    verdict: str
    explanation: str
    recommendation: Optional[str] = None
    regulation_reference: Optional[str] = None

    model_config = {"from_attributes": True}


# Résoudre la forward reference
ClaimResponse.model_rebuild()
