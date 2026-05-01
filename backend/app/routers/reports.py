from __future__ import annotations

import logging
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user, require_pro
from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)
from app.config import settings
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.evidence import EvidenceFile  # noqa: F401 — needed for selectinload
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
            selectinload(Audit.claims).selectinload(Claim.evidence_files),
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

    # Supprimer l'ancien PDF s'il existe (le nonce dans le nom change à chaque regénération)
    if audit.pdf_url:
        old_path = (Path(settings.PDF_STORAGE_PATH).resolve() / audit.pdf_url).resolve()
        if str(old_path).startswith(str(Path(settings.PDF_STORAGE_PATH).resolve())) and old_path.is_file():
            old_path.unlink(missing_ok=True)

    filename, sha256 = generate_audit_pdf(audit, audit.organization)

    # Regénérer le token à chaque nouveau PDF (90 jours d'expiration)
    audit.share_token = secrets.token_urlsafe(32)
    audit.share_token_expires_at = datetime.now(timezone.utc) + timedelta(days=90)
    audit.pdf_url = filename
    audit.pdf_sha256 = sha256
    await db.commit()

    return {
        "message": "Rapport généré avec succès",
        "pdf_url": filename,
        "share_token": audit.share_token,
        "pdf_sha256": sha256,
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
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Audit)
        .where(
            Audit.id == audit_id,
            Audit.share_token == token,
            Audit.share_token_expires_at > now,
        )
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


import re

from app.models.client_access import ClientAccess


def _make_token(company_name: str) -> str:
    """Génère un token lisible : naturalia-service-2026-{random22chars}"""
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")[:25]
    year = datetime.now(timezone.utc).year
    return f"{slug}-{year}-{secrets.token_urlsafe(12)}"


def _ca_to_dict(ca: ClientAccess, frontend_url: str) -> dict:
    return {
        "client_url": f"{frontend_url}/client/{ca.token}",
        "client_email": ca.client_email,
        "validity_days": ca.validity_days,
        "expires_at": ca.expires_at.isoformat() if ca.expires_at else None,
        "is_revoked": ca.is_revoked,
        "created_at": ca.created_at.isoformat() if ca.created_at else None,
        "last_opened_at": ca.last_opened_at.isoformat() if ca.last_opened_at else None,
        "pdf_downloaded_at": ca.pdf_downloaded_at.isoformat() if ca.pdf_downloaded_at else None,
        "zip_downloaded_at": ca.zip_downloaded_at.isoformat() if ca.zip_downloaded_at else None,
    }


class ClientAccessRequest(BaseModel):
    client_email: str
    validity_days: Optional[int] = 90  # None = illimité
    custom_message: Optional[str] = None


@router.post("/{audit_id}/client-access")
async def create_client_access(
    audit_id: UUID,
    data: ClientAccessRequest,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Crée ou recrée un accès client sécurisé et envoie le lien par email."""
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
        .options(selectinload(Audit.organization))
    )
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit introuvable")
    if not audit.pdf_url:
        raise HTTPException(
            status_code=400,
            detail="Générez d'abord le rapport PDF avant de créer l'accès client.",
        )

    cabinet_name = audit.organization.name if audit.organization else "GreenAudit"
    now = datetime.now(timezone.utc)
    expires_at = None
    if data.validity_days:
        from datetime import timedelta
        expires_at = now + timedelta(days=data.validity_days)

    # Supprimer l'accès existant s'il y en a un
    existing = await db.execute(
        select(ClientAccess).where(ClientAccess.audit_id == audit_id)
    )
    old_ca = existing.scalar_one_or_none()
    if old_ca:
        await db.delete(old_ca)
        await db.flush()

    ca = ClientAccess(
        audit_id=audit_id,
        token=_make_token(audit.company_name),
        client_email=data.client_email,
        validity_days=data.validity_days,
        expires_at=expires_at,
    )
    db.add(ca)
    await db.commit()
    await db.refresh(ca)

    client_url = f"{settings.FRONTEND_URL}/client/{ca.token}"

    # Envoi email
    validity_str = f"{data.validity_days} jours" if data.validity_days else "illimitée"
    default_message = (
        f"{cabinet_name} met à votre disposition le rapport d'audit de conformité "
        f"anti-greenwashing pour {audit.company_name}.\n\n"
        f"Accédez à votre espace sécurisé :\n{client_url}\n\n"
        f"Depuis cet espace vous pouvez :\n"
        f"- Consulter le résultat de l'analyse de vos allégations\n"
        f"- Télécharger le rapport PDF\n"
        f"- Télécharger le dossier de preuves (SHA-256 + traçabilité)\n\n"
        f"Ce lien est valable {validity_str} et vous est réservé.\n\n"
        f"Cordialement,\n{cabinet_name}"
    )
    body = data.custom_message or default_message
    # Injecter le lien dans le message custom s'il n'y est pas déjà
    if data.custom_message and client_url not in data.custom_message:
        body = f"{data.custom_message}\n\n{client_url}"

    email_sent = False
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    if smtp_user and smtp_password:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = data.client_email
            msg["Subject"] = f"Votre rapport d'audit anti-greenwashing — {audit.company_name}"
            msg.attach(MIMEText(body, "plain", "utf-8"))
            with smtplib.SMTP("smtp-relay.brevo.com", 587, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            email_sent = True
            logger.info(f"Accès client envoyé à {data.client_email} pour audit {audit_id}")
        except Exception as e:
            logger.error(f"Erreur envoi email accès client: {e}")

    result_dict = _ca_to_dict(ca, settings.FRONTEND_URL)
    result_dict["email_sent"] = email_sent
    return result_dict


@router.get("/{audit_id}/client-access")
async def get_client_access(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retourne le statut de l'accès client (tracking inclus)."""
    # Vérifier ownership
    audit_result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
    )
    if not audit_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Audit introuvable")

    ca_result = await db.execute(
        select(ClientAccess).where(ClientAccess.audit_id == audit_id)
    )
    ca = ca_result.scalar_one_or_none()
    if not ca:
        return {"exists": False}

    result = _ca_to_dict(ca, settings.FRONTEND_URL)
    result["exists"] = True
    return result


@router.delete("/{audit_id}/client-access", status_code=204, response_class=Response)
async def revoke_client_access(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Révoque l'accès client (le lien devient immédiatement inaccessible)."""
    audit_result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
    )
    if not audit_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Audit introuvable")

    ca_result = await db.execute(
        select(ClientAccess).where(ClientAccess.audit_id == audit_id)
    )
    ca = ca_result.scalar_one_or_none()
    if ca:
        ca.is_revoked = True
        await db.commit()
