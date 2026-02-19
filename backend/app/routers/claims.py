from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_partner
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.partner import Partner
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate

router = APIRouter(tags=["claims"])


async def _get_partner_audit(
    audit_id: UUID, partner: Partner, db: AsyncSession
) -> Audit:
    """Helper : vérifie que l'audit appartient au partenaire."""
    result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.partner_id == partner.id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit introuvable",
        )
    return audit


async def _get_partner_claim(
    claim_id: UUID, partner: Partner, db: AsyncSession, load_results: bool = False
) -> Claim:
    """Helper : récupère une claim dont l'audit appartient au partenaire."""
    stmt = (
        select(Claim)
        .join(Audit)
        .where(Claim.id == claim_id, Audit.partner_id == partner.id)
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
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> Claim:
    """Ajouter une claim à un audit."""
    audit = await _get_partner_audit(audit_id, partner, db)

    if audit.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'ajouter une claim à un audit terminé",
        )

    claim = Claim(audit_id=audit.id, **data.model_dump())
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim


@router.get(
    "/api/audits/{audit_id}/claims",
    response_model=List[ClaimResponse],
)
async def list_claims(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> List[Claim]:
    """Lister les claims d'un audit."""
    await _get_partner_audit(audit_id, partner, db)

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
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> Claim:
    """Modifier une claim existante."""
    claim = await _get_partner_claim(claim_id, partner, db, load_results=True)

    # Vérifier que l'audit n'est pas terminé
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


@router.delete("/api/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    claim_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Supprimer une claim."""
    claim = await _get_partner_claim(claim_id, partner, db)

    result = await db.execute(select(Audit).where(Audit.id == claim.audit_id))
    audit = result.scalar_one()
    if audit.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer une claim d'un audit terminé",
        )

    await db.delete(claim)
    await db.commit()
