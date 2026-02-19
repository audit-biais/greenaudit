"""Tests unitaires du module de scoring."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.scoring import calculate_global_score, compute_verdict_counts


# ===================================================================
# calculate_global_score
# ===================================================================

class TestCalculateGlobalScore:
    def test_all_conforming(self):
        score, level = calculate_global_score(conforming=5, at_risk=0, non_conforming=0)
        assert score == Decimal("100.00")
        assert level == "faible"

    def test_all_non_conforming(self):
        score, level = calculate_global_score(conforming=0, at_risk=0, non_conforming=5)
        assert score == Decimal("0.00")
        assert level == "critique"

    def test_all_at_risk(self):
        score, level = calculate_global_score(conforming=0, at_risk=4, non_conforming=0)
        assert score == Decimal("50.00")
        assert level == "eleve"

    def test_mixed_faible(self):
        # 8 conformes + 2 risque = (800 + 100) / 10 = 90
        score, level = calculate_global_score(conforming=8, at_risk=2, non_conforming=0)
        assert score == Decimal("90.00")
        assert level == "faible"

    def test_mixed_modere(self):
        # 5 conformes + 2 risque + 3 nc = (500 + 100) / 10 = 60
        score, level = calculate_global_score(conforming=5, at_risk=2, non_conforming=3)
        assert score == Decimal("60.00")
        assert level == "modere"

    def test_mixed_critique(self):
        # 3 conformes + 1 risque + 6 nc = (300 + 50) / 10 = 35
        score, level = calculate_global_score(conforming=3, at_risk=1, non_conforming=6)
        assert score == Decimal("35.00")
        assert level == "critique"

    def test_zero_claims(self):
        score, level = calculate_global_score(conforming=0, at_risk=0, non_conforming=0)
        assert score == Decimal("0")
        assert level == "critique"

    def test_boundary_80(self):
        # 4 conformes + 0 risque + 1 nc = 400 / 5 = 80
        score, level = calculate_global_score(conforming=4, at_risk=0, non_conforming=1)
        assert score == Decimal("80.00")
        assert level == "faible"

    def test_boundary_60(self):
        # 3 conformes + 0 risque + 2 nc = 300 / 5 = 60
        score, level = calculate_global_score(conforming=3, at_risk=0, non_conforming=2)
        assert score == Decimal("60.00")
        assert level == "modere"

    def test_boundary_40(self):
        # 2 conformes + 0 risque + 3 nc = 200 / 5 = 40
        score, level = calculate_global_score(conforming=2, at_risk=0, non_conforming=3)
        assert score == Decimal("40.00")
        assert level == "eleve"

    def test_rounding(self):
        # 1 conforme + 1 risque + 1 nc = (100 + 50) / 3 = 50.00
        score, level = calculate_global_score(conforming=1, at_risk=1, non_conforming=1)
        assert score == Decimal("50.00")
        assert level == "eleve"


# ===================================================================
# compute_verdict_counts
# ===================================================================

class TestComputeVerdictCounts:
    def test_empty(self):
        counts = compute_verdict_counts([])
        assert counts == {"conforme": 0, "risque": 0, "non_conforme": 0}

    def test_mixed(self):
        verdicts = ["conforme", "non_conforme", "risque", "conforme", "non_conforme"]
        counts = compute_verdict_counts(verdicts)
        assert counts == {"conforme": 2, "risque": 1, "non_conforme": 2}

    def test_all_same(self):
        counts = compute_verdict_counts(["conforme"] * 4)
        assert counts == {"conforme": 4, "risque": 0, "non_conforme": 0}

    def test_ignores_unknown(self):
        counts = compute_verdict_counts(["conforme", "unknown", "risque"])
        assert counts == {"conforme": 1, "risque": 1, "non_conforme": 0}
