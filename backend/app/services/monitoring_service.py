from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session
from app.models.audit import Audit
from app.models.monitoring_alert import MonitoringAlert
from app.models.monitoring_config import MonitoringConfig

logger = logging.getLogger(__name__)


async def scrape_website(url: str) -> str:
    """
    Scrape le site via Firecrawl (crawl récursif automatique).
    Firecrawl découvre les pages RSE peu importe leur URL, exécute le JS
    et retourne du Markdown propre — fonctionne sur React/Next.js/Shopify.
    Retourne le texte concaténé, limité à 15 000 caractères.
    Fallback sur Jina Reader si FIRECRAWL_API_KEY non configurée.
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    if settings.FIRECRAWL_API_KEY:
        return await _scrape_firecrawl(url)
    return await _scrape_jina(url)


async def _scrape_firecrawl(url: str) -> str:
    """Crawl récursif via Firecrawl — trouve automatiquement les pages RSE."""
    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

        result = await asyncio.to_thread(
            app.crawl_url,
            url,
            {
                "limit": 15,
                "maxDepth": 2,
                "scrapeOptions": {"formats": ["markdown"]},
            },
        )

        # Firecrawl peut retourner un dict OU un objet selon la version du SDK
        if isinstance(result, dict):
            pages = result.get("data", [])
        elif hasattr(result, "data"):
            pages = result.data or []
        else:
            pages = []

        def get_markdown(p):
            if isinstance(p, dict):
                return p.get("markdown", "")
            return getattr(p, "markdown", "") or ""

        collected = "\n\n".join(get_markdown(p) for p in pages if get_markdown(p))

        if not collected.strip():
            logger.warning(f"Firecrawl : aucun contenu pour {url}, fallback Jina")
            return await _scrape_jina(url)

        logger.info(f"Firecrawl : {len(pages)} page(s) scrapée(s) pour {url}")
        return collected[:15000]

    except Exception as exc:
        logger.error(f"Erreur Firecrawl pour {url}: {exc} — fallback Jina")
        return await _scrape_jina(url)


async def _scrape_jina(url: str) -> str:
    """Fallback Jina Reader — 6 chemins codés en dur."""
    _RSE_PATHS = [
        "", "/rse", "/developpement-durable",
        "/engagement", "/sustainability", "/environnement",
    ]
    base_url = url.rstrip("/")
    collected_text = ""

    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        headers={"Accept": "text/plain", "X-Return-Format": "text"},
    ) as client:
        for path in _RSE_PATHS:
            target = f"https://r.jina.ai/{base_url}{path}"
            try:
                response = await client.get(target)
                if response.status_code != 200:
                    continue
                collected_text += response.text + "\n"
                if len(collected_text) >= 8000:
                    break
            except Exception as exc:
                logger.debug(f"Jina impossible pour {base_url}{path}: {exc}")
                continue

    return collected_text[:8000]


async def extract_claims_with_claude(
    text: str,
    existing_claims: List[str],
    audited_company_name: str = "",
    audited_website_url: str = "",
) -> List[str]:
    """
    Utilise Claude Haiku pour extraire les nouvelles allégations environnementales.
    Retourne uniquement les claims absentes de existing_claims.
    audited_company_name et audited_website_url permettent à Haiku de discriminer
    les allégations auto-attribuées des mentions de marques tierces.
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

        company_name = audited_company_name or "l'entreprise auditée"
        company_url = audited_website_url or "inconnue"
        company_header = f"""ENTREPRISE AUDITÉE : {company_name}
SITE WEB AUDITÉ : {company_url}

RÈGLE D'OR ABSOLUE — à appliquer AVANT toutes les autres règles :
Tu n'extrais que les allégations environnementales faites par {company_name} sur ses propres produits, services, ou engagements.

Tu EXCLUS SYSTÉMATIQUEMENT :
- Toute allégation dont le sujet grammatical est une autre marque ou entreprise (Nike, adidas, un fournisseur, un partenaire, un concurrent cité en exemple)
- Toute description d'un produit dont la marque n'est pas {company_name}
- Toute explication générique du fonctionnement d'un mécanisme environnemental non attribuée à {company_name} : "le recyclage permet de", "en recyclant on évite", "la pollution est réduite quand on", "le compostage transforme". Ces phrases décrivent comment le monde fonctionne, pas ce que {company_name} fait ou promet.
- Toute description factuelle d'activité industrielle ou commerciale sans affirmation de bénéfice environnemental : "création de X", "fabrication de X", "production de X", "construction de X", "installation de X" suivis d'un objet technique (réservoirs, usines, machines, équipements) sans qu'une incidence positive sur l'environnement soit explicitement affirmée. Une description de ce que l'entreprise FAIT n'est pas une allégation de ce qu'elle APPORTE à l'environnement.

En cas de doute sur l'attribution, EXCLUS plutôt qu'inclus.

---

"""

        prompt = f"""{company_header}Tu es un expert en conformité à la directive EmpCo (EU 2024/825) sur les allégations environnementales.

Analyse le texte suivant extrait d'un site web et identifie les allégations environnementales — y compris les vagues et génériques, car ce sont elles qui violent EmpCo.

══════════════════════════════════════════════════
TEST PRÉALABLE OBLIGATOIRE — à appliquer AVANT toute extraction
══════════════════════════════════════════════════
Pour chaque phrase candidate, applique ce raisonnement en 2 étapes :

ÉTAPE 1 — La phrase est-elle une NOMINALISATION D'ACTION ?
Une nominalisation d'action commence par : "création de", "construction de", "installation de", "fabrication de", "production de", "développement de", "mise en place de", "réalisation de" — suivis d'un objet.
→ Si oui : c'est une description de ce que l'entreprise FAIT, pas de ce qu'elle APPORTE à l'environnement. EXCLURE systématiquement.

EXEMPLES ÉTAPE 1 (à exclure sans exception) :
• "création de réservoirs de biocarburants" → EXCLU. "Création de" = nominalisation. La phrase ne dit pas que les biocarburants améliorent le bilan carbone de l'entreprise. C'est une activité industrielle décrite, pas une allégation.
• "installation de panneaux photovoltaïques" → EXCLU. Même logique.
• "construction d'une chaufferie biomasse" → EXCLU. Même logique.

ÉTAPE 2 — Si ce n'est pas une nominalisation, la phrase AFFIRME-T-ELLE un impact environnemental positif/neutre/réduit de {company_name} ?
→ Si non : EXCLURE.

EXEMPLES ÉTAPE 2 (à exclure) :
• "le recyclage réduit la pollution" → EXCLU. Le sujet est "le recyclage" (mécanisme général), pas {company_name}.
• "les biocarburants émettent moins de CO2 que le pétrole" → EXCLU. Fait général, pas une allégation de l'entreprise.

EXEMPLES À INCLURE (franchissent les 2 étapes) :
• "nos biocarburants réduisent nos émissions de 30%" → INCLUS. Sujet = "nos", affirmation d'impact chiffré.
• "grâce à nos réservoirs de biocarburants, nous réduisons notre empreinte carbone" → INCLUS. Affirmation d'impact attribuée à l'entreprise.
══════════════════════════════════════════════════

INCLURE :
RÈGLE D'AUTO-ATTRIBUTION : L'allégation doit être une promesse, un engagement ou une description de performance de l'entreprise auditée elle-même — pas d'un tiers, pas du secteur en général, pas d'un mécanisme physique ou économique.

1. Termes génériques environnementaux même en phrase courte : "bon pour la planète", "éco-responsable", "durable", "vert", "green", "respectueux de l'environnement", "naturel", "écologique", "zéro déchet", "neutre en carbone", "climate friendly", "sustainable"
2. Allégations sur : déchets, émissions, emballages, recyclage, énergie, eau, biodiversité, forêts, carbone
3. Circuit court ou local UNIQUEMENT si explicitement présenté comme bénéfice environnemental (ex: "circuit court pour réduire notre impact carbone") — PAS si c'est un argument de fraîcheur ou de qualité
4. Anti-gaspillage UNIQUEMENT si présenté comme engagement environnemental explicite — PAS si c'est une promotion commerciale (ex: "prix réduits sur packaging abîmé")
5. Certifications environnementales avec contexte d'allégation : bio, GOTS, Ecolabel, FSC, Rainforest Alliance

EXCLURE ABSOLUMENT :
- Social pur : équité, inclusion, emploi, conditions de travail, dons, reversement à une association, mécénat
- Santé et bien-être : "sain", "équilibré", "bien-être", "bonne santé", "nutritif", "sans additifs", "sans sucre"
- Éthique sans dimension environnementale : "éthique", "responsable" seul, "engagé" seul, sans mention explicite de l'environnement, du climat, des émissions ou de l'écologie
- Commercial pur : goût, fraîcheur, prix, qualité gustative, service client, livraison, Nutriscore
- Noms de gamme ou rayons sans allégation : "rayon bio", "épicerie bio", "boulangerie naturelle"
- Provenance et origine sans lien environnemental explicite : "local", "fait sur place", "made in France", "produits français", "à moins de X km" quand l'argument est la fraîcheur ou la qualité
- Slogans de fraîcheur ou de qualité : "du champ à l'assiette", "cuisinés du jour", "frais & locaux"
- Mentions de tiers ou concurrents : allégations attribuées à d'autres marques ou entreprises que celle auditée ("Nike conçoit ses kits avec du polyester recyclé", "les marques font des efforts"). Seules les allégations auto-attribuées comptent (sujet = nous/notre marque/nos produits, ou absence de sujet tiers nommé)
- Contenu éditorial, pédagogique ou narratif : explications générales sur un mécanisme environnemental, opinions sur le secteur, storytelling sans engagement de l'entreprise ("le recyclage évite la pollution", "éviter que des bouteilles terminent dans les océans", "les efforts des marques sont de vraies avancées"). Une allégation doit être une promesse ou une description de performance de l'entreprise auditée, pas une explication du monde
- Noms de programmes, collections ou campagnes : marques, slogans déposés, noms de lignes de produits cités sans description du bénéfice environnemental concret ("Move to Zero", "Plan Planète", "Collection Green"). Si le nom est accompagné d'un engagement chiffré ou décrit dans la même phrase, l'engagement lui-même est une allégation, pas le nom
- Dons et actions sociales : "1% for the Planet", "reversé à", "nous soutenons", "partenaire de"

RÈGLE CRITIQUE — FORMAT MINIMUM :
Une allégation doit être une PHRASE ou EXPRESSION avec au minimum un verbe ou un adjectif qualificatif lié à l'environnement. Un mot seul, une abréviation seule ou un compteur ne sont PAS des allégations.
- "BIO" seul → pas une allégation (c'est une catégorie)
- "6 500 BIO" → pas une allégation (c'est un compteur)
- "HVE" seul → pas une allégation (c'est une abréviation)
- "ANTI-GASPI" seul → pas une allégation (c'est un label)
- "Boutique bio" → pas une allégation (c'est un nom de rayon)
- "nos produits sont certifiés bio" → allégation valide
- "éco-responsable" seul comme adjectif qualifiant une marque/produit → allégation valide
- "bon pour la planète" → allégation valide

EXEMPLES VALIDES : "bon pour la planète", "éco-responsable", "40% de matières recyclées", "neutre en carbone depuis 2022", "fabriqué de façon durable", "zéro déchet d'ici 2025", "vêtements éco-responsables"
EXEMPLES INVALIDES : "BIO", "HVE", "6 500 BIO", "ANTI-GASPI", "Boutique bio", "Primeur local pour plus de fraîcheur", "Nutriscore A", "sans sucre ajouté", "qualité artisanale", "frais, local, fait sur place", "made in France", "produits locaux cuisinés du jour", "du champ à l'assiette", "à moins de 50km de vos bureaux", "traiteur engagé", "alimentation saine et éthique", "respectant votre bien-être", "1% reversé à 1% for the Planet", "nous soutenons l'association X", "Nike conçoit ses kits avec du polyester recyclé", "les efforts des marques sont de vraies avancées", "Move to Zero", "le recyclage réduit la pollution liée au polyester", "éviter que des bouteilles terminent dans les océans", "création de réservoirs de biocarburants", "construction d'une nouvelle usine", "installation de panneaux solaires" (sans affirmation de bénéfice), "le recyclage évite la pollution", "en le recyclant nul besoin de le produire", "la production de polyester est réduite en le recyclant"

Allégations déjà connues (ne pas les répéter) :
{existing_str}

Texte du site :
{text}

Retourne UNIQUEMENT les nouvelles allégations environnementales au format JSON :
{{"claims": ["allégation 1", "allégation 2"]}}

Si aucune allégation environnementale, retourne : {{"claims": []}}
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

    new_claims = await extract_claims_with_claude(
        page_text,
        existing_claims,
        audited_company_name=audit.company_name or "",
        audited_website_url=audit.website_url or "",
    )

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
