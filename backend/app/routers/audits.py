from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_partner
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.models.partner import Partner
from app.schemas.audit import AuditCreate, AuditDetailResponse, AuditSummaryResponse
from app.schemas.claim_result import AuditResultsResponse
from app.services.analysis_engine import analyze_claim
from app.services.scoring import calculate_global_score, compute_verdict_counts

router = APIRouter(prefix="/api/audits", tags=["audits"])


async def _get_partner_audit(
    audit_id: UUID,
    partner: Partner,
    db: AsyncSession,
    load_claims: bool = False,
) -> Audit:
    """Helper : récupère un audit appartenant au partenaire courant."""
    stmt = select(Audit).where(Audit.id == audit_id, Audit.partner_id == partner.id)
    if load_claims:
        stmt = stmt.options(selectinload(Audit.claims))
    result = await db.execute(stmt)
    audit = result.scalar_one_or_none()
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit introuvable",
        )
    return audit


@router.post("", response_model=AuditSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_audit(
    data: AuditCreate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> Audit:
    """Créer un audit (draft)."""
    audit = Audit(
        partner_id=partner.id,
        company_name=data.company_name,
        sector=data.sector,
        website_url=data.website_url,
        contact_email=data.contact_email,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    return audit


@router.get("", response_model=List[AuditSummaryResponse])
async def list_audits(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> List[Audit]:
    """Lister les audits du partenaire courant."""
    result = await db.execute(
        select(Audit)
        .where(Audit.partner_id == partner.id)
        .order_by(Audit.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{audit_id}", response_model=AuditDetailResponse)
async def get_audit(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> Audit:
    """Détail d'un audit avec ses claims."""
    return await _get_partner_audit(audit_id, partner, db, load_claims=True)


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_audit(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Supprimer un audit (uniquement si draft)."""
    audit = await _get_partner_audit(audit_id, partner, db)
    if audit.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les audits en brouillon peuvent être supprimés",
        )
    await db.delete(audit)
    await db.commit()


@router.post("/{audit_id}/analyze", response_model=AuditResultsResponse)
async def analyze_audit(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> AuditResultsResponse:
    """
    Lancer l'analyse : applique les 6 règles sur chaque claim,
    calcule le scoring, met à jour le status de l'audit.
    """
    # Charger l'audit avec ses claims
    audit = await _get_partner_audit(audit_id, partner, db, load_claims=True)

    if not audit.claims:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'audit ne contient aucune claim à analyser",
        )

    # Supprimer les anciens résultats si re-analyse
    claim_ids = [c.id for c in audit.claims]
    await db.execute(
        delete(ClaimResult).where(ClaimResult.claim_id.in_(claim_ids))
    )

    # Analyser chaque claim
    all_verdicts: List[str] = []
    for claim in audit.claims:
        results, overall_verdict = analyze_claim(claim)
        claim.overall_verdict = overall_verdict
        all_verdicts.append(overall_verdict)
        for r in results:
            db.add(r)

    # Calculer le scoring global
    counts = compute_verdict_counts(all_verdicts)
    score, risk_level = calculate_global_score(
        conforming=counts["conforme"],
        at_risk=counts["risque"],
        non_conforming=counts["non_conforme"],
    )

    # Mettre à jour l'audit
    audit.status = "completed"
    audit.total_claims = len(audit.claims)
    audit.conforming_claims = counts["conforme"]
    audit.non_conforming_claims = counts["non_conforme"]
    audit.at_risk_claims = counts["risque"]
    audit.global_score = score
    audit.risk_level = risk_level
    audit.completed_at = datetime.now(timezone.utc)

    await db.commit()

    # Recharger avec les résultats pour la réponse
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id)
        .options(selectinload(Audit.claims).selectinload(Claim.results))
    )
    audit = result.scalar_one()

    return AuditResultsResponse(
        audit_id=audit.id,
        company_name=audit.company_name,
        status=audit.status,
        website_url=audit.website_url,
        total_claims=audit.total_claims,
        conforming_claims=audit.conforming_claims,
        non_conforming_claims=audit.non_conforming_claims,
        at_risk_claims=audit.at_risk_claims,
        global_score=float(audit.global_score) if audit.global_score is not None else None,
        risk_level=audit.risk_level,
        claims=audit.claims,
    )


@router.get("/{audit_id}/results", response_model=AuditResultsResponse)
async def get_audit_results(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> AuditResultsResponse:
    """Récupérer les résultats détaillés d'un audit analysé."""
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id, Audit.partner_id == partner.id)
        .options(selectinload(Audit.claims).selectinload(Claim.results))
    )
    audit = result.scalar_one_or_none()

    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit introuvable",
        )

    if audit.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'audit n'a pas encore été analysé",
        )

    return AuditResultsResponse(
        audit_id=audit.id,
        company_name=audit.company_name,
        status=audit.status,
        website_url=audit.website_url,
        total_claims=audit.total_claims,
        conforming_claims=audit.conforming_claims,
        non_conforming_claims=audit.non_conforming_claims,
        at_risk_claims=audit.at_risk_claims,
        global_score=float(audit.global_score) if audit.global_score is not None else None,
        risk_level=audit.risk_level,
        claims=audit.claims,
    )
