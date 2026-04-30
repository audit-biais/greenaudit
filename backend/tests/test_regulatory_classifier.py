"""
Tests unitaires pour le classificateur de régime juridique EmpCo.

Couvre les 7 branches de classify_claim_regime() + cas limites.
Ces tests sont purement synchrones côté logique — pas d'API externe.

Lancer avec : pytest tests/test_regulatory_classifier.py -v
"""

from __future__ import annotations

import pytest

from app.services.regulatory_classifier import classify_claim_regime


# Métadonnées neutres par défaut (aucun flag activé)
_BASE_META = {
    "has_label": False,
    "label_is_certified": None,
    "scope": "produit",
    "is_future_commitment": False,
    "has_proof": False,
    "proof_type": None,
}


def _meta(**kwargs) -> dict:
    """Crée des métadonnées en surchargeant les valeurs par défaut."""
    return {**_BASE_META, **kwargs}


# ── Règle 1 : label auto-décerné → annexe_I_2bis / liste_noire ───────────────

async def test_label_auto_declared_is_liste_noire() -> None:
    result = await classify_claim_regime(
        "label EcoMarque (auto-décerné)",
        _meta(has_label=True, label_is_certified=False),
    )
    assert result["regulatory_basis"] == "annexe_I_2bis"
    assert result["regime"] == "liste_noire"


async def test_label_certified_does_not_trigger_rule1() -> None:
    """Un label certifié ne doit pas tomber sur la règle 1."""
    result = await classify_claim_regime(
        "certifié Ecolabel EU",
        _meta(has_label=True, label_is_certified=True),
    )
    # Peut tomber sur d'autres règles, mais pas annexe_I_2bis
    assert result["regulatory_basis"] != "annexe_I_2bis"


# ── Règle 2 : neutralité carbone par compensation → annexe_I_4quater ─────────

async def test_carbon_neutral_is_liste_noire() -> None:
    result = await classify_claim_regime(
        "neutre en carbone via compensation",
        _meta(),
    )
    assert result["regulatory_basis"] == "annexe_I_4quater"
    assert result["regime"] == "liste_noire"


async def test_carbon_neutral_with_no_compensation_exclusion() -> None:
    """'sans compensation' doit exclure la règle 2 et laisser passer vers les règles suivantes."""
    result = await classify_claim_regime(
        "neutre en carbone, sans compensation, grâce à des réductions réelles",
        _meta(),
    )
    assert result["regulatory_basis"] != "annexe_I_4quater"


# ── Règle 3 : terme générique sans qualification → annexe_I_4bis ─────────────

async def test_generic_term_no_qualification_is_liste_noire() -> None:
    # Teste aussi le pluriel "écologiques" (s? dans le word boundary)
    result = await classify_claim_regime(
        "nos produits écologiques pour la maison",
        _meta(),
    )
    assert result["regulatory_basis"] == "annexe_I_4bis"
    assert result["regime"] == "liste_noire"


async def test_generic_term_with_percentage_is_not_4bis() -> None:
    """Terme générique + qualification mesurable → pas annexe_I_4bis."""
    result = await classify_claim_regime(
        "30% de plastique recyclé certifié GRS",
        _meta(),
    )
    assert result["regulatory_basis"] != "annexe_I_4bis"
    assert result["regulatory_basis"] == "article_6_general"
    assert result["regime"] == "cas_par_cas"


# ── Règle 4 : entreprise + aspect partiel → annexe_I_4ter / liste_noire ──────

async def test_enterprise_scope_with_partial_mention_is_liste_noire() -> None:
    # Texte sans terme blacklisté pour isoler la règle 4ter (proportionnalité)
    # "déchets" est dans PARTIAL_SCOPE_PATTERNS
    result = await classify_claim_regime(
        "Notre entreprise améliore sa gestion des déchets",
        _meta(scope="entreprise"),
    )
    assert result["regulatory_basis"] == "annexe_I_4ter"
    assert result["regime"] == "liste_noire"


async def test_enterprise_durable_emballage_hits_4bis_before_4ter() -> None:
    # Cas de la spec : "Notre entreprise est durable" + emballage + scope=entreprise
    # "durable" est en blacklist sans qualification → règle 3 (4bis) gagne sur règle 4 (4ter)
    # C'est le comportement correct selon l'ordre de priorité
    result = await classify_claim_regime(
        "Notre entreprise est durable grâce à nos efforts sur l'emballage",
        _meta(scope="entreprise"),
    )
    assert result["regulatory_basis"] == "annexe_I_4bis"
    assert result["regime"] == "liste_noire"


async def test_enterprise_scope_no_partial_is_not_4ter() -> None:
    # Pas de mot dans PARTIAL_SCOPE_PATTERNS, qualification chiffrée → pas de règle 3
    # Doit tomber sur article_6_general
    result = await classify_claim_regime(
        "Notre entreprise a réduit son impact de 40% certifié Bureau Veritas",
        _meta(scope="entreprise"),
    )
    assert result["regulatory_basis"] != "annexe_I_4ter"


# ── Règle 5 : engagement futur → article_6_1d / cas_par_cas ─────────────────

async def test_future_commitment_is_cas_par_cas() -> None:
    result = await classify_claim_regime(
        "Nous serons neutres en carbone d'ici 2030",
        _meta(is_future_commitment=True),
    )
    assert result["regulatory_basis"] == "article_6_1d"
    assert result["regime"] == "cas_par_cas"


# ── Règle 6 : exigence légale présentée comme distinctive → annexe_I_10bis ───

async def test_legal_requirement_presented_as_distinctive() -> None:
    result = await classify_claim_regime(
        "Sans CFC — notre engagement pour la planète",
        _meta(),
    )
    assert result["regulatory_basis"] == "annexe_I_10bis"
    assert result["regime"] == "liste_noire"


async def test_without_bpa_is_10bis() -> None:
    result = await classify_claim_regime(
        "emballage sans BPA",
        _meta(),
    )
    assert result["regulatory_basis"] == "annexe_I_10bis"
    assert result["regime"] == "liste_noire"


# ── Règle 7 : défaut → article_6_general / cas_par_cas ───────────────────────

async def test_specific_qualified_claim_is_general() -> None:
    result = await classify_claim_regime(
        "30% de plastique recyclé certifié GRS dans nos bouteilles",
        _meta(has_proof=True, proof_type="certification_tierce"),
    )
    assert result["regulatory_basis"] == "article_6_general"
    assert result["regime"] == "cas_par_cas"


async def test_empty_text_defaults_to_general() -> None:
    result = await classify_claim_regime("", _meta())
    assert result["regulatory_basis"] == "article_6_general"
    assert result["regime"] == "cas_par_cas"


async def test_non_environmental_text_defaults_to_general() -> None:
    result = await classify_claim_regime(
        "livraison gratuite en 48h sur toute la France",
        _meta(),
    )
    assert result["regulatory_basis"] == "article_6_general"
    assert result["regime"] == "cas_par_cas"


# ── Priorité : règle 1 gagne sur règle 3 ─────────────────────────────────────

async def test_rule1_takes_priority_over_rule3() -> None:
    """Label auto-décerné + terme générique → c'est la règle 1 qui s'applique."""
    result = await classify_claim_regime(
        "label vert auto-certifié",
        _meta(has_label=True, label_is_certified=False),
    )
    assert result["regulatory_basis"] == "annexe_I_2bis"


# ── Priorité : engagement futur gagne sur proportionnalité (fix 2026-04-29) ──

async def test_future_commitment_wins_over_proportionality() -> None:
    """
    'produits phytosanitaires' matche PARTIAL_SCOPE_PATTERNS mais la phrase
    est un engagement futur explicite → article_6_1d, PAS annexe_I_4ter.
    """
    result = await classify_claim_regime(
        "nous nous engageons à atteindre une réduction des produits phytosanitaires de 25%",
        _meta(scope="entreprise"),
    )
    assert result["regulatory_basis"] == "article_6_1d"
    assert result["regime"] == "cas_par_cas"


async def test_viser_a_wins_over_proportionality() -> None:
    """Pattern 'nous visons à' → engagement futur même si critère eau présent."""
    result = await classify_claim_regime(
        "nous visons à rationnaliser notre consommation d'eau et d'énergie",
        _meta(scope="entreprise"),
    )
    assert result["regulatory_basis"] == "article_6_1d"
    assert result["regime"] == "cas_par_cas"


async def test_blacklist_wins_over_future_commitment() -> None:
    """Terme générique blacklisté + engagement futur → blacklist gagne (règle 3 avant règle 4)."""
    result = await classify_claim_regime(
        "nous nous engageons à devenir écologiques d'ici 2030",
        _meta(scope="entreprise"),
    )
    assert result["regulatory_basis"] == "annexe_I_4bis"
    assert result["regime"] == "liste_noire"


async def test_future_commitment_lexical_no_blacklist() -> None:
    """'nous visons à réduire notre empreinte' sans terme blacklisté → article_6_1d."""
    result = await classify_claim_regime(
        "nous visons à réduire notre empreinte",
        _meta(scope="entreprise"),
    )
    assert result["regulatory_basis"] == "article_6_1d"
    assert result["regime"] == "cas_par_cas"
