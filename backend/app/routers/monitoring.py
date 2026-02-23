from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_partner
from app.database import get_db
from app.models.audit import Audit
from app.models.monitoring_alert import MonitoringAlert
from app.models.monitoring_config import MonitoringConfig
from app.models.partner import Partner
from app.schemas.monitoring import (
    MonitoringAlertResponse,
    MonitoringConfigCreate,
    MonitoringConfigResponse,
)
from app.services.monitoring_service import run_monitoring_check

router = APIRouter(tags=["monitoring"])


async def _get_audit_for_partner(
    audit_id: UUID, partner: Partner, db: AsyncSession
) -> Audit:
    result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.partner_id == partner.id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit introuvable"
        )
    return audit


def _build_config_response(
    config: MonitoringConfig,
) -> MonitoringConfigResponse:
    unread_count = sum(1 for a in config.alerts if not a.is_read)
    return MonitoringConfigResponse(
        id=config.id,
        audit_id=config.audit_id,
        is_active=config.is_active,
        frequency_days=config.frequency_days,
        last_checked_at=config.last_checked_at,
        next_check_at=config.next_check_at,
        created_at=config.created_at,
        unread_alerts_count=unread_count,
        alerts=[MonitoringAlertResponse.model_validate(a) for a in config.alerts],
    )


@router.post(
    "/api/audits/{audit_id}/monitoring",
    response_model=MonitoringConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enable_monitoring(
    audit_id: UUID,
    data: MonitoringConfigCreate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> MonitoringConfigResponse:
    """Activer le monitoring pour un audit (doit être completed + avoir website_url)."""
    audit = await _get_audit_for_partner(audit_id, partner, db)

    if audit.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le monitoring ne peut être activé que sur un audit terminé",
        )
    if not audit.website_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'audit doit avoir une URL de site web pour activer le monitoring",
        )

    # Vérifier si une config existe déjà
    existing = await db.execute(
        select(MonitoringConfig)
        .where(MonitoringConfig.audit_id == audit_id)
        .options(selectinload(MonitoringConfig.alerts))
    )
    config = existing.scalar_one_or_none()

    if config:
        # Réactiver si désactivé
        config.is_active = True
        config.frequency_days = data.frequency_days
    else:
        now = datetime.now(timezone.utc)
        config = MonitoringConfig(
            audit_id=audit_id,
            frequency_days=data.frequency_days,
            next_check_at=now + timedelta(days=data.frequency_days),
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)

    # Recharger avec les alertes
    result = await db.execute(
        select(MonitoringConfig)
        .where(MonitoringConfig.id == config.id)
        .options(selectinload(MonitoringConfig.alerts))
    )
    config = result.scalar_one()
    return _build_config_response(config)


@router.get(
    "/api/audits/{audit_id}/monitoring",
    response_model=MonitoringConfigResponse,
)
async def get_monitoring(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> MonitoringConfigResponse:
    """Récupérer la config monitoring + alertes d'un audit."""
    await _get_audit_for_partner(audit_id, partner, db)

    result = await db.execute(
        select(MonitoringConfig)
        .where(MonitoringConfig.audit_id == audit_id)
        .options(selectinload(MonitoringConfig.alerts))
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring non configuré pour cet audit",
        )

    return _build_config_response(config)


@router.delete(
    "/api/audits/{audit_id}/monitoring",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def disable_monitoring(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Désactiver le monitoring pour un audit."""
    await _get_audit_for_partner(audit_id, partner, db)

    result = await db.execute(
        select(MonitoringConfig).where(MonitoringConfig.audit_id == audit_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring non configuré pour cet audit",
        )

    config.is_active = False
    await db.commit()


@router.patch(
    "/api/monitoring/alerts/{alert_id}/read",
    response_model=MonitoringAlertResponse,
)
async def mark_alert_read(
    alert_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> MonitoringAlertResponse:
    """Marquer une alerte comme lue."""
    result = await db.execute(
        select(MonitoringAlert)
        .where(MonitoringAlert.id == alert_id)
        .options(
            selectinload(MonitoringAlert.monitoring_config).selectinload(
                MonitoringConfig.audit
            )
        )
    )
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable"
        )

    if alert.monitoring_config.audit.partner_id != partner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé"
        )

    alert.is_read = True
    await db.commit()
    await db.refresh(alert)
    return MonitoringAlertResponse.model_validate(alert)


@router.get(
    "/api/monitoring/unread-summary",
    response_model=dict,
    summary="Nombre d'alertes non lues par audit",
)
async def get_unread_summary(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retourne {audit_id: unread_count} pour tous les audits du partenaire."""
    result = await db.execute(
        select(MonitoringConfig.audit_id, func.count(MonitoringAlert.id))
        .join(MonitoringAlert, MonitoringAlert.monitoring_config_id == MonitoringConfig.id)
        .join(Audit, Audit.id == MonitoringConfig.audit_id)
        .where(
            Audit.partner_id == partner.id,
            MonitoringAlert.is_read == False,  # noqa: E712
        )
        .group_by(MonitoringConfig.audit_id)
    )
    return {str(audit_id): count for audit_id, count in result.all()}


@router.post(
    "/api/audits/{audit_id}/monitoring/check",
    response_model=dict,
    summary="[Debug] Déclencher un check de monitoring immédiat",
)
async def trigger_monitoring_check(
    audit_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Route de debug : déclencher manuellement un check de monitoring."""
    await _get_audit_for_partner(audit_id, partner, db)

    result = await db.execute(
        select(MonitoringConfig).where(
            MonitoringConfig.audit_id == audit_id,
            MonitoringConfig.is_active == True,  # noqa: E712
        )
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring non actif pour cet audit",
        )

    alerts_count = await run_monitoring_check(config.id, db)
    return {"alerts_created": alerts_count}
