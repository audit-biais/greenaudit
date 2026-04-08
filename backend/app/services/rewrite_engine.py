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
) -> list[str]:
    """
    Appelle Claude pour proposer 3 réécritures conformes de l'allégation.

    Args:
        claim_text: L'allégation originale
        sector: Le secteur de l'entreprise (cosmetiques, alimentaire, etc.)
        non_conforming_reasons: Liste des raisons de non-conformité

    Returns:
        Liste de 3 suggestions de réécriture conformes
    """
    if not settings.ANTHROPIC_API_KEY:
        return ["Clé API Claude non configurée."]

    reasons_text = "\n".join(f"- {r}" for r in non_conforming_reasons)

    prompt = f"""Tu es un expert juridique en droit de la consommation et en conformité à la directive européenne EmpCo (EU 2024/825) sur les allégations environnementales.

Une entreprise du secteur "{sector}" utilise l'allégation suivante :
« {claim_text} »

Cette allégation est NON CONFORME pour les raisons suivantes :
{reasons_text}

Propose EXACTEMENT 3 réécritures différentes de cette allégation, chacune :
1. Conforme à EmpCo : spécifique, vérifiable, non générique
2. Honnête : ne pas inventer de chiffres ou certifications inexistants
3. Actionnable : utilisable directement par une agence de communication
4. Concise : une phrase maximum
5. D'un angle différent des deux autres (ex : une axée sur les chiffres, une sur la certification, une sur l'action concrète)

Réponds UNIQUEMENT avec les 3 formulations numérotées, format strict :
1. [première suggestion]
2. [deuxième suggestion]
3. [troisième suggestion]

Sans explication, sans guillemets, sans préambule."""

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Parser les 3 suggestions numérotées
    suggestions = []
    for line in raw.split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and ". " in line:
            suggestions.append(line.split(". ", 1)[1].strip())

    # Fallback si le parsing échoue
    if not suggestions:
        suggestions = [raw]

    return suggestions[:3]
