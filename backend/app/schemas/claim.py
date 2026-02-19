from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request schemas ---

class ClaimCreate(BaseModel):
    """Ajout d'une claim à un audit."""
    claim_text: str = Field(min_length=1)
    support_type: str = Field(
        description="web, packaging, publicite, reseaux_sociaux, autre",
    )
    scope: str = Field(description="produit, entreprise")
    product_name: Optional[str] = None

    # Preuves
    has_proof: bool = False
    proof_description: Optional[str] = None
    proof_type: Optional[str] = Field(
        None,
        description="certification_tierce, rapport_interne, donnees_fournisseur, aucune",
    )

    # Labels
    has_label: bool = False
    label_name: Optional[str] = None
    label_is_certified: Optional[bool] = None

    # Engagement futur
    is_future_commitment: bool = False
    target_date: Optional[date] = None
    has_independent_verification: bool = False


class ClaimUpdate(BaseModel):
    """Modification d'une claim existante."""
    claim_text: Optional[str] = Field(None, min_length=1)
    support_type: Optional[str] = None
    scope: Optional[str] = None
    product_name: Optional[str] = None

    has_proof: Optional[bool] = None
    proof_description: Optional[str] = None
    proof_type: Optional[str] = None

    has_label: Optional[bool] = None
    label_name: Optional[str] = None
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
