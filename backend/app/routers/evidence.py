from __future__ import annotations

import io
import zipfile
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.evidence import EvidenceFile
from app.models.user import User

router = APIRouter(tags=["evidence"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo

ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def _get_user_claim(claim_id: UUID, user: User, db: AsyncSession) -> Claim:
    result = await db.execute(
        select(Claim)
        .join(Audit)
        .where(Claim.id == claim_id, Audit.organization_id == user.organization_id)
        .options(selectinload(Claim.evidence_files))
    )
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Allégation introuvable")
    return claim


ALLOWED_DOCUMENT_TYPES = {"ecolabel", "certification", "rapport_interne", "autre"}


@router.post("/api/claims/{claim_id}/evidence", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    claim_id: UUID,
    file: UploadFile = File(...),
    document_type: str = Form(default="autre"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload une pièce justificative pour une allégation.

    document_type : "ecolabel" | "certification" | "rapport_interne" | "autre"
    - "ecolabel" : EU Ecolabel, Ange Bleu, ISO 14024 Type I... débloque le verdict conforme
      sur les allégations génériques (Art. 2(s) EmpCo)
    """
    claim = await _get_user_claim(claim_id, user, db)

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. Utilisez PDF, JPEG, PNG ou Word.",
        )

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        document_type = "autre"

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux. Maximum : 10 Mo.")

    evidence = EvidenceFile(
        claim_id=claim_id,
        filename=file.filename or "document",
        content_type=file.content_type,
        file_data=contents,
        file_size=len(contents),
        document_type=document_type,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    return {
        "id": str(evidence.id),
        "filename": evidence.filename,
        "content_type": evidence.content_type,
        "file_size": evidence.file_size,
        "document_type": evidence.document_type,
        "uploaded_at": evidence.uploaded_at.isoformat(),
    }


@router.get("/api/claims/{claim_id}/evidence")
async def list_evidence(
    claim_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Liste les pièces justificatives d'une allégation."""
    claim = await _get_user_claim(claim_id, user, db)

    return [
        {
            "id": str(e.id),
            "filename": e.filename,
            "content_type": e.content_type,
            "file_size": e.file_size,
            "document_type": e.document_type,
            "uploaded_at": e.uploaded_at.isoformat(),
        }
        for e in claim.evidence_files
    ]


@router.get("/api/evidence/{evidence_id}/download")
async def download_evidence(
    evidence_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Télécharger une pièce justificative."""
    result = await db.execute(
        select(EvidenceFile)
        .join(Claim)
        .join(Audit)
        .where(
            EvidenceFile.id == evidence_id,
            Audit.organization_id == user.organization_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    return Response(
        content=evidence.file_data,
        media_type=evidence.content_type,
        headers={"Content-Disposition": f'attachment; filename="{evidence.filename}"'},
    )


@router.delete("/api/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_evidence(
    evidence_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprimer une pièce justificative."""
    result = await db.execute(
        select(EvidenceFile)
        .join(Claim)
        .join(Audit)
        .where(
            EvidenceFile.id == evidence_id,
            Audit.organization_id == user.organization_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    await db.delete(evidence)
    await db.commit()


@router.get("/api/audits/{audit_id}/evidence/download-zip")
async def download_evidence_zip(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Télécharger toutes les pièces justificatives de l'audit en un ZIP (dossier DGCCRF)."""
    audit_result = await db.execute(
        select(Audit).where(
            Audit.id == audit_id,
            Audit.organization_id == user.organization_id,
        )
    )
    audit = audit_result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit introuvable")

    claims_result = await db.execute(
        select(Claim)
        .where(Claim.audit_id == audit_id)
        .options(selectinload(Claim.evidence_files))
        .order_by(Claim.created_at)
    )
    claims = list(claims_result.scalars().all())

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        total = 0
        for i, claim in enumerate(claims, 1):
            for evidence in claim.evidence_files:
                folder = f"allegation_{i}_{claim.claim_text[:30].replace('/', '_').replace(' ', '_')}"
                zf.writestr(f"{folder}/{evidence.filename}", evidence.file_data)
                total += 1

    if total == 0:
        raise HTTPException(status_code=404, detail="Aucune pièce justificative à télécharger")

    zip_buffer.seek(0)
    filename = f"dossier_preuves_{audit.company_name.replace(' ', '_')}.zip"

    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
