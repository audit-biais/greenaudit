from __future__ import annotations

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlparse
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


_RSE_KEYWORDS = re.compile(
    r"rse|durabilit|engagement|sustainab|environnement|climat|impact|"
    r"ecolog|responsab|green|vert|carbone|carbon|biodiversit|recyclage|"
    r"empreinte|transition|net.?zero|neutralit",
    re.IGNORECASE,
)


async def _fetch_sitemap_urls(base_url: str) -> List[str]:
    """
    Récupère les URLs RSE depuis le sitemap XML du site.
    Essaie sitemap.xml puis sitemap_index.xml. Filtre par mots-clés RSE.
    Retourne au max 10 URLs pour ne pas surcharger Firecrawl.
    """
    parsed = urlparse(base_url)
    root_url = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [f"{root_url}/sitemap.xml", f"{root_url}/sitemap_index.xml"]
    rse_urls: List[str] = []

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for sitemap_url in candidates:
            try:
                resp = await client.get(sitemap_url)
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.text)
                # Gère les namespaces XML (xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                locs = [el.text for el in root.findall(".//sm:loc", ns) if el.text]
                if not locs:
                    # Fallback sans namespace
                    locs = [el.text for el in root.findall(".//loc") if el.text]

                rse_urls = [u for u in locs if _RSE_KEYWORDS.search(u)]
                logger.info(
                    f"Sitemap {sitemap_url} : {len(locs)} URLs, {len(rse_urls)} RSE"
                )
                if rse_urls:
                    break
            except Exception as exc:
                logger.debug(f"Sitemap inaccessible ({sitemap_url}): {exc}")

    return rse_urls[:10]


async def _scrape_firecrawl(url: str) -> str:
    """
    Crawl récursif via Firecrawl avec priorité aux pages RSE du sitemap.
    Chaque page est annotée avec son URL pour donner du contexte à Claude.
    """
    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

        def _scrape_pages(target_url: str, limit: int, depth: int):
            return app.crawl_url(
                target_url,
                {"limit": limit, "maxDepth": depth, "scrapeOptions": {"formats": ["markdown"]}},
            )

        def _extract_pages(result) -> list:
            if isinstance(result, dict):
                return result.get("data", [])
            elif hasattr(result, "data"):
                return result.data or []
            return []

        def get_markdown(p) -> str:
            if isinstance(p, dict):
                return p.get("markdown", "") or ""
            return getattr(p, "markdown", "") or ""

        def get_url(p) -> str:
            if isinstance(p, dict):
                meta = p.get("metadata", {}) or {}
                return meta.get("url", "") or p.get("url", "") or ""
            meta = getattr(p, "metadata", None)
            if isinstance(meta, dict):
                return meta.get("url", "")
            return getattr(p, "url", "") or ""

        # Conseil 1 — Crawl principal + fetch sitemap en parallèle (pas de latence ajoutée)
        sitemap_task = asyncio.create_task(_fetch_sitemap_urls(url))
        result = await asyncio.to_thread(_scrape_pages, url, 15, 2)
        sitemap_urls = await sitemap_task
        pages = _extract_pages(result)

        # Conseil 1 — Scraper en plus les pages RSE du sitemap non couvertes par le crawl
        crawled_urls = {get_url(p) for p in pages}
        extra_urls = [u for u in sitemap_urls if u not in crawled_urls]

        for extra_url in extra_urls[:5]:
            try:
                extra_result = await asyncio.to_thread(_scrape_pages, extra_url, 1, 0)
                extra_pages = _extract_pages(extra_result)
                pages.extend(extra_pages)
                logger.info(f"Sitemap extra : page ajoutée — {extra_url}")
            except Exception as exc:
                logger.debug(f"Sitemap extra scrape failed ({extra_url}): {exc}")

        if not pages:
            logger.warning(f"Firecrawl : aucun contenu pour {url}, fallback Jina")
            return await _scrape_jina(url)

        # Conseil 2 — Annoter chaque page avec son URL pour le contexte Claude
        sections = []
        for p in pages:
            md = get_markdown(p)
            if not md.strip():
                continue
            page_url = get_url(p) or url
            sections.append(f"=== PAGE: {page_url} ===\n{md}")

        collected = "\n\n".join(sections)

        if not collected.strip():
            logger.warning(f"Firecrawl : markdown vide pour {url}, fallback Jina")
            return await _scrape_jina(url)

        logger.info(
            f"Firecrawl : {len(pages)} page(s) dont {len(extra_urls[:5])} depuis sitemap — {url}"
        )
        return collected[:20000]

    except Exception as exc:
        logger.error(f"Erreur Firecrawl pour {url}: {exc} — fallback Jina")
        return await _scrape_jina(url)


async def _scrape_jina(url: str) -> str:
    """Fallback Jina Reader — 6 chemins codés en dur, avec marqueurs PAGE."""
    _RSE_PATHS = [
        "", "/rse", "/developpement-durable",
        "/engagement", "/sustainability", "/environnement",
    ]
    base_url = url.rstrip("/")
    sections: list = []
    total = 0

    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        headers={"Accept": "text/plain", "X-Return-Format": "text"},
    ) as client:
        for path in _RSE_PATHS:
            page_url = f"{base_url}{path}" if path else base_url
            target = f"https://r.jina.ai/{page_url}"
            try:
                response = await client.get(target)
                if response.status_code != 200:
                    continue
                text = response.text.strip()
                if text:
                    sections.append(f"=== PAGE: {page_url} ===\n{text}")
                    total += len(text)
                if total >= 8000:
                    break
            except Exception as exc:
                logger.debug(f"Jina impossible pour {page_url}: {exc}")
                continue

    return "\n\n".join(sections)[:8000]


# ---------------------------------------------------------------------------
# Filtre post-extraction déterministe — faux positifs structurels
# ---------------------------------------------------------------------------

# Bloc 1 — Nominalisations d'action industrielle sans bénéfice environnemental
_INDUSTRIAL_ACTION_PREFIXES = re.compile(
    r"^(création|fabrication|production|construction|installation|"
    r"mise en place|développement|déploiement|réalisation|"
    r"ouverture|lancement|livraison)\b",
    re.IGNORECASE,
)
_TECHNICAL_OBJECT_TERMS = re.compile(
    r"\b(réservoir[s]?|usine[s]?|centrale[s]?|infrastructure[s]?|"
    r"équipement[s]?|machine[s]?|borne[s]?|panneau[x]?|"
    r"canalisation[s]?|tuyau[x]?|citerne[s]?|silo[s]?|"
    r"entrepôt[s]?|bâtiment[s]?|site[s]?\s+industriel[s]?)\b",
    re.IGNORECASE,
)
_ENVIRONMENTAL_BENEFIT_TERMS = re.compile(
    r"\b(réduire|réduction|limiter|limitation|préserver|protéger|"
    r"durable[s]?|écologique[s]?|responsable[s]?|vert[s]?|verte[s]?|"
    r"propre[s]?|recyclé[s]?|recyclée[s]?|bas.carbone|"
    r"moins.d.émission|empreinte.réduite|impact.réduit|"
    r"économie[s]?.d.énergie|économe[s]?.en)\b",
    re.IGNORECASE,
)

# Bloc 2 — Mécanismes physiques impersonnels
_IMPERSONAL_SUBJECT = re.compile(
    r"^(le|la|l['']|les|ce|cet|cette|ces|il|on)\s+"
    r"(coton|polyester|plastique|recyclage|compostage|pollution|"
    r"bioplastique|matériau|matière|produit|processus|procédé|"
    r"carton|verre|aluminium|métal|textile|tissu|fibre|"
    r"production|fabrication|eau|énergie|laine|bois)\b",
    re.IGNORECASE,
)
_MECHANISM_MARKERS = re.compile(
    r"\b(consomme moins (de|d[''])|émet moins|produit moins|"
    r"nul besoin de|pas besoin de|en le recyclant|en recyclant|"
    r"que le .{1,20} normal|que le .{1,20} classique|"
    r"par rapport au .{1,20} vierge|évite la production|"
    r"limite la production|réduit la pollution)\b",
    re.IGNORECASE,
)
_ABSOLUTE_MECHANISM_MARKERS = re.compile(
    r"\bnul besoin de\b|\bpas besoin de\b|\ben le recyclant\b|\ben les recyclant\b",
    re.IGNORECASE,
)

# Bloc 5 — Qualité produit sans dimension environnementale
_PRODUCT_QUALITY_TERMS = re.compile(
    r"\b(plus solide[s]?|plus résistant[s]?|plus confortable[s]?|"
    r"plus doux|plus souple[s]?|meilleure qualité|haute qualité|"
    r"plus agréable[s]?|plus robuste[s]?|plus léger[s]?|plus légère[s]?)\b",
    re.IGNORECASE,
)
_ENV_TERMS_SIMPLE = re.compile(
    r"\b(environnement|écolog|recyclé|durable|carbone|émission|"
    r"déchet|pollution|climate|biodiversité|écoresponsable)\b",
    re.IGNORECASE,
)

# Bloc 3 — Collectifs génériques (les marques, elles deviennent...)
_GENERIC_COLLECTIVE_SUBJECT = re.compile(
    r"^(elles|ils)\s+(deviennent|sont|font|vont|s['']engagent)\b"
    r"|^(les marques|les entreprises|les acteurs|le secteur|l['']industrie)\b",
    re.IGNORECASE,
)

# Bloc 4 — Navigation UI sans allégation environnementale
_UI_NAVIGATION = re.compile(
    r"\b(n['']hésite pas à|orienter (tes|vos) recherches|clique ici|"
    r"tapant dans la barre|recherche sur (notre|le) site)\b",
    re.IGNORECASE,
)


def _build_attribution_pattern(company_name: str) -> re.Pattern:
    """Construit le pattern d'attribution à l'entreprise de façon dynamique."""
    base = r"\b(nous|notre|nos|chez\s+\w+)\b"
    if company_name:
        # Prend le premier mot du nom de l'entreprise (ex: "JD Sports" → "JD")
        first_word = re.escape(company_name.split()[0])
        return re.compile(base + rf"|\b{first_word}\b", re.IGNORECASE)
    return re.compile(base, re.IGNORECASE)


def filter_false_positives(claims: List[str], company_name: str = "") -> List[str]:
    """
    Filtre post-extraction déterministe — s'exécute après extract_claims_with_claude().

    Bloc 1 — Nominalisations industrielles sans bénéfice environnemental.
    Bloc 2 — Mécanismes physiques impersonnels (sujet = matériau/processus).
    Bloc 3 — Collectifs génériques (les marques, elles deviennent...).
    Bloc 4 — Navigation UI sans allégation environnementale.
    """
    attribution = _build_attribution_pattern(company_name)
    filtered = []

    for claim in claims:
        text = claim.strip()
        excluded = False

        # Bloc 1 : nominalisation industrielle
        if (
            _INDUSTRIAL_ACTION_PREFIXES.search(text)
            and _TECHNICAL_OBJECT_TERMS.search(text)
            and not _ENVIRONMENTAL_BENEFIT_TERMS.search(text)
        ):
            excluded = True

        # Bloc 2a : sujet matériau/processus + pas d'attribution
        # (le marqueur de mécanisme n'est plus requis : tout énoncé sur un matériau
        # sans attribution à l'entreprise est une description générale, pas une allégation)
        elif (
            _IMPERSONAL_SUBJECT.search(text)
            and not attribution.search(text)
        ):
            excluded = True

        # Bloc 2b : marqueurs absolus de mécanisme sans attribution
        elif (
            _ABSOLUTE_MECHANISM_MARKERS.search(text)
            and not attribution.search(text)
        ):
            excluded = True

        # Bloc 2c : pronom neutre (il/on) en sujet + marqueur mécanisme + pas attribution
        elif (
            re.match(r"^(il|on)\s+\w", text, re.IGNORECASE)
            and _MECHANISM_MARKERS.search(text)
            and not attribution.search(text)
        ):
            excluded = True

        # Bloc 3 : collectif générique sans attribution
        elif (
            _GENERIC_COLLECTIVE_SUBJECT.search(text)
            and not attribution.search(text)
        ):
            excluded = True

        # Bloc 4 : navigation UI
        elif _UI_NAVIGATION.search(text):
            excluded = True

        # Bloc 5 : qualité produit sans dimension environnementale
        elif (
            _PRODUCT_QUALITY_TERMS.search(text)
            and not _ENV_TERMS_SIMPLE.search(text)
        ):
            excluded = True

        if excluded:
            logger.info(f"filter_false_positives: exclu — '{text}'")
        else:
            filtered.append(claim)

    return filtered


_PAGE_MARKER_RE = re.compile(r"=== PAGE: (https?://\S+) ===")


_FR_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "en",
    "sur", "par", "pour", "avec", "sans", "dans", "au", "aux", "ce", "cet",
    "cette", "ces", "il", "elle", "ils", "elles", "nous", "vous", "se", "si",
    "ne", "pas", "plus", "que", "qui", "quoi", "dont", "où", "est", "sont",
    "a", "ont", "être", "avoir", "mais", "donc", "or", "ni", "car", "à",
}


def _find_source_url(claim_text: str, scraped_text: str) -> Optional[str]:
    """
    Cherche dans quelle section (=== PAGE: url ===) se trouve l'allégation.
    Passe 1 — exact : fenêtres glissantes de 4+ mots sur le texte normalisé.
    Passe 2 — mots-clés : section qui contient le plus de mots significatifs
               de l'allégation (fallback pour badges, textes fragmentés, paraphrases).
    """
    parts = _PAGE_MARKER_RE.split(scraped_text)
    if len(parts) < 3:
        return None

    def _norm(s: str) -> str:
        s = s.lower().strip("«»\"'\u2018\u2019\u201c\u201d")
        return re.sub(r"[\s\u00a0]+", " ", s).strip()

    claim_n = _norm(claim_text)
    if not claim_n:
        return None

    words = claim_n.split()

    # ── Passe 1 : correspondance exacte (sous-chaînes) ──────────────────────
    needles: list = [claim_n]
    for size in (8, 6, 5):
        if len(words) > size:
            needles.append(" ".join(words[:size]))
    for j in range(len(words) - 3):
        needles.append(" ".join(words[j : j + 4]))

    for i in range(1, len(parts) - 1, 2):
        page_url = parts[i]
        content = _norm(parts[i + 1])
        for needle in needles:
            if len(needle) >= 10 and needle in content:
                return page_url

    # ── Passe 2 : score par mots-clés (fallback badges / paraphrases) ───────
    keywords = [w for w in words if w not in _FR_STOPWORDS and len(w) >= 4]
    if len(keywords) < 2:
        return None

    best_url: Optional[str] = None
    best_score = 0
    threshold = max(2, len(keywords) // 2)  # au moins la moitié des mots-clés

    for i in range(1, len(parts) - 1, 2):
        page_url = parts[i]
        content = _norm(parts[i + 1])
        score = sum(1 for kw in keywords if kw in content)
        if score > best_score:
            best_score = score
            best_url = page_url

    return best_url if best_score >= threshold else None


async def extract_claims_with_claude(
    text: str,
    existing_claims: List[str],
    audited_company_name: str = "",
    audited_website_url: str = "",
) -> list:
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

RÈGLE VERBATIM — OBLIGATOIRE :
Copie chaque allégation EXACTEMENT telle qu'elle apparaît dans le texte de la page — mêmes mots, même ordre.
Si le passage est trop long (plus de 120 caractères), garde le début exact et coupe avec "…".
N'invente pas, ne reformule pas, ne résume pas.

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
        raw_claims = [str(c) for c in data.get("claims", [])]
        filtered = filter_false_positives(raw_claims, company_name=audited_company_name)
        return [
            {"claim_text": c, "source_url": _find_source_url(c, text)}
            for c in filtered
        ]

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
    for item in new_claims:
        alert = MonitoringAlert(
            monitoring_config_id=config.id,
            claim_text=item["claim_text"],
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
