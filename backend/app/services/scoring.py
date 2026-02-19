"""
Calcul du scoring global d'un audit.

Score = (claims conformes * 100 + claims risque * 50) / total_claims
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple


def calculate_global_score(
    conforming: int, at_risk: int, non_conforming: int
) -> Tuple[Decimal, str]:
    """
    Calcule le score global et le niveau de risque.

    Args:
        conforming: nombre de claims conformes
        at_risk: nombre de claims à risque
        non_conforming: nombre de claims non conformes

    Returns:
        (score 0-100, risk_level)

    Risk levels:
        >= 80 : "faible"
        >= 60 : "modere"
        >= 40 : "eleve"
        < 40  : "critique"
    """
    total = conforming + at_risk + non_conforming
    if total == 0:
        return Decimal("0"), "critique"

    raw_score = (conforming * 100 + at_risk * 50) / total
    score = Decimal(str(raw_score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if score >= 80:
        risk_level = "faible"
    elif score >= 60:
        risk_level = "modere"
    elif score >= 40:
        risk_level = "eleve"
    else:
        risk_level = "critique"

    return score, risk_level


def compute_verdict_counts(
    verdicts: list,
) -> Dict[str, int]:
    """
    Compte les verdicts des claims.

    Args:
        verdicts: liste de overall_verdict (str) de chaque claim

    Returns:
        {"conforme": n, "risque": n, "non_conforme": n}
    """
    counts = {"conforme": 0, "risque": 0, "non_conforme": 0}
    for v in verdicts:
        if v in counts:
            counts[v] += 1
    return counts
