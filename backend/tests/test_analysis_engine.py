"""Tests unitaires du moteur d'analyse — les 6 règles EmpCo."""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.claim import Claim
from app.services.analysis_engine import (
    analyze_claim,
    rule_compensation,
    rule_future_commitment,
    rule_justification,
    rule_labels,
    rule_proportionality,
    rule_specificity,
)


def _make_claim(**kwargs) -> Claim:
    """Crée une Claim en mémoire (sans DB) avec des valeurs par défaut."""
    defaults = {
        "id": uuid.uuid4(),
        "audit_id": uuid.uuid4(),
        "claim_text": "Allégation test",
        "support_type": "web",
        "scope": "produit",
        "has_proof": False,
        "proof_type": None,
        "has_label": False,
        "label_is_certified": None,
        "label_name": None,
        "is_future_commitment": False,
        "target_date": None,
        "has_independent_verification": False,
        "product_name": None,
    }
    defaults.update(kwargs)
    return Claim(**defaults)


# ===================================================================
# Règle 1 — Spécificité (blacklist)
# ===================================================================

class TestRuleSpecificity:
    def test_no_blacklist_term(self):
        claim = _make_claim(claim_text="Nos emballages contiennent 30% de carton recyclé")
        result = rule_specificity(claim)
        assert result.verdict == "non_applicable"

    def test_blacklist_term_alone(self):
        claim = _make_claim(claim_text="Notre produit est écologique")
        result = rule_specificity(claim)
        assert result.verdict == "non_conforme"
        assert "écologique" in result.explanation

    def test_blacklist_term_with_qualification(self):
        claim = _make_claim(claim_text="Produit écologique : 30% de matières recyclées certifiées ISO 14001")
        result = rule_specificity(claim)
        assert result.verdict == "risque"

    def test_green_alone(self):
        claim = _make_claim(claim_text="Un produit green pour la planète")
        result = rule_specificity(claim)
        assert result.verdict == "non_conforme"

    def test_sustainable_with_percentage(self):
        claim = _make_claim(claim_text="Sustainable : réduction de 40% de nos émissions")
        result = rule_specificity(claim)
        assert result.verdict == "risque"


# ===================================================================
# Règle 2 — Neutralité carbone / compensation
# ===================================================================

class TestRuleCompensation:
    def test_no_carbon_neutral_term(self):
        claim = _make_claim(claim_text="Nous réduisons nos émissions de 20%")
        result = rule_compensation(claim)
        assert result.verdict == "non_applicable"

    def test_carbon_neutral(self):
        claim = _make_claim(claim_text="Notre entreprise est carbon neutral depuis 2024")
        result = rule_compensation(claim)
        assert result.verdict == "non_conforme"

    def test_neutre_en_carbone(self):
        claim = _make_claim(claim_text="Livraison neutre en carbone")
        result = rule_compensation(claim)
        assert result.verdict == "non_conforme"

    def test_net_zero(self):
        claim = _make_claim(claim_text="Objectif net zero atteint")
        result = rule_compensation(claim)
        assert result.verdict == "non_conforme"

    def test_compensation_carbone(self):
        claim = _make_claim(claim_text="Émissions en compensation carbone via reforestation")
        result = rule_compensation(claim)
        assert result.verdict == "non_conforme"


# ===================================================================
# Règle 3 — Labels
# ===================================================================

class TestRuleLabels:
    def test_no_label(self):
        claim = _make_claim(has_label=False)
        result = rule_labels(claim)
        assert result.verdict == "non_applicable"

    def test_certified_label(self):
        claim = _make_claim(
            has_label=True, label_name="EU Ecolabel", label_is_certified=True
        )
        result = rule_labels(claim)
        assert result.verdict == "conforme"

    def test_self_awarded_label(self):
        claim = _make_claim(
            has_label=True, label_name="Green Company", label_is_certified=False
        )
        result = rule_labels(claim)
        assert result.verdict == "non_conforme"
        assert "auto-décerné" in result.explanation


# ===================================================================
# Règle 4 — Proportionnalité
# ===================================================================

class TestRuleProportionality:
    def test_scope_produit(self):
        claim = _make_claim(scope="produit", claim_text="Emballage recyclable")
        result = rule_proportionality(claim)
        assert result.verdict == "non_applicable"

    def test_scope_entreprise_no_partial(self):
        claim = _make_claim(
            scope="entreprise",
            claim_text="Nous sommes engagés dans une démarche globale",
        )
        result = rule_proportionality(claim)
        assert result.verdict == "conforme"

    def test_scope_entreprise_mentions_emballage(self):
        claim = _make_claim(
            scope="entreprise",
            claim_text="Notre entreprise utilise uniquement des emballages recyclés",
        )
        result = rule_proportionality(claim)
        assert result.verdict == "risque"

    def test_scope_entreprise_mentions_transport(self):
        claim = _make_claim(
            scope="entreprise",
            claim_text="Nous avons réduit l'impact de notre transport",
        )
        result = rule_proportionality(claim)
        assert result.verdict == "risque"


# ===================================================================
# Règle 5 — Engagements futurs
# ===================================================================

class TestRuleFutureCommitment:
    def test_not_future(self):
        claim = _make_claim(is_future_commitment=False)
        result = rule_future_commitment(claim)
        assert result.verdict == "non_applicable"

    def test_future_complete(self):
        claim = _make_claim(
            is_future_commitment=True,
            target_date=date(2028, 12, 31),
            has_independent_verification=True,
        )
        result = rule_future_commitment(claim)
        assert result.verdict == "conforme"

    def test_future_no_date(self):
        claim = _make_claim(
            is_future_commitment=True,
            target_date=None,
            has_independent_verification=True,
        )
        result = rule_future_commitment(claim)
        assert result.verdict == "non_conforme"
        assert "date cible" in result.explanation

    def test_future_no_verification(self):
        claim = _make_claim(
            is_future_commitment=True,
            target_date=date(2028, 12, 31),
            has_independent_verification=False,
        )
        result = rule_future_commitment(claim)
        assert result.verdict == "non_conforme"
        assert "vérification indépendante" in result.explanation

    def test_future_missing_both(self):
        claim = _make_claim(
            is_future_commitment=True,
            target_date=None,
            has_independent_verification=False,
        )
        result = rule_future_commitment(claim)
        assert result.verdict == "non_conforme"
        assert "date cible" in result.explanation
        assert "vérification indépendante" in result.explanation


# ===================================================================
# Règle 6 — Justification / Preuves
# ===================================================================

class TestRuleJustification:
    def test_no_proof(self):
        claim = _make_claim(has_proof=False)
        result = rule_justification(claim)
        assert result.verdict == "non_conforme"

    def test_proof_type_aucune(self):
        claim = _make_claim(has_proof=True, proof_type="aucune")
        result = rule_justification(claim)
        assert result.verdict == "non_conforme"

    def test_certification_tierce(self):
        claim = _make_claim(has_proof=True, proof_type="certification_tierce")
        result = rule_justification(claim)
        assert result.verdict == "conforme"

    def test_donnees_fournisseur(self):
        claim = _make_claim(has_proof=True, proof_type="donnees_fournisseur")
        result = rule_justification(claim)
        assert result.verdict == "conforme"

    def test_rapport_interne(self):
        claim = _make_claim(has_proof=True, proof_type="rapport_interne")
        result = rule_justification(claim)
        assert result.verdict == "risque"

    def test_unknown_proof_type(self):
        claim = _make_claim(has_proof=True, proof_type="autre_chose")
        result = rule_justification(claim)
        assert result.verdict == "risque"


# ===================================================================
# Orchestration — analyze_claim
# ===================================================================

class TestAnalyzeClaim:
    def test_fully_compliant_claim(self):
        """Claim avec preuve solide, pas de terme générique, pas de label ni engagement."""
        claim = _make_claim(
            claim_text="Nos emballages contiennent 80% de carton recyclé post-consommation",
            scope="produit",
            has_proof=True,
            proof_type="certification_tierce",
        )
        results, verdict = analyze_claim(claim)
        assert len(results) == 6
        assert verdict == "conforme"

    def test_non_conforme_claim(self):
        """Claim générique + pas de preuve → non_conforme."""
        claim = _make_claim(
            claim_text="Produit naturel",
            has_proof=False,
        )
        results, verdict = analyze_claim(claim)
        assert verdict == "non_conforme"
        nc_criteria = [r.criterion for r in results if r.verdict == "non_conforme"]
        assert "specificity" in nc_criteria
        assert "justification" in nc_criteria

    def test_risque_claim_two_risks_no_nc(self):
        """Claim avec exactement 2 critères risque et 0 non_conforme → overall risque."""
        # specificity=risque (terme qualifié), justification=risque (rapport interne)
        # compensation=n/a, labels=n/a, proportionality=conforme (entreprise sans partial),
        # future_commitment=n/a
        claim = _make_claim(
            claim_text="Produit durable certifié ISO 14001",
            scope="entreprise",
            has_proof=True,
            proof_type="rapport_interne",
        )
        results, verdict = analyze_claim(claim)
        verdicts = {r.criterion: r.verdict for r in results}
        assert verdicts["specificity"] == "risque"
        assert verdicts["justification"] == "risque"
        assert verdict == "risque"

    def test_carbon_neutral_always_non_conforme(self):
        """Même avec des preuves solides, carbon neutral = non_conforme."""
        claim = _make_claim(
            claim_text="Entreprise neutre en carbone grâce à nos efforts",
            has_proof=True,
            proof_type="certification_tierce",
        )
        results, verdict = analyze_claim(claim)
        assert verdict == "non_conforme"
        comp = [r for r in results if r.criterion == "compensation"]
        assert comp[0].verdict == "non_conforme"

    def test_results_count_always_six(self):
        """Chaque claim produit exactement 6 résultats."""
        claim = _make_claim(claim_text="Test quelconque")
        results, _ = analyze_claim(claim)
        assert len(results) == 6
        criteria = {r.criterion for r in results}
        assert criteria == {
            "specificity", "compensation", "labels",
            "proportionality", "future_commitment", "justification",
        }
