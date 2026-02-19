"""Tests d'intégration — endpoints auth."""

from __future__ import annotations

from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "new@greenaudit.fr",
            "password": "securepass123",
            "company_name": "Nouvelle Agence",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@greenaudit.fr"
        assert data["company_name"] == "Nouvelle Agence"
        assert "password_hash" not in data
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, partner):
        resp = await client.post("/api/auth/register", json={
            "email": "test@greenaudit.fr",  # même email que la fixture partner
            "password": "securepass123",
            "company_name": "Doublon",
        })
        assert resp.status_code == 409

    async def test_register_password_too_short(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "short@greenaudit.fr",
            "password": "short",
            "company_name": "Test",
        })
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "securepass123",
            "company_name": "Test",
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, partner):
        resp = await client.post("/api/auth/login", json={
            "email": "test@greenaudit.fr",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, partner):
        resp = await client.post("/api/auth/login", json={
            "email": "test@greenaudit.fr",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        resp = await client.post("/api/auth/login", json={
            "email": "unknown@greenaudit.fr",
            "password": "whatever123",
        })
        assert resp.status_code == 401


class TestMe:
    async def test_get_me(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@greenaudit.fr"

    async def test_get_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 403

    async def test_get_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401
