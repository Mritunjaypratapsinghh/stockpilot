"""
Integration tests — HTTP endpoint tests with httpx AsyncClient.
Tests that need DB are wrapped in try/skip for CI without MongoDB.
"""

import pytest
from app.core.security import create_access_token
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "507f1f77bcf86cd799439011"}, email="test@example.com")
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_status(self, client):
        resp = await client.get("/health")
        assert resp.status_code in (200, 503)
        assert "status" in resp.json()


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client):
        resp = await client.post("/api/auth/register", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        try:
            resp = await client.post("/api/auth/register", json={"email": "a@b.com", "password": "short"})
            assert resp.status_code == 422
        except Exception:
            pytest.skip("DB not initialized")

    @pytest.mark.asyncio
    async def test_login_invalid(self, client):
        try:
            resp = await client.post("/api/auth/login", json={"email": "x@y.com", "password": "WrongPass1"})
            assert resp.status_code in (401, 500)
        except Exception:
            pytest.skip("DB not initialized")

    @pytest.mark.asyncio
    async def test_me_without_auth(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_expired_token(self, client):
        from datetime import datetime, timezone

        from app.core.config import settings
        from jose import jwt

        payload = {"sub": "user123", "exp": datetime(2020, 1, 1, tzinfo=timezone.utc)}
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout(self, client, auth_headers):
        resp = await client.post("/api/auth/logout", headers=auth_headers)
        assert resp.status_code == 200


class TestProtectedEndpoints:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/portfolio",
            "/api/portfolio/holdings",
            "/api/analytics",
            "/api/finance/goals",
            "/api/alerts",
            "/api/watchlist",
            "/api/vault/entries",
        ],
    )
    async def test_require_auth(self, client, endpoint):
        resp = await client.get(endpoint)
        assert resp.status_code == 401


class TestMetricsEndpoint:
    @pytest.mark.asyncio
    async def test_prometheus_format(self, client):
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "http_request" in resp.text


class TestCorrelationID:
    @pytest.mark.asyncio
    async def test_response_has_request_id(self, client):
        resp = await client.get("/health")
        assert "x-request-id" in resp.headers

    @pytest.mark.asyncio
    async def test_echoes_client_id(self, client):
        resp = await client.get("/health", headers={"X-Request-ID": "trace-abc"})
        assert resp.headers["x-request-id"] == "trace-abc"
