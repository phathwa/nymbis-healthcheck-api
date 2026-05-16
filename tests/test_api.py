"""Tests for the Flask API."""

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
    """Requests with a valid API key should be accepted."""
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
