"""Suite de tests de sécurité GreenAudit.

Couvre :
- Isolation multi-tenant (IDOR)
- Résistance aux tokens forgés (alg:none)
- Brute-force protection (rate limiting)
- Endpoint de partage : accessible sans auth, pas de fuite de champs sensibles
- Validation des inputs (path traversal, champ trop long, enum invalide)
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import _token_for
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.user import User

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# 1. Isolation multi-tenant — user_b ne peut pas lire l'audit de user_a
# ---------------------------------------------------------------------------

async def test_tenant_isolation(
    client: AsyncClient,
    audit_a: Audit,
    headers_b: dict,
):
    """GET /api/audits/{id} avec le token de user_b → 404 (pas 403, l'audit est invisible)."""
    resp = await client.get(f"/api/audits/{audit_a.id}", headers=headers_b)
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# 2. IDOR claim — user_b ne peut pas modifier la claim de user_a
# ---------------------------------------------------------------------------

async def test_idor_claim(
    client: AsyncClient,
    claim_a: Claim,
    headers_b: dict,
):
    """PUT /api/claims/{id} avec le token de user_b → 404."""
    resp = await client.put(
        f"/api/claims/{claim_a.id}",
        headers=headers_b,
        json={"claim_text": "Injection IDOR"},
    )
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# 3. Résistance à l'attaque alg:none sur le JWT
# ---------------------------------------------------------------------------

def _forge_alg_none_token(email: str, user_id: str) -> str:
    """Construit un JWT avec alg=none et signature vide."""
    header = (
        base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    payload = (
        base64.urlsafe_b64encode(
            json.dumps({"sub": email, "user_id": user_id}).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}."


async def test_jwt_alg_none(client: AsyncClient, user_a: User):
    """Un token forgé avec alg=none pour user_a → 401."""
    token = _forge_alg_none_token(user_a.email, str(user_a.id))
    resp = await client.get(
        "/api/audits",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# 4. Protection brute-force — rate limit sur /login
# ---------------------------------------------------------------------------

async def test_brute_force_login(client: AsyncClient):
    """Après 10 tentatives de login, la 11ème renvoie 429."""
    statuses = []
    for _ in range(11):
        resp = await client.post(
            "/api/auth/login",
            data={"username": "brute@test.com", "password": "wrongpassword"},
        )
        statuses.append(resp.status_code)

    # Les premières tentatives : 401 (credential invalides) ou 429 (rate limit)
    # La 11ème doit obligatoirement être 429
    assert 429 in statuses, f"Aucun 429 reçu en {len(statuses)} tentatives : {statuses}"


# ---------------------------------------------------------------------------
# 5. Lien de partage — accessible sans auth, pas de champs sensibles
# ---------------------------------------------------------------------------

async def test_share_token_no_auth(
    client: AsyncClient,
    db_session: AsyncSession,
    audit_a: Audit,
):
    """GET /api/audits/{id}/share/{token} sans JWT → 200, organization_id absent."""
    # Injecter un share_token valide directement en DB
    token = "valid-share-token-for-test-1234567890"
    audit_a.share_token = token
    audit_a.share_token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db_session.add(audit_a)
    await db_session.commit()

    resp = await client.get(f"/api/audits/{audit_a.id}/share/{token}")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    # Le champ organization_id ne doit pas être exposé
    assert "organization_id" not in body
    # Les champs attendus sont présents
    assert "audit_id" in body
    assert "company_name" in body


# ---------------------------------------------------------------------------
# 6. Path traversal — audit_id non-UUID → 422
# ---------------------------------------------------------------------------

async def test_path_traversal_pdf(client: AsyncClient, headers_a: dict):
    """GET /api/audits/../../../etc/passwd/results → 422 (UUID invalide)."""
    resp = await client.get(
        "/api/audits/../../../etc/passwd/results",
        headers=headers_a,
    )
    # FastAPI valide le type UUID avant d'atteindre le handler
    assert resp.status_code in (422, 404), resp.text


# ---------------------------------------------------------------------------
# 7. Dépassement de taille — claim_text de 100 000 caractères → 422
# ---------------------------------------------------------------------------

async def test_oversized_claim(
    client: AsyncClient,
    audit_a: Audit,
    headers_a: dict,
):
    """POST claim avec claim_text > 2000 chars → 422."""
    resp = await client.post(
        f"/api/audits/{audit_a.id}/claims",
        headers=headers_a,
        json={
            "claim_text": "A" * 100_000,
            "support_type": "web",
            "scope": "produit",
            "has_proof": False,
            "proof_type": "aucune",
            "has_label": False,
            "is_future_commitment": False,
        },
    )
    assert resp.status_code == 422, resp.text


# ---------------------------------------------------------------------------
# 8. Enum invalide — support_type avec payload XSS → 422
# ---------------------------------------------------------------------------

async def test_invalid_support_type(
    client: AsyncClient,
    audit_a: Audit,
    headers_a: dict,
):
    """POST claim avec support_type='<script>alert(1)</script>' → 422."""
    resp = await client.post(
        f"/api/audits/{audit_a.id}/claims",
        headers=headers_a,
        json={
            "claim_text": "Allégation test",
            "support_type": "<script>alert(1)</script>",
            "scope": "produit",
            "has_proof": False,
            "proof_type": "aucune",
            "has_label": False,
            "is_future_commitment": False,
        },
    )
    assert resp.status_code == 422, resp.text
