from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user, require_pro
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.models.evidence import EvidenceFile
from app.models.organization import Organization
from app.models.user import User
from app.services.scoring import calculate_global_score, compute_verdict_counts

router = APIRouter(tags=["evidence"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo

# Priorité des types de document pour la règle 6
_VAULT_STRONG = {"ecolabel", "certification"}   # → conforme
_VAULT_WEAK   = {"rapport_interne", "autre"}     # → risque


async def _refresh_justification_from_vault(claim_id: UUID, db: AsyncSession) -> None:
    """
    Réévalue le critère 'justification' (règle 6) d'après le vault.
    Met à jour ClaimResult, overall_verdict de la claim et score global de l'audit.
    Appelé après chaque upload ou suppression de preuve.
    """
    # Charger la claim avec résultats et fichiers vault
    result = await db.execute(
        select(Claim)
        .where(Claim.id == claim_id)
        .options(
            selectinload(Claim.evidence_files),
            selectinload(Claim.results),
        )
    )
    claim = result.scalar_one_or_none()
    if not claim:
        return

    # Trouver le ClaimResult justification — si absent l'audit n'a pas encore été analysé
    just_result = next((r for r in claim.results if r.criterion == "justification"), None)
    if not just_result:
        return

    evidence_files = claim.evidence_files
    doc_types = {ef.document_type for ef in evidence_files}

    if doc_types & _VAULT_STRONG:
        just_result.verdict = "conforme"
        just_result.explanation = (
            "L'allégation est étayée par une preuve de qualité élevée "
            "(certification tierce ou écolabel reconnu) déposée dans le vault. "
            "Ce niveau de justification est conforme à l'Art. 6.1(b) EmpCo."
        )
        just_result.recommendation = None
    elif doc_types & _VAULT_WEAK:
        just_result.verdict = "risque"
        just_result.explanation = (
            "L'allégation est étayée par un document interne ou non certifié. "
            "Cette preuve est considérée comme faible car non vérifiée par un tiers."
        )
        just_result.recommendation = (
            "Obtenir une certification tierce ou un écolabel reconnu "
            "pour renforcer la défendabilité de cette allégation."
        )
    else:
        # Vault vide — revenir à la logique originale (claim.has_proof / proof_type)
        from app.services.analysis_engine import rule_justification
        original = rule_justification(claim, scan_mode=False)
        just_result.verdict = original.verdict
        just_result.explanation = original.explanation
        just_result.recommendation = original.recommendation

    # Recompute overall_verdict de la claim
    verdicts = [r.verdict for r in claim.results]
    nc = sum(1 for v in verdicts if v == "non_conforme")
    rq = sum(1 for v in verdicts if v == "risque")
    claim.overall_verdict = "non_conforme" if nc > 0 else ("risque" if rq >= 2 else "conforme")

    # Recompute score global de l'audit
    audit_result = await db.execute(
        select(Audit)
        .where(Audit.id == claim.audit_id)
        .options(selectinload(Audit.claims))
    )
    audit = audit_result.scalar_one_or_none()
    if audit:
        all_verdicts = [c.overall_verdict for c in audit.claims if c.overall_verdict and not c.is_false_positive]
        counts = compute_verdict_counts(all_verdicts)
        score, risk_level = calculate_global_score(
            conforming=counts["conforme"],
            at_risk=counts["risque"],
            non_conforming=counts["non_conforme"],
        )
        audit.global_score = score
        audit.risk_level = risk_level
        audit.conforming_claims = counts["conforme"]
        audit.at_risk_claims = counts["risque"]
        audit.non_conforming_claims = counts["non_conforme"]

    await db.commit()

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
    user: User = Depends(require_pro),
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

    # Réévaluer règle 6 + score global en fonction du vault mis à jour
    await _refresh_justification_from_vault(claim_id, db)

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

    deleted_claim_id = evidence.claim_id
    await db.delete(evidence)
    await db.commit()

    # Réévaluer règle 6 + score global après suppression de la preuve
    await _refresh_justification_from_vault(deleted_claim_id, db)


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

    # Charger le nom du cabinet RSE
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    cabinet_name = org.name if org else "Cabinet inconnu"

    zip_buffer = io.BytesIO()
    now = datetime.now(timezone.utc)
    tracability_lines: list[str] = []
    total = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, claim in enumerate(claims, 1):
            for evidence in claim.evidence_files:
                folder = f"allegation_{i}_{claim.claim_text[:30].replace('/', '_').replace(' ', '_')}"
                zf.writestr(f"{folder}/{evidence.filename}", evidence.file_data)
                sha256 = hashlib.sha256(evidence.file_data).hexdigest()
                tracability_lines.append(
                    f"  [{evidence.filename}]  SHA-256 : {sha256}"
                )
                total += 1

        if total == 0:
            raise HTTPException(status_code=404, detail="Aucune pièce justificative à télécharger")

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

    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
