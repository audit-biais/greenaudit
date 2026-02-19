"""Tests d'intégration — endpoints audits + analyze."""

from __future__ import annotations

from httpx import AsyncClient


class TestAuditsCRUD:
    async def test_create_audit(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/audits", json={
            "company_name": "Acme Corp",
            "sector": "e-commerce",
            "website_url": "https://acme.com",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["company_name"] == "Acme Corp"
        assert data["status"] == "draft"
        assert data["total_claims"] == 0

    async def test_list_audits(self, client: AsyncClient, auth_headers, audit):
        resp = await client.get("/api/audits", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["company_name"] == "Entreprise Test"

    async def test_get_audit_detail(self, client: AsyncClient, auth_headers, audit):
        resp = await client.get(f"/api/audits/{audit.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(audit.id)
        assert "claims" in data

    async def test_get_audit_not_found(self, client: AsyncClient, auth_headers):
        resp = await client.get(
            "/api/audits/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_delete_draft_audit(self, client: AsyncClient, auth_headers, audit):
        resp = await client.delete(f"/api/audits/{audit.id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/audits")
        assert resp.status_code == 403


class TestAnalyze:
    async def test_analyze_no_claims(self, client: AsyncClient, auth_headers, audit):
        resp = await client.post(
            f"/api/audits/{audit.id}/analyze", headers=auth_headers
        )
        assert resp.status_code == 400
        assert "aucune claim" in resp.json()["detail"].lower()

    async def test_analyze_success(
        self, client: AsyncClient, auth_headers, audit, claim
    ):
        resp = await client.post(
            f"/api/audits/{audit.id}/analyze", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["total_claims"] == 1
        assert data["risk_level"] is not None
        assert data["global_score"] is not None
        # La claim "écologique" sans preuve doit être non_conforme
        assert data["non_conforming_claims"] == 1
        assert len(data["claims"]) == 1
        claim_data = data["claims"][0]
        assert claim_data["overall_verdict"] == "non_conforme"
        assert len(claim_data["results"]) == 6

    async def test_analyze_results_endpoint(
        self, client: AsyncClient, auth_headers, audit, claim
    ):
        # D'abord analyser
        await client.post(f"/api/audits/{audit.id}/analyze", headers=auth_headers)
        # Puis récupérer les résultats
        resp = await client.get(
            f"/api/audits/{audit.id}/results", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["claims"]) == 1

    async def test_results_before_analysis(
        self, client: AsyncClient, auth_headers, audit
    ):
        resp = await client.get(
            f"/api/audits/{audit.id}/results", headers=auth_headers
        )
        assert resp.status_code == 400

    async def test_reanalyze_replaces_results(
        self, client: AsyncClient, auth_headers, audit, claim
    ):
        # Première analyse
        resp1 = await client.post(
            f"/api/audits/{audit.id}/analyze", headers=auth_headers
        )
        assert resp1.status_code == 200
        # Deuxième analyse (re-analyse)
        resp2 = await client.post(
            f"/api/audits/{audit.id}/analyze", headers=auth_headers
        )
        assert resp2.status_code == 200
        # Doit toujours avoir 6 résultats par claim, pas 12
        assert len(resp2.json()["claims"][0]["results"]) == 6

    async def test_delete_completed_audit_rejected(
        self, client: AsyncClient, auth_headers, audit, claim
    ):
        await client.post(f"/api/audits/{audit.id}/analyze", headers=auth_headers)
        resp = await client.delete(f"/api/audits/{audit.id}", headers=auth_headers)
        assert resp.status_code == 400
