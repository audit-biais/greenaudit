"""
Script de capture de fixture pour les tests de régression.

Usage :
    cd backend
    python -m tests.capture_fixture https://www.naturalia.fr naturalia

Le script :
1. Scrape le site via scrape_website() (Firecrawl ou Jina selon la config)
2. Lance extract_claims_with_claude() pour obtenir une première liste de claims
3. Crée le fichier tests/fixtures/<nom>.json avec :
   - scraped_text figé
   - true_claims pré-remplis (à valider/corriger manuellement)
   - must_not_extract vide (à remplir manuellement)

Après exécution, ouvrir le JSON et :
- Supprimer les faux positifs de true_claims
- Ajouter les faux positifs connus dans must_not_extract
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# Charger les variables d'env depuis .env si présent
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


async def main(url: str, name: str) -> None:
    from app.services.monitoring_service import extract_claims_with_claude, scrape_website

    print(f"Scraping {url}...")
    text = await scrape_website(url)
    print(f"  {len(text)} caractères récupérés")

    if not text.strip():
        print("ERREUR : aucun texte récupéré. Vérifier l'URL ou la config Firecrawl/Jina.")
        sys.exit(1)

    print("Extraction des allégations via Claude...")
    claims = await extract_claims_with_claude(
        text,
        existing_claims=[],
        audited_company_name=name.replace("_", " ").title(),
        audited_website_url=url,
    )
    print(f"  {len(claims)} allégation(s) extraite(s)")

    company_name = name.replace("_", " ").title()
    fixture = {
        "_comment": (
            "true_claims = allégations validées manuellement. "
            "must_not_extract = faux positifs connus à ne jamais extraire."
        ),
        "site": urlparse(url).netloc,
        "company_name": company_name,  # Utilisé par le prompt pour l'auto-attribution
        "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "scraped_text": text,
        "true_claims": claims,  # À valider/corriger manuellement
        "must_not_extract": [],  # À remplir manuellement
    }

    out = Path(__file__).parent / "fixtures" / f"{name}.json"
    out.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nFixture créée : {out}")
    print("\nProchaines étapes :")
    print("  1. Ouvrir le JSON et valider true_claims (supprimer les faux positifs)")
    print("  2. Ajouter les faux positifs connus dans must_not_extract")
    print("  3. Lancer : pytest -m integration -v")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m tests.capture_fixture <url> <nom>")
        print("Ex:    python -m tests.capture_fixture https://www.naturalia.fr naturalia")
        sys.exit(1)

    asyncio.run(main(sys.argv[1], sys.argv[2]))
