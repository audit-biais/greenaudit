"""
Moteur d'analyse des 6 règles EmpCo (EU 2024/825).

Pour chaque claim, applique 6 critères et produit un ClaimResult par règle.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.utils.blacklist import (
    BLACKLIST_TERMS,
    CARBON_NEUTRAL_TERMS,
    PARTIAL_SCOPE_PATTERNS,
    QUALIFICATION_PATTERNS,
)


def _text_lower(claim: Claim) -> str:
    return claim.claim_text.lower().strip()


def _has_qualification(text: str) -> bool:
    """Vérifie si le texte contient une qualification mesurable."""
    for pattern in QUALIFICATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _find_blacklist_match(text: str) -> Optional[str]:
    """Retourne le premier terme blacklisté trouvé dans le texte, ou None."""
    for term in BLACKLIST_TERMS:
        if term.lower() in text:
            return term
    return None


def _find_carbon_neutral_match(text: str) -> Optional[str]:
    """Retourne le premier terme de neutralité carbone trouvé, ou None."""
    for term in CARBON_NEUTRAL_TERMS:
        if term.lower() in text:
            return term
    return None


def _has_partial_scope_mention(text: str) -> bool:
    """Vérifie si le texte mentionne un aspect partiel (emballage, transport, etc.)."""
    for pattern in PARTIAL_SCOPE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Règle 1 — Claims génériques (blacklist)
# ---------------------------------------------------------------------------

def rule_specificity(claim: Claim) -> ClaimResult:
    """Détecte les termes génériques interdits par EmpCo dans claim_text."""
    text = _text_lower(claim)
    matched_term = _find_blacklist_match(text)

    if matched_term is None:
        return ClaimResult(
            claim_id=claim.id,
            criterion="specificity",
            verdict="non_applicable",
            explanation="Aucun terme générique interdit détecté dans l'allégation.",
        )

    if _has_qualification(text):
        return ClaimResult(
            claim_id=claim.id,
            criterion="specificity",
            verdict="risque",
            explanation=(
                f"Le terme « {matched_term} » est présent mais accompagné d'une "
                f"qualification. Vérifier que la preuve est suffisante et mesurable."
            ),
            recommendation=(
                "Fournir une preuve quantifiée et vérifiable pour étayer "
                "la qualification du terme générique."
            ),
            regulation_reference="Directive EmpCo (EU 2024/825), Art. 2(o) — interdiction des allégations environnementales génériques sans preuve",
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="specificity",
        verdict="non_conforme",
        explanation=(
            f"Le terme « {matched_term} » est utilisé seul, sans qualification "
            f"spécifique ni preuve mesurable. Ceci est interdit par la directive EmpCo."
        ),
        recommendation=(
            f"Supprimer le terme « {matched_term} » ou le remplacer par une "
            f"allégation spécifique et mesurable (ex : « contient 30% de matières recyclées »)."
        ),
        regulation_reference="Directive EmpCo (EU 2024/825), Art. 2(o) — interdiction des allégations environnementales génériques",
    )


# ---------------------------------------------------------------------------
# Règle 2 — Neutralité carbone par compensation
# ---------------------------------------------------------------------------

def rule_compensation(claim: Claim) -> ClaimResult:
    """Détecte les claims de neutralité carbone (interdiction absolue EmpCo)."""
    text = _text_lower(claim)
    matched_term = _find_carbon_neutral_match(text)

    if matched_term is None:
        return ClaimResult(
            claim_id=claim.id,
            criterion="compensation",
            verdict="non_applicable",
            explanation="Aucune allégation de neutralité carbone détectée.",
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="compensation",
        verdict="non_conforme",
        explanation=(
            f"L'allégation contient « {matched_term} ». Les claims de neutralité "
            f"carbone basées sur la compensation sont interdites par la directive EmpCo, "
            f"sans exception."
        ),
        recommendation=(
            "Supprimer toute référence à la neutralité carbone. "
            "Communiquer plutôt sur les réductions d'émissions concrètes "
            "et mesurables de l'entreprise."
        ),
        regulation_reference="Directive EmpCo (EU 2024/825), Art. 2(o) et Annexe I, point 4 — interdiction des allégations de neutralité carbone par compensation",
    )


# ---------------------------------------------------------------------------
# Règle 3 — Labels auto-décernés
# ---------------------------------------------------------------------------

def rule_labels(claim: Claim) -> ClaimResult:
    """Vérifie la conformité des labels utilisés."""
    if not claim.has_label:
        return ClaimResult(
            claim_id=claim.id,
            criterion="labels",
            verdict="non_applicable",
            explanation="Aucun label déclaré pour cette allégation.",
        )

    if claim.label_is_certified:
        return ClaimResult(
            claim_id=claim.id,
            criterion="labels",
            verdict="conforme",
            explanation=(
                f"Le label « {claim.label_name or 'non précisé'} » est certifié "
                f"par un organisme tiers indépendant."
            ),
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="labels",
        verdict="non_conforme",
        explanation=(
            f"Le label « {claim.label_name or 'non précisé'} » est auto-décerné. "
            f"Les labels de durabilité auto-décernés sont interdits par la directive EmpCo."
        ),
        recommendation=(
            "Retirer ce label ou obtenir une certification par un organisme "
            "tiers indépendant accrédité."
        ),
        regulation_reference="Directive EmpCo (EU 2024/825), Art. 2(r) — labels de durabilité certifiés par des tiers",
    )


# ---------------------------------------------------------------------------
# Règle 4 — Proportionnalité (ensemble vs aspect)
# ---------------------------------------------------------------------------

def rule_proportionality(claim: Claim) -> ClaimResult:
    """Vérifie la proportionnalité entre le scope déclaré et le contenu réel."""
    if claim.scope != "entreprise":
        return ClaimResult(
            claim_id=claim.id,
            criterion="proportionality",
            verdict="non_applicable",
            explanation="Le scope est limité à un produit, la règle de proportionnalité ne s'applique pas.",
        )

    text = _text_lower(claim)

    if _has_partial_scope_mention(text):
        return ClaimResult(
            claim_id=claim.id,
            criterion="proportionality",
            verdict="risque",
            explanation=(
                "L'allégation est déclarée au niveau « entreprise » mais le texte "
                "mentionne un aspect partiel (emballage, transport, produit…). "
                "Cela peut induire le consommateur en erreur sur la portée réelle."
            ),
            recommendation=(
                "Reformuler l'allégation pour préciser qu'elle ne concerne qu'un "
                "aspect spécifique de l'activité, ou fournir des preuves couvrant "
                "l'ensemble de l'entreprise."
            ),
            regulation_reference="Directive EmpCo (EU 2024/825), Art. 2(o) — proportionnalité et clarté des allégations",
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="proportionality",
        verdict="conforme",
        explanation=(
            "L'allégation au niveau « entreprise » ne semble pas limitée à un "
            "aspect partiel. La portée déclarée paraît cohérente avec le contenu."
        ),
    )


# ---------------------------------------------------------------------------
# Règle 5 — Engagements futurs
# ---------------------------------------------------------------------------

def rule_future_commitment(claim: Claim) -> ClaimResult:
    """Vérifie la conformité des engagements futurs."""
    if not claim.is_future_commitment:
        return ClaimResult(
            claim_id=claim.id,
            criterion="future_commitment",
            verdict="non_applicable",
            explanation="L'allégation n'est pas un engagement futur.",
        )

    has_date = claim.target_date is not None
    has_verif = claim.has_independent_verification

    if has_date and has_verif:
        return ClaimResult(
            claim_id=claim.id,
            criterion="future_commitment",
            verdict="conforme",
            explanation=(
                f"L'engagement futur dispose d'une date cible "
                f"({claim.target_date}) et d'un suivi par un vérificateur indépendant."
            ),
        )

    missing = []
    if not has_date:
        missing.append("date cible")
    if not has_verif:
        missing.append("vérification indépendante")

    return ClaimResult(
        claim_id=claim.id,
        criterion="future_commitment",
        verdict="non_conforme",
        explanation=(
            f"L'engagement futur est incomplet : il manque {' et '.join(missing)}. "
            f"EmpCo exige un calendrier précis et un suivi indépendant."
        ),
        recommendation=(
            "Définir une date cible précise et mandater un organisme indépendant "
            "pour suivre et vérifier la réalisation de l'engagement."
        ),
        regulation_reference="Directive EmpCo (EU 2024/825), Annexe I, point 5 — engagements environnementaux futurs",
    )


# ---------------------------------------------------------------------------
# Règle 6 — Preuve et traçabilité
# ---------------------------------------------------------------------------

def rule_justification(claim: Claim) -> ClaimResult:
    """Vérifie la présence et la qualité des preuves."""
    if not claim.has_proof or claim.proof_type == "aucune":
        return ClaimResult(
            claim_id=claim.id,
            criterion="justification",
            verdict="non_conforme",
            explanation=(
                "Aucune preuve fournie pour étayer cette allégation. "
                "Toute allégation environnementale doit être justifiée."
            ),
            recommendation=(
                "Fournir une preuve vérifiable : certification tierce, "
                "données fournisseur traçables ou rapport d'audit indépendant."
            ),
            regulation_reference="Directive EmpCo (EU 2024/825), Art. 3 — obligation de justification des allégations",
        )

    if claim.proof_type in ("certification_tierce", "donnees_fournisseur"):
        return ClaimResult(
            claim_id=claim.id,
            criterion="justification",
            verdict="conforme",
            explanation=(
                f"L'allégation est étayée par une preuve de type « {claim.proof_type} ». "
                f"Ce niveau de justification est acceptable."
            ),
        )

    if claim.proof_type == "rapport_interne":
        return ClaimResult(
            claim_id=claim.id,
            criterion="justification",
            verdict="risque",
            explanation=(
                "L'allégation est étayée par un rapport interne. "
                "Cette preuve est considérée comme faible car non vérifiée "
                "par un tiers indépendant."
            ),
            recommendation=(
                "Faire valider le rapport interne par un organisme indépendant "
                "ou obtenir une certification tierce."
            ),
            regulation_reference="Directive EmpCo (EU 2024/825), Art. 3 — preuves scientifiques reconnues",
        )

    # Type de preuve non reconnu → risque
    return ClaimResult(
        claim_id=claim.id,
        criterion="justification",
        verdict="risque",
        explanation=(
            f"Le type de preuve « {claim.proof_type} » n'est pas dans les "
            f"catégories reconnues. Vérifier sa recevabilité."
        ),
        recommendation="Fournir une certification tierce ou des données fournisseur traçables.",
        regulation_reference="Directive EmpCo (EU 2024/825), Art. 3",
    )


# ---------------------------------------------------------------------------
# Orchestration : analyse complète d'une claim
# ---------------------------------------------------------------------------

ALL_RULES = [
    rule_specificity,
    rule_compensation,
    rule_labels,
    rule_proportionality,
    rule_future_commitment,
    rule_justification,
]


def analyze_claim(claim: Claim) -> Tuple[List[ClaimResult], str]:
    """
    Applique les 6 règles sur une claim.

    Retourne (liste de ClaimResult, overall_verdict).

    Logique du verdict global :
    - "non_conforme" si au moins 1 critère est non_conforme
    - "risque" si aucun non_conforme mais 2+ critères "risque"
    - "conforme" sinon (0 non_conforme et max 1 risque)
    """
    results: List[ClaimResult] = []
    for rule_fn in ALL_RULES:
        result = rule_fn(claim)
        results.append(result)

    non_conforme_count = sum(1 for r in results if r.verdict == "non_conforme")
    risque_count = sum(1 for r in results if r.verdict == "risque")

    if non_conforme_count > 0:
        overall = "non_conforme"
    elif risque_count >= 2:
        overall = "risque"
    else:
        overall = "conforme"

    return results, overall
