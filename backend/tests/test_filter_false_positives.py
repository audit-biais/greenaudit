"""
Tests unitaires pour filter_false_positives() dans monitoring_service.py.

Lancer avec : pytest tests/test_filter_false_positives.py -v
"""

from __future__ import annotations

from app.services.monitoring_service import filter_false_positives


# ── Bloc 1 — Nominalisations industrielles ────────────────────────────────────

def test_creation_reservoirs_biocarburants_est_filtre() -> None:
    result = filter_false_positives(["création de réservoirs de biocarburants"])
    assert result == []


def test_construction_usine_est_filtre() -> None:
    result = filter_false_positives(["construction d'une nouvelle usine"])
    assert result == []


def test_installation_panneaux_sans_benefice_est_filtre() -> None:
    result = filter_false_positives(["installation de panneaux solaires"])
    assert result == []


def test_creation_reservoirs_avec_reduire_est_garde() -> None:
    claims = ["création de réservoirs de biocarburants pour réduire nos émissions"]
    assert filter_false_positives(claims) == claims


def test_usine_ecoresponsable_est_garde() -> None:
    claims = ["notre usine est écoresponsable"]
    assert filter_false_positives(claims) == claims


# ── Bloc 2 — Mécanismes physiques impersonnels ────────────────────────────────

def test_coton_consomme_moins_eau_est_filtre() -> None:
    result = filter_false_positives(
        ['le coton durable consomme moins d\'eau que le coton "normal"'],
        company_name="JD Sports",
    )
    assert result == []


def test_polyester_pollution_reduite_est_filtre() -> None:
    result = filter_false_positives([
        "la pollution liée à la production de polyester est réduite, "
        "car en le recyclant, nul besoin de le produire"
    ])
    assert result == []


def test_il_limite_production_polyester_est_filtre() -> None:
    result = filter_false_positives(
        ["Il limite la production inutile de polyester"],
        company_name="JD Sports",
    )
    assert result == []


def test_chez_jd_coton_durable_est_garde() -> None:
    claims = ["chez JD tu trouveras des produits faits de coton durable"]
    assert filter_false_positives(claims, company_name="JD Sports") == claims


def test_nous_utilisons_coton_durable_est_garde() -> None:
    claims = ["nous utilisons du coton durable"]
    assert filter_false_positives(claims, company_name="JD Sports") == claims


# ── Bloc 3 — Collectifs génériques ───────────────────────────────────────────

def test_elles_deviennent_ecoresponsables_est_filtre() -> None:
    result = filter_false_positives(
        ["elles deviennent toutes de plus en plus écoresponsables"],
        company_name="JD Sports",
    )
    assert result == []


def test_les_marques_font_des_efforts_est_filtre() -> None:
    result = filter_false_positives(
        ["les marques font des efforts pour réduire leur impact"],
        company_name="JD Sports",
    )
    assert result == []


# ── Bloc 4 — Navigation UI ────────────────────────────────────────────────────

def test_nhesite_pas_orienter_recherches_est_filtre() -> None:
    result = filter_false_positives([
        "N'hésite pas à orienter tes recherches sur notre site "
        "en tapant dans la barre de recherches « coton durable »"
    ])
    assert result == []


def test_decouvre_produits_ecoresponsables_chez_jd_est_garde() -> None:
    """Contient navigation ET allégation avec attribution → garder."""
    claims = ["découvre les produits écoresponsables chez JD"]
    # La phrase contient "JD" → attribution détectée → pas de filtrage bloc 3/4
    assert filter_false_positives(claims, company_name="JD Sports") == claims


# ── Cas mixtes ────────────────────────────────────────────────────────────────

def test_liste_mixte_filtre_correctement() -> None:
    claims = [
        "création de réservoirs de biocarburants",
        "nos emballages sont recyclés à 40%",
        "le coton durable consomme moins d'eau que le coton normal",
        "elles deviennent toutes de plus en plus écoresponsables",
        "N'hésite pas à orienter tes recherches",
        "Deviens écoresponsable avec JD",
    ]
    result = filter_false_positives(claims, company_name="JD Sports")
    assert "création de réservoirs de biocarburants" not in result
    assert "le coton durable consomme moins d'eau que le coton normal" not in result
    assert "elles deviennent toutes de plus en plus écoresponsables" not in result
    assert "N'hésite pas à orienter tes recherches" not in result
    assert "nos emballages sont recyclés à 40%" in result
    assert "Deviens écoresponsable avec JD" in result


def test_liste_vide_retourne_vide() -> None:
    assert filter_false_positives([]) == []


def test_claim_sans_objet_technique_est_garde() -> None:
    claims = ["création d'un programme de réduction carbone"]
    assert filter_false_positives(claims) == claims
