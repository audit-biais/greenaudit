from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user, require_pro
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.models.evidence import EvidenceFile
from app.models.user import User
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate
from app.services.analysis_engine import analyze_claim, RULES_VERSION
from app.services.regulatory_classifier import classify_claim_regime
from app.services.scoring import calculate_global_score, compute_verdict_counts
from app.services.rewrite_engine import suggest_rewrite

router = APIRouter(tags=["claims"])


async def _get_user_audit(
    audit_id: UUID, user: User, db: AsyncSession
) -> Audit:
    """Helper : vérifie que l'audit appartient à l'organisation de l'utilisateur."""
    result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit introuvable",
        )
    return audit


async def _get_user_claim(
    claim_id: UUID, user: User, db: AsyncSession, load_results: bool = False
) -> Claim:
    """Helper : récupère une claim dont l'audit appartient à l'organisation de l'utilisateur."""
    stmt = (
        select(Claim)
        .join(Audit)
        .where(Claim.id == claim_id, Audit.organization_id == user.organization_id)
    )
    if load_results:
        stmt = stmt.options(selectinload(Claim.results))
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim introuvable",
        )
    return claim


# --- Routes sous /api/audits/{audit_id}/claims ---

@router.post(
    "/api/audits/{audit_id}/claims",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_claim(
    audit_id: UUID,
    data: ClaimCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Claim:
    """Ajouter une claim à un audit."""
    audit = await _get_user_audit(audit_id, user, db)

    claim = Claim(audit_id=audit.id, **data.model_dump())
    db.add(claim)
    await db.flush()

    # Si l'audit est déjà complété, analyser immédiatement la nouvelle claim
    if audit.status == "completed":
        meta = {
            "support_type": claim.support_type,
            "scope": claim.scope,
            "has_proof": claim.has_proof,
            "proof_type": claim.proof_type,
        }
        classification = await classify_claim_regime(claim.claim_text, meta)
        claim.regulatory_basis = classification["regulatory_basis"]
        claim.regime = classification["regime"]

        results, overall_verdict = analyze_claim(
            claim,
            has_ecolabel_evidence=False,
            country=getattr(audit, "country", "fr") or "fr",
            scan_mode=True,
        )
        claim.overall_verdict = overall_verdict
        for r in results:
            db.add(r)

        # Recalculer le score global
        await db.flush()
        all_res = await db.execute(
            select(Claim).where(
                Claim.audit_id == audit.id,
                Claim.is_false_positive == False,
            )
        )
        all_claims = list(all_res.scalars().all())
        all_verdicts = [c.overall_verdict for c in all_claims if c.overall_verdict]
        counts = compute_verdict_counts(all_verdicts)
        score, risk_level = calculate_global_score(
            conforming=counts["conforme"],
            at_risk=counts["risque"],
            non_conforming=counts["non_conforme"],
        )
        audit.global_score = score
        audit.risk_level = risk_level
        audit.total_claims = len(all_claims)
        audit.conforming_claims = counts["conforme"]
        audit.at_risk_claims = counts["risque"]
        audit.non_conforming_claims = counts["non_conforme"]
        audit.rules_version = RULES_VERSION

    await db.commit()

    result = await db.execute(
        select(Claim)
        .where(Claim.id == claim.id)
        .options(selectinload(Claim.results))
    )
    return result.scalar_one()


@router.get(
    "/api/audits/{audit_id}/claims",
    response_model=List[ClaimResponse],
)
async def list_claims(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Claim]:
    """Lister les claims d'un audit."""
    await _get_user_audit(audit_id, user, db)

    result = await db.execute(
        select(Claim)
        .where(Claim.audit_id == audit_id)
        .options(selectinload(Claim.results))
        .order_by(Claim.created_at)
    )
    return list(result.scalars().all())


# --- Routes sous /api/claims/{claim_id} ---

@router.put("/api/claims/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: UUID,
    data: ClaimUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Claim:
    """Modifier une claim existante."""
    claim = await _get_user_claim(claim_id, user, db, load_results=True)

    result = await db.execute(
        select(Audit).where(Audit.id == claim.audit_id, Audit.organization_id == user.organization_id)
    )
    audit = result.scalar_one()
    if audit.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de modifier une claim d'un audit terminé",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)
    await db.commit()
    await db.refresh(claim)
    return claim


@router.delete("/api/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_claim(
    claim_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprimer une claim."""
    claim = await _get_user_claim(claim_id, user, db)

    result = await db.execute(
        select(Audit).where(Audit.id == claim.audit_id, Audit.organization_id == user.organization_id)
    )
    audit = result.scalar_one()
    if audit.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer une claim d'un audit terminé",
        )

    await db.delete(claim)
    await db.commit()


@router.patch("/api/claims/{claim_id}/mark-corrected", response_model=ClaimResponse)
async def mark_claim_corrected(
    claim_id: UUID,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
) -> Claim:
    """Marquer une allégation comme corrigée (toggle). Réservé aux plans Pro et Enterprise."""
    claim = await _get_user_claim(claim_id, user, db, load_results=True)

    # Si on veut marquer comme corrigée, vérifier qu'au moins une preuve existe
    if not claim.is_corrected:
        evidence_result = await db.execute(
            select(EvidenceFile).where(EvidenceFile.claim_id == claim_id).limit(1)
        )
        if evidence_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de marquer comme corrigée : aucune preuve n'a été uploadée pour cette allégation.",
            )

    claim.is_corrected = not claim.is_corrected
    claim.corrected_at = datetime.now(timezone.utc) if claim.is_corrected else None
    await db.commit()
    await db.refresh(claim)
    return claim


class FalsePositiveRequest(BaseModel):
    reason: str


@router.patch("/api/claims/{claim_id}/mark-false-positive", response_model=ClaimResponse)
async def mark_claim_false_positive(
    claim_id: UUID,
    data: FalsePositiveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Claim:
    """Marquer une allégation comme faux positif (toggle)."""
    claim = await _get_user_claim(claim_id, user, db, load_results=True)

    if claim.is_false_positive:
        # Toggle off — réinitialiser
        claim.is_false_positive = False
        claim.false_positive_reason = None
    else:
        claim.is_false_positive = True
        claim.false_positive_reason = data.reason

    await db.commit()
    await db.refresh(claim)
    return claim


class RewriteResponse(BaseModel):
    original: str
    suggestions: List[str]


@router.post("/api/claims/{claim_id}/rewrite", response_model=RewriteResponse)
async def rewrite_claim(
    claim_id: UUID,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Propose une réécriture conforme EmpCo pour une claim non conforme."""
    claim = await _get_user_claim(claim_id, user, db, load_results=True)

    if claim.overall_verdict not in ("non_conforme", "risque"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La réécriture n'est disponible que pour les allégations non conformes ou à risque",
        )

    # Récupérer le secteur via l'audit (filtre org conservé)
    audit_result = await db.execute(
        select(Audit).where(Audit.id == claim.audit_id, Audit.organization_id == user.organization_id)
    )
    audit = audit_result.scalar_one()

    # Collecter les raisons de non-conformité
    reasons = [
        r.explanation
        for r in claim.results
        if r.verdict in ("non_conforme", "risque")
    ]

    suggestion = await suggest_rewrite(
        claim_text=claim.claim_text,
        sector=audit.sector,
        non_conforming_reasons=reasons,
    )

    return {"original": claim.claim_text, "suggestions": suggestion}
