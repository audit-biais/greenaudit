"""
Tests unitaires pour filter_false_positives() dans monitoring_service.py.

Lancer avec : pytest tests/test_filter_false_positives.py -v
"""

from __future__ import annotations

from app.services.monitoring_service import filter_false_positives


# ── Cas à filtrer (descriptions factuelles industrielles sans bénéfice) ──────

def test_creation_reservoirs_biocarburants_est_filtre() -> None:
    """Cas exact rapporté sur Raffinerie du Midi."""
    result = filter_false_positives(["création de réservoirs de biocarburants"])
    assert result == []


def test_construction_usine_est_filtre() -> None:
    result = filter_false_positives(["construction d'une nouvelle usine"])
    assert result == []


def test_installation_panneaux_sans_benefice_est_filtre() -> None:
    result = filter_false_positives(["installation de panneaux solaires"])
    assert result == []


# ── Cas à garder (bénéfice environnemental présent) ──────────────────────────

def test_creation_reservoirs_avec_reduire_est_garde() -> None:
    """Même structure mais avec bénéfice explicite → garder."""
    claims = ["création de réservoirs de biocarburants pour réduire nos émissions"]
    result = filter_false_positives(claims)
    assert result == claims


def test_panneaux_solaires_avec_benefice_chiffre_est_garde() -> None:
    result = filter_false_positives(["nos panneaux solaires réduisent nos émissions de 30%"])
    assert result == ["nos panneaux solaires réduisent nos émissions de 30%"]


def test_usine_ecoresponsable_est_garde() -> None:
    """Usine mentionnée mais l'allégation porte sur un bénéfice → garder."""
    result = filter_false_positives(["notre usine est écoresponsable"])
    # Pas de verbe d'action industrielle en début → pas filtré
    assert result == ["notre usine est écoresponsable"]


# ── Cas mixtes — liste avec vrais et faux positifs ───────────────────────────

def test_liste_mixte_filtre_correctement() -> None:
    claims = [
        "création de réservoirs de biocarburants",          # filtré
        "nos emballages sont recyclés à 40%",               # gardé
        "installation de panneaux solaires",                 # filtré
        "réduire notre empreinte écologique",               # gardé (pas de verbe d'action + objet technique)
    ]
    result = filter_false_positives(claims)
    assert "création de réservoirs de biocarburants" not in result
    assert "installation de panneaux solaires" not in result
    assert "nos emballages sont recyclés à 40%" in result
    assert "réduire notre empreinte écologique" in result


# ── Cas limites ───────────────────────────────────────────────────────────────

def test_liste_vide_retourne_vide() -> None:
    assert filter_false_positives([]) == []


def test_claim_sans_objet_technique_est_garde() -> None:
    """Verbe d'action mais sans objet technique → pas filtré."""
    result = filter_false_positives(["création d'un programme de réduction carbone"])
    # "programme" n'est pas dans _TECHNICAL_OBJECT_TERMS → gardé
    assert result == ["création d'un programme de réduction carbone"]
