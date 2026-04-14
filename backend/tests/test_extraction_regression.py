"""
Tests de régression pour le prompt d'extraction Claude.

Lancer manuellement (appelle l'API Anthropic) :
    pytest -m integration -v

Ne pas lancer en CI par défaut — lent + coûte des tokens.

Workflow :
1. Scraper un site avec `python -m tests.capture_fixture <url> <nom>`
2. Valider manuellement les true_claims et must_not_extract dans le JSON
3. Lancer `pytest -m integration` pour vérifier
4. Après chaque évolution du prompt, relancer pour détecter les régressions
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PRECISION_THRESHOLD = 0.80  # 80% des true_claims détectées (recall)
FALSE_POSITIVE_TOLERANCE = 0  # zéro faux positif toléré sur must_not_extract


def load_fixture(name: str) -> dict[str, Any]:
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        pytest.skip(f"Fixture {name}.json introuvable — à créer avec capture_fixture.py")
    return json.loads(path.read_text(encoding="utf-8"))


def _match(extracted: str, reference: str) -> bool:
    """Correspondance souple : substring bidirectionnel, insensible à la casse."""
    a, b = extracted.lower().strip(), reference.lower().strip()
    return a in b or b in a


def count_true_positives(extracted: list[str], true_claims: list[str]) -> int:
    """Nombre de true_claims effectivement retrouvées dans extracted."""
    return sum(
        1 for true in true_claims
        if any(_match(ex, true) for ex in extracted)
    )


def find_false_positives(extracted: list[str], must_not: list[str]) -> list[str]:
    """Retourne les éléments de must_not_extract détectés à tort."""
    return [
        forbidden for forbidden in must_not
        if any(_match(ex, forbidden) for ex in extracted)
    ]


# ---------------------------------------------------------------------------
# Fixtures de sites
# ---------------------------------------------------------------------------

SITES = ["jd_sports", "naturalia", "labelle_vie"]


@pytest.mark.integration
@pytest.mark.parametrize("site_name", SITES)
async def test_no_false_positives(site_name: str) -> None:
    """Aucun élément de must_not_extract ne doit être extrait."""
    from app.services.monitoring_service import extract_claims_with_claude

    fixture = load_fixture(site_name)
    must_not = fixture.get("must_not_extract", [])
    if not must_not:
        pytest.skip(f"{site_name} : must_not_extract vide, rien à vérifier")

    claims = await extract_claims_with_claude(
        fixture["scraped_text"],
        existing_claims=[],
        audited_company_name=fixture.get("company_name", fixture.get("site", "")),
        audited_website_url=fixture.get("site", ""),
    )

    false_positives = find_false_positives(claims, must_not)
    assert not false_positives, (
        f"[{site_name}] {len(false_positives)} faux positif(s) détecté(s) :\n"
        + "\n".join(f"  - {fp}" for fp in false_positives)
    )


@pytest.mark.integration
@pytest.mark.parametrize("site_name", SITES)
async def test_recall_above_threshold(site_name: str) -> None:
    """Au moins PRECISION_THRESHOLD des true_claims doivent être retrouvées."""
    from app.services.monitoring_service import extract_claims_with_claude

    fixture = load_fixture(site_name)
    true_claims = fixture.get("true_claims", [])
    if not true_claims:
        pytest.skip(f"{site_name} : true_claims vide, rien à vérifier")

    claims = await extract_claims_with_claude(
        fixture["scraped_text"],
        existing_claims=[],
        audited_company_name=fixture.get("company_name", fixture.get("site", "")),
        audited_website_url=fixture.get("site", ""),
    )

    tp = count_true_positives(claims, true_claims)
    recall = tp / len(true_claims)

    missed = [t for t in true_claims if not any(_match(ex, t) for ex in claims)]
    assert recall >= PRECISION_THRESHOLD, (
        f"[{site_name}] Recall {recall:.0%} sous le seuil {PRECISION_THRESHOLD:.0%}\n"
        f"Manquées ({len(missed)}) :\n"
        + "\n".join(f"  - {m}" for m in missed)
        + f"\nExtraites ({len(claims)}) :\n"
        + "\n".join(f"  - {c}" for c in claims)
    )
