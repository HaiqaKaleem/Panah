"""Tests for authentication, WebSocket, and middleware features."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Authentication Tests ──────────────────────────────────────────────

class TestAuthRegister:
    def test_register_success(self):
        r = client.post("/api/v1/auth/register", json={
            "email": "test@panagah.org",
            "password": "TestPass123",
            "full_name": "Test Engineer",
            "role": "engineer",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "test@panagah.org"
        assert data["full_name"] == "Test Engineer"
        assert data["role"] == "engineer"
        assert data["is_active"] is True
        assert "id" in data

    def test_register_duplicate_email(self):
        client.post("/api/v1/auth/register", json={
            "email": "dup@panagah.org",
            "password": "TestPass123",
            "full_name": "Dup User",
            "role": "engineer",
        })
        r = client.post("/api/v1/auth/register", json={
            "email": "dup@panagah.org",
            "password": "TestPass456",
            "full_name": "Dup User 2",
            "role": "engineer",
        })
        assert r.status_code == 409

    def test_register_invalid_email(self):
        r = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "TestPass123",
            "full_name": "Bad Email",
            "role": "engineer",
        })
        assert r.status_code == 422

    def test_register_short_password(self):
        r = client.post("/api/v1/auth/register", json={
            "email": "short@panagah.org",
            "password": "ab",
            "full_name": "Short Pass",
            "role": "engineer",
        })
        assert r.status_code == 422

    def test_register_invalid_role(self):
        r = client.post("/api/v1/auth/register", json={
            "email": "badrole@panagah.org",
            "password": "TestPass123",
            "full_name": "Bad Role",
            "role": "superadmin",
        })
        assert r.status_code == 422


class TestAuthLogin:
    def test_login_success(self):
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": "login@panagah.org",
            "password": "LoginPass123",
            "full_name": "Login User",
            "role": "engineer",
        })
        # Login
        r = client.post("/api/v1/auth/login", json={
            "email": "login@panagah.org",
            "password": "LoginPass123",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert data["user"]["email"] == "login@panagah.org"

    def test_login_wrong_password(self):
        client.post("/api/v1/auth/register", json={
            "email": "wrong@panagah.org",
            "password": "CorrectPass123",
            "full_name": "Wrong User",
            "role": "engineer",
        })
        r = client.post("/api/v1/auth/login", json={
            "email": "wrong@panagah.org",
            "password": "WrongPassword",
        })
        assert r.status_code == 401

    def test_login_nonexistent_user(self):
        r = client.post("/api/v1/auth/login", json={
            "email": "nobody@panagah.org",
            "password": "AnyPass123",
        })
        assert r.status_code == 401


class TestAuthProfile:
    def test_get_me_authenticated(self):
        # Register + login
        client.post("/api/v1/auth/register", json={
            "email": "me@panagah.org",
            "password": "MePass12345",
            "full_name": "Me User",
            "role": "engineer",
        })
        login = client.post("/api/v1/auth/login", json={
            "email": "me@panagah.org",
            "password": "MePass12345",
        })
        token = login.json()["access_token"]

        # Get profile
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "me@panagah.org"

    def test_get_me_unauthenticated(self):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_get_me_invalid_token(self):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert r.status_code == 401


class TestAuthTokenRefresh:
    def test_refresh_token(self):
        client.post("/api/v1/auth/register", json={
            "email": "refresh@panagah.org",
            "password": "RefreshPass123",
            "full_name": "Refresh User",
            "role": "engineer",
        })
        login = client.post("/api/v1/auth/login", json={
            "email": "refresh@panagah.org",
            "password": "RefreshPass123",
        })
        token = login.json()["access_token"]

        r = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert "access_token" in r.json()


class TestAdminEndpoints:
    def _get_admin_token(self):
        """Login as admin (seeded user)."""
        r = client.post("/api/v1/auth/login", json={
            "email": "admin@panagah.org",
            "password": "Admin@12345",
        })
        return r.json()["access_token"]

    def test_list_users_admin(self):
        token = self._get_admin_token()
        r = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1  # At least admin

    def test_list_users_non_admin(self):
        client.post("/api/v1/auth/register", json={
            "email": "nonadmin@panagah.org",
            "password": "NonAdmin123",
            "full_name": "Non Admin",
            "role": "engineer",
        })
        login = client.post("/api/v1/auth/login", json={
            "email": "nonadmin@panagah.org",
            "password": "NonAdmin123",
        })
        token = login.json()["access_token"]

        r = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403


# ── System Endpoint Tests ─────────────────────────────────────────────

class TestSystemEndpoints:
    def test_health_check(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data

    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Panagah API"
        assert data["version"] == "1.0.0"
        assert "docs" in data
        assert "websocket" in data

    def test_metrics(self):
        r = client.get("/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "uptime_seconds" in data
        assert "python_version" in data


# ── Middleware Tests ───────────────────────────────────────────────────

class TestMiddleware:
    def test_request_id_header(self):
        r = client.get("/health")
        assert "X-Request-ID" in r.headers

    def test_response_time_header(self):
        r = client.get("/health")
        assert "X-Response-Time" in r.headers

    def test_custom_request_id(self):
        r = client.get("/health", headers={"X-Request-ID": "custom-id-123"})
        assert r.headers["X-Request-ID"] == "custom-id-123"


# ── Error Handler Tests ───────────────────────────────────────────────

class TestErrorHandlers:
    def test_404_format(self):
        r = client.get("/api/v1/projects/999999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert "error" in data

    def test_422_format(self):
        r = client.post("/api/v1/auth/register", json={"bad": "data"})
        assert r.status_code == 422
        data = r.json()
        assert "details" in data
        assert isinstance(data["details"], list)


# ── OpenAPI Tests ─────────────────────────────────────────────────────

class TestOpenAPI:
    def test_openapi_schema_loads(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert "info" in schema
        assert schema["info"]["version"] == "1.0.0"

    def test_docs_accessible(self):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_redoc_accessible(self):
        r = client.get("/redoc")
        assert r.status_code == 200

    def test_auth_endpoints_in_schema(self):
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/me" in paths
        assert "/api/v1/auth/refresh" in paths
