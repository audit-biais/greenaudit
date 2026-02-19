"""Tests d'intégration — endpoints claims."""

from __future__ import annotations

from httpx import AsyncClient


class TestClaimsCRUD:
    async def test_create_claim(self, client: AsyncClient, auth_headers, audit):
        resp = await client.post(f"/api/audits/{audit.id}/claims", json={
            "claim_text": "Emballage 100% recyclable",
            "support_type": "packaging",
            "scope": "produit",
            "has_proof": True,
            "proof_type": "certification_tierce",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["claim_text"] == "Emballage 100% recyclable"
        assert data["audit_id"] == str(audit.id)
        assert data["has_proof"] is True

    async def test_list_claims(self, client: AsyncClient, auth_headers, audit, claim):
        resp = await client.get(
            f"/api/audits/{audit.id}/claims", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["claim_text"] == claim.claim_text

    async def test_update_claim(self, client: AsyncClient, auth_headers, claim):
        resp = await client.put(f"/api/claims/{claim.id}", json={
            "claim_text": "Texte modifié",
            "has_proof": True,
            "proof_type": "certification_tierce",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["claim_text"] == "Texte modifié"
        assert data["has_proof"] is True
        assert data["proof_type"] == "certification_tierce"

    async def test_delete_claim(self, client: AsyncClient, auth_headers, claim):
        resp = await client.delete(f"/api/claims/{claim.id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_create_claim_no_auth(self, client: AsyncClient, audit):
        resp = await client.post(f"/api/audits/{audit.id}/claims", json={
            "claim_text": "Test",
            "support_type": "web",
            "scope": "produit",
        })
        assert resp.status_code == 403

    async def test_create_claim_with_label(
        self, client: AsyncClient, auth_headers, audit
    ):
        resp = await client.post(f"/api/audits/{audit.id}/claims", json={
            "claim_text": "Produit labellisé EU Ecolabel",
            "support_type": "packaging",
            "scope": "produit",
            "has_label": True,
            "label_name": "EU Ecolabel",
            "label_is_certified": True,
            "has_proof": True,
            "proof_type": "certification_tierce",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["has_label"] is True
        assert data["label_name"] == "EU Ecolabel"
        assert data["label_is_certified"] is True

    async def test_create_claim_future_commitment(
        self, client: AsyncClient, auth_headers, audit
    ):
        resp = await client.post(f"/api/audits/{audit.id}/claims", json={
            "claim_text": "Nous visons 100% d'énergie renouvelable",
            "support_type": "web",
            "scope": "entreprise",
            "is_future_commitment": True,
            "target_date": "2028-12-31",
            "has_independent_verification": True,
            "has_proof": True,
            "proof_type": "certification_tierce",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_future_commitment"] is True
        assert data["target_date"] == "2028-12-31"
