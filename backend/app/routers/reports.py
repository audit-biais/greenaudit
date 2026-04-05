from __future__ import annotations

import secrets
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user, require_pro
from app.database import get_db
from app.config import settings
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.organization import Organization
from app.models.user import User
from app.schemas.claim_result import AuditResultsResponse
from app.services.pdf_generator import generate_audit_pdf

router = APIRouter(prefix="/api/audits", tags=["reports"])


async def _load_completed_audit(
    audit_id: UUID, user: User, db: AsyncSession
) -> Audit:
    """Charge un audit completed avec claims, results et organisation."""
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
        .options(
            selectinload(Audit.claims).selectinload(Claim.results),
            selectinload(Audit.organization),
        )
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
            detail="L'audit doit être analysé avant de générer un rapport",
        )
    return audit


@router.post("/{audit_id}/report", status_code=status.HTTP_201_CREATED)
async def generate_report(
    audit_id: UUID,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Générer le rapport PDF pour un audit analysé."""
    audit = await _load_completed_audit(audit_id, user, db)

    filename = generate_audit_pdf(audit, audit.organization)

    if not audit.share_token:
        audit.share_token = secrets.token_urlsafe(32)

    audit.pdf_url = filename
    await db.commit()

    return {
        "message": "Rapport généré avec succès",
        "pdf_url": filename,
        "share_token": audit.share_token,
    }


@router.get("/{audit_id}/report/download")
async def download_report(
    audit_id: UUID,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Télécharger le rapport PDF d'un audit."""
    result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
    )
    audit = result.scalar_one_or_none()

    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit introuvable",
        )
    if not audit.pdf_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun rapport généré pour cet audit",
        )

    storage = Path(settings.PDF_STORAGE_PATH).resolve()
    filepath = (storage / audit.pdf_url).resolve()
    if not str(filepath).startswith(str(storage)) or not filepath.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier PDF introuvable sur le serveur",
        )

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=f"rapport_greenaudit_{audit.company_name}.pdf",
    )


@router.get("/{audit_id}/share/{token}", response_model=AuditResultsResponse)
async def shared_audit_results(
    audit_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> AuditResultsResponse:
    """
    Lien de partage client — lecture seule, pas d'authentification.
    Vérifie que le token correspond à l'audit.
    """
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id, Audit.share_token == token)
        .options(selectinload(Audit.claims).selectinload(Claim.results))
    )
    audit = result.scalar_one_or_none()

    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lien de partage invalide ou expiré",
        )

    return AuditResultsResponse(
        audit_id=audit.id,
        company_name=audit.company_name,
        status=audit.status,
        total_claims=audit.total_claims,
        conforming_claims=audit.conforming_claims,
        non_conforming_claims=audit.non_conforming_claims,
        at_risk_claims=audit.at_risk_claims,
        global_score=float(audit.global_score) if audit.global_score is not None else None,
        risk_level=audit.risk_level,
        claims=audit.claims,
    )
