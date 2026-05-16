"""Tests for the Flask health check API."""

from app import create_app


def test_health_endpoint_requires_api_key(monkeypatch):
    """Requests without an API key should return 401."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    response = client.get("/api/health/i-0123456789abcdef0")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_health_endpoint_rejects_invalid_api_key(monkeypatch):
    """Requests with invalid API keys should return 401."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    response = client.get(
        "/api/health/i-0123456789abcdef0",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_health_endpoint_accepts_valid_api_key(monkeypatch):
    """Requests with a valid API key should return health JSON."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    response = client.get(
        "/api/health/i-0123456789abcdef0",
        headers={"X-API-Key": "dev-key"},
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["instance_id"] == "i-0123456789abcdef0"
    assert body["state"] == "unknown"
    assert body["status_code"] == "unknown"
    assert body["health"] == "unknown"
    assert "timestamp" in body


def test_health_endpoint_uses_instance_id_from_url(monkeypatch):
    """The instance ID should be read from the URL path."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    response = client.get(
        "/api/health/i-test123456789",
        headers={"X-API-Key": "dev-key"},
    )

    assert response.status_code == 200
    assert response.get_json()["instance_id"] == "i-test123456789"


def test_health_endpoint_does_not_accept_post(monkeypatch):
    """The health endpoint should only accept GET requests."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/health/i-0123456789abcdef0",
        headers={"X-API-Key": "dev-key"},
    )

    assert response.status_code == 405
