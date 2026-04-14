"""
Classificateur du régime juridique EmpCo pour chaque allégation environnementale.

Architecture 3 étages du moteur d'analyse :
  (1) Détection      — extract_claims_with_claude() dans monitoring_service.py
  (2) Classification — classify_claim_regime() ← CE MODULE
  (3) Évaluation     — analyze_claim() dans analysis_engine.py (8 règles)

Ce module détermine si une allégation relève de :
  - L'Annexe I de la directive 2005/29/CE modifiée (interdiction automatique → "liste_noire")
  - L'article 6 — évaluation au cas par cas → "cas_par_cas"

La classification s'applique au CLAIM entier, pas à chaque ClaimResult.
Elle est stockée dans les colonnes claims.regulatory_basis et claims.regime.

Logique : premier match gagne (priority order).

Pour l'étape 3 future : les verdicts de l'analysis_engine seront reformulés
en fonction de regulatory_basis pour distinguer les sanctions automatiques
(liste_noire) des évaluations contextuelles (cas_par_cas).
"""

from __future__ import annotations

import re
from typing import Optional

from app.utils.blacklist import (
    BLACKLIST_TERMS_NORMALIZED,
    CARBON_NEUTRAL_TERMS,
    LEGAL_REQUIREMENT_PATTERNS,
    PARTIAL_SCOPE_PATTERNS,
    QUALIFICATION_PATTERNS,
    _normalize,
)

# Patterns indiquant que la neutralité carbone est présentée hors compensation
_NO_COMPENSATION_PATTERNS = [
    r"sans\s+compensation",
    r"hors\s+compensation",
    r"sans\s+offset",
    r"hors\s+offset",
    r"réduction[s]?\s+(réelle[s]?|effective[s]?|directe[s]?)",
]


def _has_qualification(text: str) -> bool:
    for pattern in QUALIFICATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _find_blacklist_match(text_normalized: str) -> Optional[str]:
    for norm_term, original_term in BLACKLIST_TERMS_NORMALIZED:
        if " " in norm_term or "-" in norm_term:
            if norm_term in text_normalized:
                return original_term
        else:
            # s? pour matcher les pluriels (ecologique → ecologiques, vert → verts)
            if re.search(r"\b" + re.escape(norm_term) + r"s?\b", text_normalized):
                return original_term
    return None


def _find_carbon_neutral_match(text: str) -> Optional[str]:
    for term in CARBON_NEUTRAL_TERMS:
        if term.lower() in text:
            return term
    return None


def _has_partial_scope_mention(text: str) -> bool:
    for pattern in PARTIAL_SCOPE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _find_legal_requirement_match(text: str) -> Optional[str]:
    for pattern in LEGAL_REQUIREMENT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _claims_no_compensation(text: str) -> bool:
    for pattern in _NO_COMPENSATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


async def classify_claim_regime(
    claim_text: str,
    claim_metadata: dict,
) -> dict:
    """
    Détermine le régime juridique applicable à une allégation EmpCo.

    Paramètres :
    - claim_text : texte brut de l'allégation
    - claim_metadata : dict avec les champs du modèle Claim :
        has_label (bool), label_is_certified (bool|None),
        scope (str), is_future_commitment (bool),
        has_proof (bool), proof_type (str|None)

    Retourne :
        {
            "regulatory_basis": str,   # ex: "annexe_I_4bis"
            "regime": str,             # "liste_noire" ou "cas_par_cas"
            "rationale": str,          # explication courte pour debug/logs
        }

    Logique (premier match gagne) :
    1. Label auto-décerné                    → annexe_I_2bis   / liste_noire
    2. Neutralité carbone par compensation   → annexe_I_4quater / liste_noire
    3. Terme générique sans qualification    → annexe_I_4bis   / liste_noire
    4. Allégation entreprise sur aspect part → annexe_I_4ter   / liste_noire
    5. Engagement futur                      → article_6_1d    / cas_par_cas
    6. Exigence légale présentée distinc.    → annexe_I_10bis  / liste_noire
    7. Défaut                                → article_6_general / cas_par_cas
    """
    text = claim_text.lower().strip()
    text_normalized = _normalize(text)

    # ── Règle 1 : label auto-décerné (Annexe I, point 2bis) ──────────────────
    if claim_metadata.get("has_label") and not claim_metadata.get("label_is_certified"):
        return {
            "regulatory_basis": "annexe_I_2bis",
            "regime": "liste_noire",
            "rationale": "Label déclaré sans certification tierce — Annexe I, point 2bis",
        }

    # ── Règle 2 : neutralité carbone par compensation (Annexe I, point 4quater) ─
    carbon_term = _find_carbon_neutral_match(text)
    if carbon_term and not _claims_no_compensation(text):
        return {
            "regulatory_basis": "annexe_I_4quater",
            "regime": "liste_noire",
            "rationale": f"Terme '{carbon_term}' sans exclusion explicite de compensation — Annexe I, point 4quater",
        }

    # ── Règle 3 : terme générique sans qualification (Annexe I, point 4bis) ──
    blacklist_term = _find_blacklist_match(text_normalized)
    if blacklist_term and not _has_qualification(text):
        return {
            "regulatory_basis": "annexe_I_4bis",
            "regime": "liste_noire",
            "rationale": f"Terme générique '{blacklist_term}' sans qualification mesurable — Annexe I, point 4bis",
        }

    # ── Règle 4 : proportionnalité (Annexe I, point 4ter) ────────────────────
    if claim_metadata.get("scope") == "entreprise" and _has_partial_scope_mention(text):
        return {
            "regulatory_basis": "annexe_I_4ter",
            "regime": "liste_noire",
            "rationale": "Allégation 'entreprise' portant sur un aspect partiel — Annexe I, point 4ter",
        }

    # ── Règle 5 : engagement futur (Art. 6, §2, point d) ─────────────────────
    if claim_metadata.get("is_future_commitment"):
        return {
            "regulatory_basis": "article_6_1d",
            "regime": "cas_par_cas",
            "rationale": "Engagement futur à évaluer selon Art. 6.2(d)",
        }

    # ── Règle 6 : exigence légale présentée comme distinctive (Annexe I, 10bis)
    legal_match = _find_legal_requirement_match(text)
    if legal_match:
        return {
            "regulatory_basis": "annexe_I_10bis",
            "regime": "liste_noire",
            "rationale": f"Exigence légale '{legal_match}' présentée comme avantage — Annexe I, point 10bis",
        }

    # ── Règle 7 : défaut — allégation spécifique à évaluer au cas par cas ───
    return {
        "regulatory_basis": "article_6_general",
        "regime": "cas_par_cas",
        "rationale": "Allégation spécifique ou qualifiée — évaluation au cas par cas Art. 6",
    }
