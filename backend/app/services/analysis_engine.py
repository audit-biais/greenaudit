"""
Moteur d'analyse des 8 règles EmpCo (EU 2024/825) + loi AGEC France.

Pour chaque claim, applique 8 critères et produit un ClaimResult par règle.

Références directrices :
- Directive 2005/29/CE modifiée par la Directive (UE) 2024/825 (« EmpCo »)
- Annexe I : pratiques commerciales réputées déloyales en toutes circonstances
- Art. 6 : actions trompeuses
- Art. 7 : omissions trompeuses
- Loi AGEC n°2020-105 du 10 février 2020, Art. 13 (France uniquement)

VERSIONING DES RÈGLES
---------------------
Quand EmpCo évolue (nouvelles annexes, nouveaux articles, transpositions nationales) :
1. Incrémenter RULES_VERSION ci-dessous
2. Mettre à jour blacklist.py (termes / patterns concernés)
3. Mettre à jour les fonctions rule_* impactées
4. Pousser en prod → les nouveaux audits porteront la nouvelle version
5. Les anciens audits conservent leur rules_version d'origine (traçabilité)

Changelog :
- 1.0.0 : 7 règles EmpCo de base (spécificité, compensation, labels, proportionnalité,
          engagements futurs, justification, exigence légale)
- 1.1.0 : Filtre Écolabel sur rule_specificity (Art. 2(s) + has_ecolabel_evidence)
          Proportionnalité composants mineurs scope=produit (Annexe I, 4ter)
          Règle 8 AGEC France (loi n°2020-105, Art. 13)
          Champ country sur Audit
"""

from __future__ import annotations

# Version des règles appliquées — à incrémenter à chaque modification du moteur
RULES_VERSION = "1.1.0"

import re
from typing import Dict, List, Optional, Tuple

from app.models.claim import Claim
from app.models.claim_result import ClaimResult
from app.utils.blacklist import (
    AGEC_ABSOLUTE_FORBIDDEN_NORMALIZED,
    BLACKLIST_TERMS,
    BLACKLIST_TERMS_NORMALIZED,
    CARBON_NEUTRAL_TERMS,
    LEGAL_REQUIREMENT_PATTERNS,
    MINOR_COMPONENT_PATTERNS,
    PARTIAL_SCOPE_PATTERNS,
    QUALIFICATION_PATTERNS,
    _normalize,
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
    """Retourne le premier terme blacklisté trouvé dans le texte, ou None.

    La détection est insensible à la casse ET aux accents :
    'eco-responsable' matche 'éco-responsable' et vice versa.
    """
    text_normalized = _normalize(text)
    for norm_term, original_term in BLACKLIST_TERMS_NORMALIZED:
        if norm_term in text_normalized:
            return original_term
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


def _find_minor_component(text: str) -> Optional[str]:
    """Retourne le premier composant mineur mentionné, ou None."""
    for pattern in MINOR_COMPONENT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _find_agec_forbidden(text: str) -> Optional[str]:
    """Retourne le premier terme absolument interdit par la loi AGEC, ou None."""
    text_normalized = _normalize(text)
    for norm_term, original_term in AGEC_ABSOLUTE_FORBIDDEN_NORMALIZED:
        if norm_term in text_normalized:
            return original_term
    return None


def _find_legal_requirement_match(text: str) -> Optional[str]:
    """Retourne le premier pattern d'exigence légale trouvé, ou None."""
    for pattern in LEGAL_REQUIREMENT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


# ---------------------------------------------------------------------------
# Règle 1 — Claims génériques (Annexe I, point 4bis)
# ---------------------------------------------------------------------------

def rule_specificity(claim: Claim, has_ecolabel_evidence: bool = False) -> ClaimResult:
    """
    Détecte les allégations environnementales génériques.

    Annexe I, point 4bis : « Présenter une allégation environnementale générique
    au sujet de laquelle le professionnel n'est pas en mesure de démontrer
    l'excellente performance environnementale reconnue en rapport avec l'allégation. »

    La « performance environnementale excellente reconnue » (Art. 2(s)) correspond
    au label écologique de l'UE (règlement CE 66/2010), aux systèmes ISO 14024
    de type I, ou aux meilleures performances en vertu du droit de l'Union.

    Si un Écolabel officiel est présent dans l'Evidence Vault de la claim,
    l'allégation peut être conforme même avec un terme générique.
    """
    text = _text_lower(claim)
    matched_term = _find_blacklist_match(text)

    if matched_term is None:
        return ClaimResult(
            claim_id=claim.id,
            criterion="specificity",
            verdict="non_applicable",
            explanation="Aucun terme générique interdit détecté dans l'allégation.",
        )

    # Filtre Écolabel : un écolabel officiel dans le vault démontre la "performance
    # environnementale excellente reconnue" exigée par l'Art. 2(s)
    if has_ecolabel_evidence:
        return ClaimResult(
            claim_id=claim.id,
            criterion="specificity",
            verdict="conforme",
            explanation=(
                f"Le terme « {matched_term} » est présent mais un Écolabel officiel "
                f"(EU Ecolabel, ISO 14024 Type I ou équivalent) a été déposé dans "
                f"l'Evidence Vault. Cela constitue la « performance environnementale "
                f"excellente reconnue » exigée par l'Art. 2(s) et l'Annexe I, point 4bis."
            ),
            recommendation=(
                "Conserver l'Écolabel dans vos dossiers de conformité. "
                "S'assurer que l'écolabel est affiché visiblement avec l'allégation "
                "sur tous les supports (Art. 6.1(b))."
            ),
            regulation_reference=(
                "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                "Annexe I, point 4bis + Art. 2(s) — performance environnementale "
                "excellente reconnue via Écolabel EU / ISO 14024 Type I"
            ),
        )

    if _has_qualification(text):
        return ClaimResult(
            claim_id=claim.id,
            criterion="specificity",
            verdict="risque",
            explanation=(
                f"Le terme « {matched_term} » est présent mais accompagné d'une "
                f"qualification. Attention : l'Annexe I point 4bis exige une "
                f"« performance environnementale excellente reconnue » (EU Ecolabel, "
                f"ISO 14024 Type I ou équivalent). Une simple mention chiffrée "
                f"ne suffit pas toujours à satisfaire cette exigence."
            ),
            recommendation=(
                "Déposer un Écolabel officiel (EU Ecolabel, ISO 14024 Type I) "
                "dans l'Evidence Vault pour sécuriser cette allégation, "
                "ou reformuler l'allégation de manière spécifique et mesurable."
            ),
            regulation_reference=(
                "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                "Annexe I, point 4bis — allégation environnementale générique "
                "sans performance excellente reconnue (Art. 2(s))"
            ),
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="specificity",
        verdict="non_conforme",
        explanation=(
            f"Le terme « {matched_term} » est utilisé seul, sans qualification "
            f"spécifique ni Écolabel officiel. Cette pratique est interdite en "
            f"toutes circonstances par l'Annexe I, point 4bis."
        ),
        recommendation=(
            f"Supprimer le terme « {matched_term} » ou obtenir un Écolabel officiel "
            f"(EU Ecolabel, Ange Bleu, ISO 14024 Type I) et le déposer dans l'Evidence Vault. "
            f"Alternative : reformuler avec une allégation spécifique et mesurable, "
            f"ex : « contient 30 % de matières recyclées certifiées »."
        ),
        regulation_reference=(
            "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
            "Annexe I, point 4bis — pratique réputée déloyale en toutes circonstances"
        ),
    )


# ---------------------------------------------------------------------------
# Règle 2 — Neutralité carbone par compensation (Annexe I, point 4quater)
# ---------------------------------------------------------------------------

def rule_compensation(claim: Claim) -> ClaimResult:
    """
    Détecte les claims de neutralité carbone basées sur la compensation.

    Annexe I, point 4quater : « Affirmer, sur la base de la compensation des
    émissions de gaz à effet de serre, qu'un produit a un impact neutre, réduit
    ou positif sur l'environnement en termes d'émissions de gaz à effet de serre. »

    C'est une interdiction absolue — pas de nuance possible.
    """
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
            f"L'allégation contient « {matched_term} ». Toute affirmation d'impact "
            f"neutre, réduit ou positif en termes d'émissions de GES basée sur "
            f"la compensation est interdite en toutes circonstances par l'Annexe I, "
            f"point 4quater."
        ),
        recommendation=(
            "Supprimer toute référence à la neutralité carbone ou à la compensation. "
            "Communiquer plutôt sur les réductions d'émissions concrètes et mesurables "
            "de l'entreprise (ex : « -25 % d'émissions CO2 entre 2022 et 2025 »)."
        ),
        regulation_reference=(
            "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
            "Annexe I, point 4quater — pratique réputée déloyale en toutes circonstances"
        ),
    )


# ---------------------------------------------------------------------------
# Règle 3 — Labels auto-décernés (Annexe I, point 2bis + Art. 2(r))
# ---------------------------------------------------------------------------

def rule_labels(claim: Claim) -> ClaimResult:
    """
    Vérifie la conformité des labels de développement durable.

    Annexe I, point 2bis : « Afficher un label de développement durable qui n'est
    pas fondé sur un système de certification ou qui n'a pas été mis en place
    par des autorités publiques. »

    Art. 2(r) définit les 4 critères obligatoires d'un système de certification :
    (i) ouvert à conditions transparentes, équitables et non discriminatoires
    (ii) exigences élaborées avec experts et parties prenantes
    (iii) procédures de non-conformité (retrait/suspension)
    (iv) contrôle par tiers indépendant (normes internationales)
    """
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
                f"Le label « {claim.label_name or 'non précisé'} » est déclaré "
                f"comme certifié par un organisme tiers. Pour être pleinement conforme "
                f"à l'Art. 2(r), vérifier que le système de certification répond aux "
                f"4 critères : (i) ouvert et non discriminatoire, (ii) exigences "
                f"co-élaborées avec experts, (iii) procédures de retrait en cas de "
                f"non-conformité, (iv) contrôle par tiers indépendant."
            ),
            recommendation=(
                "S'assurer que le système de certification du label satisfait "
                "les 4 critères de l'Art. 2(r) de la directive 2005/29/CE modifiée. "
                "Conserver la preuve de certification à disposition."
            ),
            regulation_reference=(
                "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                "Annexe I, point 2bis + Art. 2(r) — système de certification"
            ),
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="labels",
        verdict="non_conforme",
        explanation=(
            f"Le label « {claim.label_name or 'non précisé'} » est auto-décerné "
            f"(non fondé sur un système de certification tiers ni mis en place par "
            f"des autorités publiques). Cette pratique est interdite en toutes "
            f"circonstances par l'Annexe I, point 2bis."
        ),
        recommendation=(
            "Retirer ce label ou obtenir une certification par un organisme tiers "
            "indépendant répondant aux 4 critères de l'Art. 2(r) : système ouvert, "
            "exigences co-élaborées, procédures de retrait, contrôle indépendant."
        ),
        regulation_reference=(
            "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
            "Annexe I, point 2bis — pratique réputée déloyale en toutes circonstances"
        ),
    )


# ---------------------------------------------------------------------------
# Règle 4 — Proportionnalité (Annexe I, point 4ter)
# ---------------------------------------------------------------------------

def rule_proportionality(claim: Claim) -> ClaimResult:
    """
    Vérifie la proportionnalité entre le scope déclaré et le contenu réel.

    Annexe I, point 4ter : « Présenter une allégation environnementale concernant
    l'ensemble du produit ou de l'entreprise du professionnel, alors qu'elle ne
    concerne qu'un des aspects du produit ou une activité spécifique de l'entreprise. »

    Deux cas détectés :
    1. scope=entreprise + mention d'un aspect partiel → risque
    2. scope=produit + mention d'un composant mineur seulement → non_conforme
       (ex : "Ce produit est durable car le bouchon est recyclé")
    """
    text = _text_lower(claim)

    if claim.scope == "entreprise":
        if _has_partial_scope_mention(text):
            return ClaimResult(
                claim_id=claim.id,
                criterion="proportionality",
                verdict="risque",
                explanation=(
                    "L'allégation est déclarée au niveau « entreprise » mais le texte "
                    "mentionne un aspect partiel (emballage, transport, produit…). "
                    "L'Annexe I, point 4ter interdit de présenter une allégation sur "
                    "l'ensemble de l'entreprise alors qu'elle ne concerne qu'une "
                    "activité spécifique."
                ),
                recommendation=(
                    "Reformuler l'allégation pour préciser qu'elle ne concerne qu'un "
                    "aspect spécifique de l'activité, ou fournir des preuves couvrant "
                    "l'ensemble de l'entreprise."
                ),
                regulation_reference=(
                    "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                    "Annexe I, point 4ter — pratique réputée déloyale en toutes circonstances"
                ),
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

    # scope = produit : non conforme UNIQUEMENT si le texte contient à la fois
    # un terme générique global (durable, vert, écologique...) ET un composant mineur.
    # Exemple non conforme : "Ce produit est durable grâce à son bouchon recyclé"
    # Exemple conforme    : "Notre bouchon est en plastique recyclé" (périmètre honnête)
    minor_component = _find_minor_component(text)
    if minor_component:
        global_term = _find_blacklist_match(text)
        if global_term:
            return ClaimResult(
                claim_id=claim.id,
                criterion="proportionality",
                verdict="non_conforme",
                explanation=(
                    f"L'allégation utilise le terme global « {global_term} » pour "
                    f"décrire le produit entier, alors que la justification environnementale "
                    f"ne porte que sur un composant mineur (« {minor_component} »). "
                    f"L'Annexe I, point 4ter interdit de suggérer qu'une caractéristique "
                    f"partielle s'applique à l'ensemble du produit."
                ),
                recommendation=(
                    f"Soit reformuler en limitant explicitement le périmètre : "
                    f"ex. « Le {minor_component} de ce produit est en matériau recyclé ». "
                    f"Soit fournir des preuves que l'avantage environnemental couvre "
                    f"l'ensemble du cycle de vie du produit."
                ),
                regulation_reference=(
                    "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                    "Annexe I, point 4ter — pratique réputée déloyale en toutes circonstances"
                ),
            )

    return ClaimResult(
        claim_id=claim.id,
        criterion="proportionality",
        verdict="non_applicable",
        explanation="La règle de proportionnalité produit ne s'applique pas à cette allégation.",
    )


# ---------------------------------------------------------------------------
# Règle 5 — Engagements futurs (Art. 6, paragraphe 2, point d)
# ---------------------------------------------------------------------------

def rule_future_commitment(claim: Claim) -> ClaimResult:
    """
    Vérifie la conformité des engagements environnementaux futurs.

    Art. 6, paragraphe 2, point d) : constitue une action trompeuse « une
    allégation environnementale relative aux performances futures sans
    engagements clairs, objectifs, accessibles au public et vérifiables inscrits
    dans un plan de mise en œuvre détaillé et réaliste qui inclut des objectifs
    mesurables et assortis d'échéances ainsi que d'autres éléments pertinents
    requis à l'appui de sa réalisation, tels que l'affectation de ressources,
    et qui est régulièrement vérifié par un tiers expert indépendant, dont les
    conclusions sont mises à la disposition des consommateurs. »
    """
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
                f"({claim.target_date}) et d'un suivi par un vérificateur "
                f"indépendant. Pour être pleinement conforme à l'Art. 6.2(d), "
                f"l'entreprise doit également disposer d'un plan de mise en œuvre "
                f"détaillé avec objectifs mesurables, allocation de ressources, et "
                f"les conclusions du vérificateur doivent être accessibles au public."
            ),
            recommendation=(
                "Vérifier l'existence d'un plan de mise en œuvre détaillé et "
                "réaliste incluant : objectifs mesurables avec échéances, "
                "affectation de ressources, et publication des conclusions "
                "du vérificateur indépendant."
            ),
            regulation_reference=(
                "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                "Art. 6, paragraphe 2, point d) — engagements environnementaux futurs"
            ),
        )

    missing = []
    if not has_date:
        missing.append("date cible avec échéances mesurables")
    if not has_verif:
        missing.append("vérification par un tiers expert indépendant")

    return ClaimResult(
        claim_id=claim.id,
        criterion="future_commitment",
        verdict="non_conforme",
        explanation=(
            f"L'engagement futur est incomplet : il manque {' et '.join(missing)}. "
            f"L'Art. 6.2(d) exige un plan de mise en œuvre détaillé et réaliste "
            f"avec objectifs mesurables, allocation de ressources, et vérification "
            f"régulière par un tiers indépendant dont les conclusions sont publiques."
        ),
        recommendation=(
            "Établir un plan de mise en œuvre détaillé incluant : "
            "(1) des objectifs mesurables avec échéances précises, "
            "(2) l'affectation de ressources dédiées, "
            "(3) un mandat de vérification par un tiers expert indépendant, "
            "(4) la publication des conclusions de vérification."
        ),
        regulation_reference=(
            "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
            "Art. 6, paragraphe 2, point d) — action trompeuse"
        ),
    )


# ---------------------------------------------------------------------------
# Règle 6 — Preuve et traçabilité (Art. 6.1(b) + Art. 7)
# ---------------------------------------------------------------------------

def rule_justification(
    claim: Claim,
    scan_mode: bool = False,
    specificity_verdict: str = "non_conforme",
) -> ClaimResult:
    """
    Vérifie la présence et la qualité des preuves.

    Art. 6, paragraphe 1, point b) : les « caractéristiques environnementales »
    du produit font partie des informations ne devant pas être trompeuses.
    Art. 7 : omettre une information substantielle est une omission trompeuse.

    En mode scan → risque (preuves non vérifiables automatiquement, risque réglementaire direct).
    Quand has_proof = False, la recommandation est différenciée selon la qualité
    de la formulation (verdict spécificité transmis par analyze_claim) :
    - conforme / non_applicable → formulation OK, action = Documenter
    - risque                    → formulation perfectible, action = Documenter et préciser
    - non_conforme              → formulation vague, action = Reformuler puis documenter
    """
    if not claim.has_proof or claim.proof_type == "aucune":
        if scan_mode:
            return ClaimResult(
                claim_id=claim.id,
                criterion="justification",
                verdict="risque",
                explanation=(
                    "Preuves non vérifiées. "
                    "Cette allégation a été détectée automatiquement par scan. "
                    "Toute allégation environnementale doit être étayée par des preuves "
                    "vérifiables (Art. 6.1(b)). L'absence de preuve documentée constitue "
                    "un risque réglementaire direct."
                ),
                recommendation=(
                    "Documenter cette allégation avec une preuve vérifiable : "
                    "certification tierce, données fournisseur traçables ou rapport "
                    "d'audit indépendant."
                ),
                regulation_reference=(
                    "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                    "Art. 6, paragraphe 1, point b) + Art. 7"
                ),
            )

        # Recommandation différenciée selon la qualité de la formulation
        if specificity_verdict in ("conforme", "non_applicable"):
            recommendation = (
                "La formulation est suffisamment précise. "
                "Action requise : documenter l'allégation en fournissant une preuve "
                "vérifiable (certification tierce, données fournisseur traçables "
                "ou rapport d'audit indépendant)."
            )
        elif specificity_verdict == "risque":
            recommendation = (
                "La formulation est acceptable mais perfectible. "
                "Action requise : (1) préciser davantage l'allégation si possible, "
                "(2) la documenter avec une preuve vérifiable (certification tierce "
                "ou données fournisseur traçables)."
            )
        else:  # non_conforme
            recommendation = (
                "La formulation est trop vague ou générique. "
                "Action requise : (1) reformuler l'allégation de façon spécifique "
                "et mesurable, (2) la documenter avec une preuve vérifiable "
                "(certification tierce ou données fournisseur traçables)."
            )

        return ClaimResult(
            claim_id=claim.id,
            criterion="justification",
            verdict="non_conforme",
            explanation=(
                "Aucune preuve fournie pour étayer cette allégation. "
                "Toute allégation environnementale doit être justifiée par "
                "des preuves vérifiables sous peine de constituer une action "
                "trompeuse (Art. 6.1(b)) ou une omission trompeuse (Art. 7)."
            ),
            recommendation=recommendation,
            regulation_reference=(
                "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                "Art. 6, paragraphe 1, point b) + Art. 7 — justification des "
                "caractéristiques environnementales"
            ),
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
            regulation_reference=(
                "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
                "Art. 6, paragraphe 1, point b) — preuves des caractéristiques "
                "environnementales"
            ),
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
        regulation_reference=(
            "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
            "Art. 6, paragraphe 1, point b)"
        ),
    )


# ---------------------------------------------------------------------------
# Règle 7 — Exigences légales comme avantage distinctif (Annexe I, 10bis)
# ---------------------------------------------------------------------------

def rule_legal_requirement(claim: Claim) -> ClaimResult:
    """
    Détecte les exigences légales présentées comme caractéristique distinctive.

    Annexe I, point 10bis : « Présenter comme une caractéristique distinctive
    de l'offre du professionnel des exigences imposées par la loi pour tous
    les produits de la catégorie de produits concernée sur le marché de l'Union. »

    Exemples : « sans BPA » (interdit par règlement EU), « conforme REACH »
    (obligatoire pour tous), « emballage recyclable » (obligation AGEC).
    """
    text = _text_lower(claim)
    matched = _find_legal_requirement_match(text)

    if matched is None:
        return ClaimResult(
            claim_id=claim.id,
            criterion="legal_requirement",
            verdict="non_applicable",
            explanation=(
                "Aucune mention d'exigence légale présentée comme avantage distinctif "
                "n'a été détectée."
            ),
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="legal_requirement",
        verdict="non_conforme",
        explanation=(
            f"L'allégation contient « {matched} » qui correspond à une exigence "
            f"imposée par la réglementation pour tous les produits de cette catégorie. "
            f"Présenter une obligation légale comme un avantage distinctif est interdit "
            f"en toutes circonstances par l'Annexe I, point 10bis."
        ),
        recommendation=(
            f"Supprimer la mention « {matched} » qui constitue une obligation légale, "
            f"pas un avantage distinctif. Pour communiquer sur vos engagements "
            f"environnementaux, mettez en avant des actions volontaires allant "
            f"au-delà des exigences réglementaires."
        ),
        regulation_reference=(
            "Directive 2005/29/CE modifiée par EmpCo (EU 2024/825), "
            "Annexe I, point 10bis — pratique réputée déloyale en toutes circonstances"
        ),
    )


# ---------------------------------------------------------------------------
# Règle 8 — Termes absolument interdits en France (Loi AGEC Art. 13)
# ---------------------------------------------------------------------------

def rule_agec_france(claim: Claim, country: str = "fr") -> ClaimResult:
    """
    Détecte les termes interdits par la loi AGEC (Art. 13) en France.

    La loi AGEC (Anti-Gaspillage pour une Économie Circulaire, loi n°2020-105)
    interdit ABSOLUMENT les mentions « biodégradable », « respectueux de
    l'environnement » et termes équivalents sur tout produit mis sur le marché
    français — sans exception possible, même avec preuve ou certification.

    Cette règle est plus sévère qu'EmpCo : EmpCo permet ces termes avec
    un Écolabel, la loi AGEC les interdit systématiquement.

    S'applique uniquement si country="fr".
    """
    if country.lower() != "fr":
        return ClaimResult(
            claim_id=claim.id,
            criterion="agec_france",
            verdict="non_applicable",
            explanation="La règle AGEC ne s'applique qu'aux produits commercialisés en France.",
        )

    text = _text_lower(claim)
    matched_term = _find_agec_forbidden(text)

    if matched_term is None:
        return ClaimResult(
            claim_id=claim.id,
            criterion="agec_france",
            verdict="non_applicable",
            explanation="Aucun terme interdit par la loi AGEC (Art. 13) détecté.",
        )

    return ClaimResult(
        claim_id=claim.id,
        criterion="agec_france",
        verdict="non_conforme",
        explanation=(
            f"Le terme « {matched_term} » est formellement interdit en France par "
            f"la loi AGEC (Art. 13, loi n°2020-105 du 10 février 2020). "
            f"Cette interdiction est absolue : aucune preuve, certification ou "
            f"Écolabel ne peut la lever. Elle est plus stricte que la directive "
            f"EmpCo (EU 2024/825) sur ce point spécifique."
        ),
        recommendation=(
            f"Supprimer immédiatement le terme « {matched_term} » de tous les supports "
            f"commerciaux destinés au marché français. "
            f"Remplacer par une allégation spécifique et quantifiée, ex : "
            f"« se décompose en 6 mois dans des conditions industrielles certifiées EN 13432 »."
        ),
        regulation_reference=(
            "Loi AGEC n°2020-105 du 10 février 2020, Art. 13 — "
            "interdiction des mentions « biodégradable » et « respectueux de "
            "l'environnement » sur les produits (marché français)"
        ),
    )


# ---------------------------------------------------------------------------
# Orchestration : analyse complète d'une claim
# ---------------------------------------------------------------------------

def analyze_claim(
    claim: Claim,
    has_ecolabel_evidence: bool = False,
    country: str = "fr",
    scan_mode: bool = False,
) -> Tuple[List[ClaimResult], str]:
    """
    Applique les 8 règles sur une claim.

    Paramètres :
    - has_ecolabel_evidence : True si un document de type "ecolabel" est dans
      l'Evidence Vault de cette claim (débloque le verdict conforme pour rule_specificity)
    - country : code pays ISO pour les règles nationales (défaut "fr" → loi AGEC)

    Retourne (liste de ClaimResult, overall_verdict).

    Logique du verdict global :
    - "non_conforme" si au moins 1 critère est non_conforme
    - "risque" si aucun non_conforme mais 2+ critères "risque"
    - "conforme" sinon (0 non_conforme et max 1 risque)
    """
    results: List[ClaimResult] = []

    # Règles avec paramètres spécifiques
    specificity_result = rule_specificity(claim, has_ecolabel_evidence=has_ecolabel_evidence)
    results.append(specificity_result)
    results.append(rule_compensation(claim))
    results.append(rule_labels(claim))
    results.append(rule_proportionality(claim))
    results.append(rule_future_commitment(claim))
    results.append(rule_justification(
        claim,
        scan_mode=scan_mode,
        specificity_verdict=specificity_result.verdict,
    ))
    results.append(rule_legal_requirement(claim))
    results.append(rule_agec_france(claim, country=country))

    non_conforme_count = sum(1 for r in results if r.verdict == "non_conforme")
    risque_count = sum(1 for r in results if r.verdict == "risque")

    if non_conforme_count > 0:
        overall = "non_conforme"
    elif risque_count >= 2:
        overall = "risque"
    else:
        overall = "conforme"

    return results, overall
