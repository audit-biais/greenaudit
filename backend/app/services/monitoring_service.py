from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session
from app.models.audit import Audit
from app.models.monitoring_alert import MonitoringAlert
from app.models.monitoring_config import MonitoringConfig

logger = logging.getLogger(__name__)

# Pages RSE/durabilité courantes à essayer en plus de la page d'accueil
_RSE_PATHS = [
    "",
    "/developpement-durable",
    "/rse",
    "/engagement",
    "/sustainability",
    "/environnement",
    "/responsabilite",
]


async def scrape_website(url: str) -> str:
    """
    Scrape la page d'accueil + pages RSE/durabilité d'un site.
    Retourne le texte brut concaténé, limité à 8 000 caractères.
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    base_url = url.rstrip("/")
    collected_text = ""

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GreenAuditBot/1.0)"},
    ) as client:
        for path in _RSE_PATHS:
            target = f"{base_url}{path}"
            try:
                response = await client.get(target)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                # Meta description
                meta = soup.find("meta", attrs={"name": "description"})
                if meta and meta.get("content"):
                    collected_text += meta["content"] + "\n"

                # Titres et paragraphes
                for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
                    text = tag.get_text(strip=True)
                    if text:
                        collected_text += text + "\n"

                if len(collected_text) >= 8000:
                    break

            except Exception as exc:
                logger.debug(f"Impossible de scraper {target}: {exc}")
                continue

    return collected_text[:8000]


async def extract_claims_with_claude(
    text: str, existing_claims: List[str]
) -> List[str]:
    """
    Utilise Claude Haiku pour extraire les nouvelles allégations environnementales.
    Retourne uniquement les claims absentes de existing_claims.
    """
    if not settings.ANTHROPIC_API_KEY or not text.strip():
        return []

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        existing_str = (
            "\n".join(f"- {c}" for c in existing_claims)
            if existing_claims
            else "Aucune"
        )

        prompt = f"""Analyse le texte suivant extrait d'un site web et identifie TOUTES les allégations environnementales ou de durabilité (ex: "produit éco-responsable", "neutre en carbone", "emballage recyclé", etc.).

Allégations déjà connues (ne pas les répéter) :
{existing_str}

Texte du site :
{text}

Retourne UNIQUEMENT les nouvelles allégations (absentes de la liste ci-dessus) au format JSON :
{{"claims": ["allégation 1", "allégation 2"]}}

Si aucune nouvelle allégation, retourne : {{"claims": []}}
Réponds UNIQUEMENT avec le JSON, sans texte autour."""

        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()

        # Extraire le JSON si entouré de markdown code blocks
        if "```" in response_text:
            parts = response_text.split("```")
            response_text = parts[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        data = json.loads(response_text)
        return [str(c) for c in data.get("claims", [])]

    except Exception as exc:
        logger.error(f"Erreur Claude API lors de l'extraction: {exc}")
        return []


async def run_monitoring_check(config_id: UUID, db: AsyncSession) -> int:
    """
    Exécute un check de monitoring pour une config donnée.
    Retourne le nombre d'alertes créées.
    """
    result = await db.execute(
        select(MonitoringConfig)
        .where(MonitoringConfig.id == config_id)
        .options(selectinload(MonitoringConfig.audit).selectinload(Audit.claims))
    )
    config = result.scalar_one_or_none()

    if config is None or not config.is_active:
        return 0

    audit = config.audit
    if not audit or not audit.website_url:
        logger.warning(f"Config {config_id} : audit sans website_url, skip")
        return 0

    existing_claims = [claim.claim_text for claim in audit.claims]

    logger.info(f"Monitoring check — audit {audit.id} ({audit.website_url})")
    page_text = await scrape_website(audit.website_url)

    if not page_text.strip():
        logger.warning(f"Aucun texte récupéré pour {audit.website_url}")
        _update_timestamps(config)
        await db.commit()
        return 0

    new_claims = await extract_claims_with_claude(page_text, existing_claims)

    alerts_created = 0
    for claim_text in new_claims:
        alert = MonitoringAlert(
            monitoring_config_id=config.id,
            claim_text=claim_text,
            source_url=audit.website_url,
        )
        db.add(alert)
        alerts_created += 1

    _update_timestamps(config)
    await db.commit()

    logger.info(
        f"Monitoring check terminé — audit {audit.id} : {alerts_created} nouvelles alertes"
    )
    return alerts_created


async def run_due_monitoring_checks() -> None:
    """
    Job scheduler : vérifie et exécute tous les checks de monitoring dus.
    Appelé toutes les heures par APScheduler.
    """
    now = datetime.now(timezone.utc)

    # Récupérer les IDs des configs dues dans une première session
    async with async_session() as db:
        result = await db.execute(
            select(MonitoringConfig.id).where(
                MonitoringConfig.is_active == True,  # noqa: E712
                MonitoringConfig.next_check_at <= now,
            )
        )
        config_ids = list(result.scalars().all())

    if not config_ids:
        return

    logger.info(f"Scheduler monitoring : {len(config_ids)} check(s) à lancer")

    # Exécuter chaque check dans sa propre session pour isolation
    for config_id in config_ids:
        async with async_session() as db:
            try:
                count = await run_monitoring_check(config_id, db)
                logger.info(f"Monitoring {config_id}: {count} alertes créées")
            except Exception as exc:
                logger.error(f"Erreur monitoring check {config_id}: {exc}")


def _update_timestamps(config: MonitoringConfig) -> None:
    """Met à jour last_checked_at et calcule next_check_at."""
    now = datetime.now(timezone.utc)
    config.last_checked_at = now
    config.next_check_at = now + timedelta(days=config.frequency_days)
