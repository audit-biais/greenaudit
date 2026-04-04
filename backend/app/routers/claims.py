from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.models.user import User
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate
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

    if audit.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'ajouter une claim à un audit terminé",
        )

    claim = Claim(audit_id=audit.id, **data.model_dump())
    db.add(claim)
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

    result = await db.execute(select(Audit).where(Audit.id == claim.audit_id))
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

    result = await db.execute(select(Audit).where(Audit.id == claim.audit_id))
    audit = result.scalar_one()
    if audit.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer une claim d'un audit terminé",
        )

    await db.delete(claim)
    await db.commit()


@router.post("/api/claims/{claim_id}/rewrite")
async def rewrite_claim(
    claim_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Propose une réécriture conforme EmpCo pour une claim non conforme."""
    claim = await _get_user_claim(claim_id, user, db, load_results=True)

    if claim.overall_verdict not in ("non_conforme", "risque"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La réécriture n'est disponible que pour les allégations non conformes ou à risque",
        )

    # Récupérer le secteur via l'audit
    audit_result = await db.execute(select(Audit).where(Audit.id == claim.audit_id))
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

    return {"original": claim.claim_text, "suggestion": suggestion}
