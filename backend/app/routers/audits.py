import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List
from uuid import UUID

logger = logging.getLogger(__name__)

_PAGE_MARKER_RE = re.compile(r"=== PAGE: (https?://\S+) ===")

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import check_audit_limit, get_current_user, require_pro
from app.database import get_db
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.models.evidence import EvidenceFile
from app.models.user import User
from pydantic import BaseModel, Field, field_validator

from app.models.organization import Organization
from app.models.client_access import ClientAccess
from app.schemas.audit import AuditCreate, AuditDetailResponse, AuditSummaryResponse, ClientAccessSummary
from app.schemas.claim_result import AuditResultsResponse
from app.services.analysis_engine import analyze_claim, RULES_VERSION
from app.services.regulatory_classifier import classify_claim_regime
from app.services.monitoring_service import scrape_website, extract_claims_with_claude
from app.limiter import limiter, get_user_or_ip
from app.services.scoring import calculate_global_score, compute_verdict_counts

router = APIRouter(prefix="/api/audits", tags=["audits"])


async def _get_user_audit(
    audit_id: UUID,
    user: User,
    db: AsyncSession,
    load_claims: bool = False,
) -> Audit:
    """Helper : récupère un audit appartenant à l'organisation de l'utilisateur courant."""
    stmt = select(Audit).where(
        Audit.id == audit_id,
        Audit.organization_id == user.organization_id,
    )
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
    user: User = Depends(check_audit_limit),
    db: AsyncSession = Depends(get_db),
) -> Audit:
    """Créer un audit (draft)."""
    if not user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous devez appartenir à une organisation pour créer un audit",
        )
    audit = Audit(
        organization_id=user.organization_id,
        company_name=data.company_name,
        sector=data.sector,
        website_url=data.website_url,
        contact_email=data.contact_email,
        country=data.country,
        created_by_user_id=user.id,
    )
    db.add(audit)
    await db.flush()

    # Incrémenter le compteur d'audits de l'organisation
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    if org:
        org.audits_this_month = (org.audits_this_month or 0) + 1

    await db.commit()
    await db.refresh(audit)
    return audit


@router.get("", response_model=List[AuditSummaryResponse])
async def list_audits(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Lister les audits de l'organisation courante avec statut coffre-fort client."""
    if not user.organization_id:
        return []
    audits_result = await db.execute(
        select(Audit)
        .where(Audit.organization_id == user.organization_id)
        .order_by(Audit.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    audits = list(audits_result.scalars().all())

    # Charger les client_accesses en une seule requête
    audit_ids = [a.id for a in audits]
    ca_result = await db.execute(
        select(ClientAccess).where(ClientAccess.audit_id.in_(audit_ids))
    )
    ca_by_audit = {ca.audit_id: ca for ca in ca_result.scalars().all()}

    response = []
    for audit in audits:
        ca = ca_by_audit.get(audit.id)
        ca_summary = None
        if ca:
            ca_summary = ClientAccessSummary(
                exists=True,
                is_revoked=ca.is_revoked,
                client_email=ca.client_email,
                last_opened_at=ca.last_opened_at,
                pdf_downloaded_at=ca.pdf_downloaded_at,
                zip_downloaded_at=ca.zip_downloaded_at,
            )
        response.append(AuditSummaryResponse(
            id=audit.id,
            company_name=audit.company_name,
            sector=audit.sector,
            status=audit.status,
            total_claims=audit.total_claims,
            global_score=audit.global_score,
            risk_level=audit.risk_level,
            created_at=audit.created_at,
            completed_at=audit.completed_at,
            client_access=ca_summary,
        ))
    return response


@router.get("/{audit_id}", response_model=AuditDetailResponse)
async def get_audit(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Audit:
    """Détail d'un audit avec ses claims."""
    return await _get_user_audit(audit_id, user, db, load_claims=True)


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_audit(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprimer un audit (uniquement si draft)."""
    audit = await _get_user_audit(audit_id, user, db)
    if audit.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les audits en brouillon peuvent être supprimés",
        )
    await db.delete(audit)
    await db.commit()


@router.post("/{audit_id}/analyze", response_model=AuditResultsResponse)
@limiter.limit("10/minute", key_func=get_user_or_ip)
async def analyze_audit(
    request: Request,
    audit_id: UUID,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
) -> AuditResultsResponse:
    """
    Lancer l'analyse : applique les 6 règles sur chaque claim,
    calcule le scoring, met à jour le status de l'audit.
    """
    audit = await _get_user_audit(audit_id, user, db, load_claims=True)

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

    # Charger les evidence files pour détecter les écolabels
    claim_ids = [c.id for c in audit.claims]
    evidence_result = await db.execute(
        select(EvidenceFile).where(EvidenceFile.claim_id.in_(claim_ids))
    )
    evidence_by_claim: Dict[UUID, bool] = {}
    for ev in evidence_result.scalars().all():
        if ev.document_type == "ecolabel":
            evidence_by_claim[ev.claim_id] = True

    # Analyser chaque claim
    all_verdicts: List[str] = []
    for claim in audit.claims:
        has_ecolabel = evidence_by_claim.get(claim.id, False)

        # Étape 2 — Classification du régime juridique (avant les 8 règles)
        metadata = {
            "has_label": claim.has_label,
            "label_is_certified": claim.label_is_certified,
            "scope": claim.scope,
            "is_future_commitment": claim.is_future_commitment,
            "has_proof": claim.has_proof,
            "proof_type": claim.proof_type,
        }
        try:
            classification = await classify_claim_regime(claim.claim_text, metadata)
        except Exception as exc:
            logger.warning("classify_claim_regime failed for claim %s: %s", claim.id, exc)
            classification = {"regulatory_basis": "unknown", "regime": "cas_par_cas"}
        claim.regulatory_basis = classification["regulatory_basis"]
        claim.regime = classification["regime"]

        # Étape 3 — Évaluation (8 règles existantes, inchangées)
        results, overall_verdict = analyze_claim(
            claim,
            has_ecolabel_evidence=has_ecolabel,
            country=audit.country,
        )
        claim.overall_verdict = overall_verdict
        # Exclure les faux positifs du scoring
        if not claim.is_false_positive:
            all_verdicts.append(overall_verdict)
        for r in results:
            db.add(r)

    # Calculer le scoring global (hors faux positifs)
    counts = compute_verdict_counts(all_verdicts)
    score, risk_level = calculate_global_score(
        conforming=counts["conforme"],
        at_risk=counts["risque"],
        non_conforming=counts["non_conforme"],
    )

    active_claims = [c for c in audit.claims if not c.is_false_positive]

    # Mettre à jour l'audit
    audit.status = "completed"
    audit.total_claims = len(active_claims)
    audit.conforming_claims = counts["conforme"]
    audit.non_conforming_claims = counts["non_conforme"]
    audit.at_risk_claims = counts["risque"]
    audit.global_score = score
    audit.risk_level = risk_level
    audit.rules_version = RULES_VERSION
    audit.completed_at = datetime.now(timezone.utc)


    await db.commit()

    # Recharger avec les résultats pour la réponse (filtre org conservé)
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
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
        rules_version=audit.rules_version,
        pdf_sha256=audit.pdf_sha256,
        share_token=audit.share_token,
        claims=audit.claims,
    )


@router.get("/{audit_id}/results", response_model=AuditResultsResponse)
async def get_audit_results(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditResultsResponse:
    """Récupérer les résultats détaillés d'un audit analysé."""
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id, Audit.organization_id == user.organization_id)
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
        rules_version=audit.rules_version,
        pdf_sha256=audit.pdf_sha256,
        share_token=audit.share_token,
        claims=audit.claims,
    )


# ---------------------------------------------------------------------------
# Scan de site web (scrape + Claude + analyse automatique)
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    """Requête de scan d'un site web."""
    url: str = Field(min_length=5, max_length=2048, description="URL du site à analyser")
    company_name: str = Field(min_length=1, max_length=255)
    sector: str = Field(default="autre", max_length=100)

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("L'URL doit commencer par http:// ou https://")
        return v


@router.post("/scan", response_model=AuditResultsResponse)
@limiter.limit("5/minute", key_func=get_user_or_ip)
async def scan_website_endpoint(
    request: Request,
    data: ScanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditResultsResponse:
    """
    Scan complet d'un site web :
    1. Scrape le site via Jina Reader
    2. Extrait les allégations environnementales via Claude Haiku
    3. Crée un audit + claims automatiquement
    4. Lance l'analyse des 6 règles EmpCo
    5. Retourne les résultats
    """
    if not user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous devez appartenir à une organisation pour lancer un scan",
        )

    # Limite Starter : 3 scans maximum (hors audit démo)
    if not user.is_superadmin:
        org_check = await db.execute(
            select(Organization).where(Organization.id == user.organization_id)
        )
        org_for_limit = org_check.scalar_one_or_none()
        if org_for_limit and org_for_limit.subscription_plan not in ("partner", "pro", "enterprise"):
            scan_count_result = await db.execute(
                select(Audit).where(
                    Audit.organization_id == user.organization_id,
                    ~Audit.company_name.contains("[DÉMO]"),
                )
            )
            scan_count = len(scan_count_result.scalars().all())
            if scan_count >= 5:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="upgrade_required",
                )

    page_text = await scrape_website(data.url)
    if not page_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Impossible de récupérer le contenu du site. "
                "Vérifiez que l'URL est publique et accessible sans connexion. "
                "Essayez avec la page RSE ou développement durable du site (ex: https://exemple.fr/rse)."
            ),
        )

    # Traitement par section — source_url assignée directement depuis le marqueur
    _parts = _PAGE_MARKER_RE.split(page_text)
    if len(_parts) >= 3:
        _sections = [
            (_parts[i], _parts[i + 1].strip())
            for i in range(1, len(_parts) - 1, 2)
            if _parts[i + 1].strip()
        ]
        _results = await asyncio.gather(*[
            extract_claims_with_claude(
                _text, [],
                audited_company_name=data.company_name,
                audited_website_url=data.url,
            )
            for _, _text in _sections
        ])
        _seen: set = set()
        claims_items: list = []
        for (_url, _), _items in zip(_sections, _results):
            for _item in _items:
                _ct = _item["claim_text"]
                _key = _ct.lower().strip().strip("«»\"'.,;:!?")
                if _key not in _seen:
                    _seen.add(_key)
                    claims_items.append({"claim_text": _ct, "source_url": _url})

        # Supprimer les claims qui sont un préfixe d'une claim plus longue
        _norm_keys = [c["claim_text"].lower().strip().strip("«»\"'.,;:!?") for c in claims_items]
        claims_items = [
            item for i, item in enumerate(claims_items)
            if not any(
                j != i and _norm_keys[j].startswith(_norm_keys[i]) and len(_norm_keys[i]) >= 30
                for j in range(len(_norm_keys))
            )
        ]
    else:
        claims_items = await extract_claims_with_claude(
            page_text, [],
            audited_company_name=data.company_name,
            audited_website_url=data.url,
        )

    if not claims_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Aucune allégation environnementale détectée sur ce site. "
                "Essayez avec une URL plus spécifique : page RSE, développement durable, engagements ou impact."
            ),
        )

    # Créer l'audit
    audit = Audit(
        organization_id=user.organization_id,
        company_name=data.company_name,
        sector=data.sector,
        website_url=data.url,
        created_by_user_id=user.id,
    )
    db.add(audit)
    await db.flush()

    # Incrémenter le compteur d'audits de l'organisation
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    if org:
        org.audits_this_month = (org.audits_this_month or 0) + 1

    # Créer les claims (mode simplifié — scope web, pas de preuve déclarée)
    for item in claims_items:
        claim = Claim(
            audit_id=audit.id,
            claim_text=item["claim_text"],
            source_url=item.get("source_url"),
            support_type="web",
            scope="entreprise",
            has_proof=False,
            proof_type="aucune",
            has_label=False,
            is_future_commitment=False,
            has_independent_verification=False,
        )
        db.add(claim)

    await db.flush()

    # Recharger avec les claims (filtre org conservé)
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit.id, Audit.organization_id == user.organization_id)
        .options(selectinload(Audit.claims))
    )
    audit = result.scalar_one()

    # Analyser (scan = pas d'écolabel dans vault, country par défaut "fr")
    all_verdicts: List[str] = []
    for claim in audit.claims:
        metadata = {
            "has_label": claim.has_label,
            "label_is_certified": claim.label_is_certified,
            "scope": claim.scope,
            "is_future_commitment": claim.is_future_commitment,
            "has_proof": claim.has_proof,
            "proof_type": claim.proof_type,
        }
        try:
            classification = await classify_claim_regime(claim.claim_text, metadata)
        except Exception as exc:
            logger.warning("classify_claim_regime failed for claim %s: %s", claim.id, exc)
            classification = {"regulatory_basis": "unknown", "regime": "cas_par_cas"}
        claim.regulatory_basis = classification["regulatory_basis"]
        claim.regime = classification["regime"]
        results, overall_verdict = analyze_claim(claim, has_ecolabel_evidence=False, country="fr", scan_mode=True)
        claim.overall_verdict = overall_verdict
        if not claim.is_false_positive:
            all_verdicts.append(overall_verdict)
        for r in results:
            db.add(r)

    counts = compute_verdict_counts(all_verdicts)
    score, risk_level = calculate_global_score(
        conforming=counts["conforme"],
        at_risk=counts["risque"],
        non_conforming=counts["non_conforme"],
    )

    active_claims = [c for c in audit.claims if not c.is_false_positive]

    # Scan → in_progress pour permettre à l'utilisateur d'ajouter des allégations manuellement
    audit.status = "in_progress"
    audit.total_claims = len(active_claims)
    audit.conforming_claims = counts["conforme"]
    audit.non_conforming_claims = counts["non_conforme"]
    audit.at_risk_claims = counts["risque"]
    audit.global_score = score
    audit.risk_level = risk_level
    audit.rules_version = RULES_VERSION

    await db.commit()

    # Recharger avec résultats complets (filtre org conservé)
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit.id, Audit.organization_id == user.organization_id)
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
        rules_version=audit.rules_version,
        pdf_sha256=audit.pdf_sha256,
        share_token=audit.share_token,
        claims=audit.claims,
    )
