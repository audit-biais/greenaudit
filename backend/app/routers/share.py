from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.client_access import ClientAccess

router = APIRouter(prefix="/api/share", tags=["share"])


async def _get_client_access(token: str, db: AsyncSession) -> tuple[ClientAccess, Audit]:
    """Valide le token et retourne (ClientAccess, Audit). Lève 404 si invalide/révoqué/expiré."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ClientAccess)
        .where(ClientAccess.token == token, ClientAccess.is_revoked == False)  # noqa: E712
        .options(
            selectinload(ClientAccess.audit).selectinload(Audit.claims).selectinload(Claim.results),
            selectinload(ClientAccess.audit).selectinload(Audit.claims).selectinload(Claim.evidence_files),
            selectinload(ClientAccess.audit).selectinload(Audit.organization),
        )
    )
    ca = result.scalar_one_or_none()
    if not ca:
        raise HTTPException(status_code=404, detail="Lien invalide ou révoqué")
    if ca.expires_at and ca.expires_at < now:
        raise HTTPException(status_code=404, detail="Lien expiré")
    return ca, ca.audit


@router.get("/{token}")
async def get_shared_audit(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Page client — données audit en lecture seule. Met à jour last_opened_at."""
    ca, audit = await _get_client_access(token, db)

    # Tracking ouverture
    ca.last_opened_at = datetime.now(timezone.utc)
    await db.commit()

    org = audit.organization
    claims_data = []
    for c in audit.claims:
        if getattr(c, "is_false_positive", False):
            continue
        claims_data.append({
            "id": str(c.id),
            "claim_text": c.claim_text,
            "overall_verdict": c.overall_verdict,
            "is_corrected": getattr(c, "is_corrected", False),
            "evidence_count": len(c.evidence_files),
        })

    return {
        "audit_id": str(audit.id),
        "company_name": audit.company_name,
        "sector": audit.sector,
        "website_url": audit.website_url,
        "status": audit.status,
        "global_score": float(audit.global_score) if audit.global_score is not None else None,
        "risk_level": audit.risk_level,
        "total_claims": audit.total_claims,
        "conforming_claims": audit.conforming_claims,
        "at_risk_claims": audit.at_risk_claims,
        "non_conforming_claims": audit.non_conforming_claims,
        "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
        "has_pdf": bool(audit.pdf_url),
        "has_evidence": any(len(c.evidence_files) > 0 for c in audit.claims),
        "claims": claims_data,
        "branding": {
            "cabinet_name": org.name if org else "GreenAudit",
            "primary_color": (org.brand_primary_color if org else None) or "#1a5c3a",
            "secondary_color": (org.brand_secondary_color if org else None) or "#2E7D32",
            "has_logo": bool(org and org.logo_data),
        },
    }


@router.get("/{token}/logo")
async def get_shared_logo(token: str, db: AsyncSession = Depends(get_db)) -> Response:
    ca, audit = await _get_client_access(token, db)
    org = audit.organization
    if not org or not org.logo_data:
        raise HTTPException(status_code=404, detail="Aucun logo")
    return Response(
        content=org.logo_data,
        media_type=org.logo_content_type or "image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/{token}/pdf")
async def download_shared_pdf(token: str, db: AsyncSession = Depends(get_db)) -> Response:
    """Téléchargement PDF client. Met à jour pdf_downloaded_at."""
    ca, audit = await _get_client_access(token, db)
    if not audit.pdf_url:
        raise HTTPException(status_code=404, detail="Aucun rapport PDF disponible")

    storage = Path(settings.PDF_STORAGE_PATH).resolve()
    filepath = (storage / audit.pdf_url).resolve()
    if not str(filepath).startswith(str(storage)) or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Fichier PDF introuvable")

    with open(filepath, "rb") as f:
        content = f.read()

    ca.pdf_downloaded_at = datetime.now(timezone.utc)
    await db.commit()

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="rapport_greenaudit_{audit.company_name}.pdf"'
        },
    )


@router.get("/{token}/zip")
async def download_shared_zip(token: str, db: AsyncSession = Depends(get_db)) -> Response:
    """Téléchargement ZIP client. Met à jour zip_downloaded_at."""
    ca, audit = await _get_client_access(token, db)
    org = audit.organization

    claims_result = await db.execute(
        select(Claim)
        .where(Claim.audit_id == audit.id)
        .options(selectinload(Claim.evidence_files))
        .order_by(Claim.created_at)
    )
    claims = list(claims_result.scalars().all())

    cabinet_name = org.name if org else "GreenAudit"
    now = datetime.now(timezone.utc)
    zip_buffer = io.BytesIO()
    tracability_lines: list[str] = []
    total = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, claim in enumerate(claims, 1):
            for evidence in claim.evidence_files:
                folder = f"allegation_{i}_{claim.claim_text[:30].replace('/', '_').replace(' ', '_')}"
                zf.writestr(f"{folder}/{evidence.filename}", evidence.file_data)
                sha256 = hashlib.sha256(evidence.file_data).hexdigest()
                tracability_lines.append(f"  [{evidence.filename}]  SHA-256 : {sha256}")
                total += 1

        if total == 0:
            raise HTTPException(status_code=404, detail="Aucune pièce justificative disponible")

        tracability_content = (
            "DOSSIER DE PREUVES — TRACABILITE\n"
            "=================================\n\n"
            f"Entreprise auditee : {audit.company_name}\n"
            f"Cabinet RSE        : {cabinet_name}\n"
            f"Date               : {now.strftime('%d/%m/%Y')}\n"
            f"Heure (UTC)        : {now.strftime('%H:%M:%S')}\n"
            f"Nombre de fichiers : {total}\n\n"
            "Empreintes SHA-256 des fichiers :\n"
            "---------------------------------\n"
            + "\n".join(tracability_lines)
            + "\n\n"
            "Ce fichier atteste de l'integrite des preuves deposees dans GreenAudit\n"
            "et peut etre presente en cas de controle DGCCRF.\n"
        )
        zf.writestr("Tracabilite.txt", tracability_content.encode("utf-8"))

    zip_buffer.seek(0)
    filename = f"dossier_preuves_{audit.company_name.replace(' ', '_')}.zip"

    ca.zip_downloaded_at = datetime.now(timezone.utc)
    await db.commit()

    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
