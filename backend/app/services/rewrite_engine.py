"""
Moteur de réécriture des allégations non conformes via Claude.
Pour chaque claim non conforme, propose une version corrigée et conforme à EmpCo.
"""
from __future__ import annotations

import anthropic

from app.config import settings


async def suggest_rewrite(
    claim_text: str,
    sector: str,
    non_conforming_reasons: list[str],
) -> str:
    """
    Appelle Claude pour proposer une réécriture conforme de l'allégation.

    Args:
        claim_text: L'allégation originale
        sector: Le secteur de l'entreprise (cosmetiques, alimentaire, etc.)
        non_conforming_reasons: Liste des raisons de non-conformité

    Returns:
        Une suggestion de réécriture conforme
    """
    if not settings.ANTHROPIC_API_KEY:
        return "Clé API Claude non configurée."

    reasons_text = "\n".join(f"- {r}" for r in non_conforming_reasons)

    prompt = f"""Tu es un expert juridique en droit de la consommation et en conformité à la directive européenne EmpCo (EU 2024/825) sur les allégations environnementales.

Une entreprise du secteur "{sector}" utilise l'allégation suivante :
« {claim_text} »

Cette allégation est NON CONFORME pour les raisons suivantes :
{reasons_text}

Propose UNE SEULE réécriture de cette allégation qui soit :
1. Conforme à EmpCo : spécifique, vérifiable, non générique
2. Honnête : ne pas inventer de chiffres ou certifications inexistants
3. Actionnable : utilisable directement par une agence de communication
4. Concise : une phrase maximum

Réponds UNIQUEMENT avec la nouvelle formulation, sans explication, sans guillemets, sans préambule."""

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()
