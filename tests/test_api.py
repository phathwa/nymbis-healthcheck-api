"""Tests for the Flask health check API."""

from unittest.mock import patch

from botocore.exceptions import ClientError

from app import create_app
from exceptions import InstanceNotFoundError


def test_health_endpoint_requires_api_key(monkeypatch):
    """Requests without an API key should return 401."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    with patch("app.log_api_request") as mock_log_api_request:
        response = client.get("/api/health/i-0123456789abcdef0")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}
    mock_log_api_request.assert_called_once()


def test_health_endpoint_rejects_invalid_api_key(monkeypatch):
    """Requests with invalid API keys should return 401."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    with patch("app.log_api_request") as mock_log_api_request:
        response = client.get(
            "/api/health/i-0123456789abcdef0",
            headers={"X-API-Key": "wrong-key"},
        )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}
    mock_log_api_request.assert_called_once()


def test_health_endpoint_accepts_valid_api_key(monkeypatch):
    """Requests with a valid API key should return health JSON."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    with patch("app.log_api_request") as mock_log_api_request:
        with patch("app.get_instance_health") as mock_get_instance_health:
            mock_get_instance_health.return_value = {
                "state": "running",
                "status_code": "ok",
                "health": "healthy",
            }

            response = client.get(
                "/api/health/i-0123456789abcdef0",
                headers={"X-API-Key": "dev-key"},
            )

    assert response.status_code == 200

    body = response.get_json()

    assert body["instance_id"] == "i-0123456789abcdef0"
    assert body["state"] == "running"
    assert body["status_code"] == "ok"
    assert body["health"] == "healthy"
    assert "timestamp" in body
    mock_log_api_request.assert_called_once()


def test_health_endpoint_uses_instance_id_from_url(monkeypatch):
    """The instance ID should be read from the URL path."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    with patch("app.log_api_request"):
        with patch("app.get_instance_health") as mock_get_instance_health:
            mock_get_instance_health.return_value = {
                "state": "running",
                "status_code": "ok",
                "health": "healthy",
            }

            response = client.get(
                "/api/health/i-test123456789",
                headers={"X-API-Key": "dev-key"},
            )

    assert response.status_code == 200
    assert response.get_json()["instance_id"] == "i-test123456789"
    mock_get_instance_health.assert_called_once_with("i-test123456789")


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


def test_health_endpoint_returns_404_for_unknown_instance(monkeypatch):
    """Unknown EC2 instances should return 404."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    with patch("app.log_api_request") as mock_log_api_request:
        with patch("app.get_instance_health") as mock_get_instance_health:
            mock_get_instance_health.side_effect = InstanceNotFoundError(
                "Instance not found"
            )

            response = client.get(
                "/api/health/i-invalid",
                headers={"X-API-Key": "dev-key"},
            )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Instance not found"}
    mock_log_api_request.assert_called_once()


def test_health_endpoint_returns_500_when_aws_fails(monkeypatch):
    """Unexpected AWS API failures should return 500."""
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")

    app = create_app()
    client = app.test_client()

    aws_error = ClientError(
        {
            "Error": {
                "Code": "RequestLimitExceeded",
                "Message": "Rate exceeded",
            }
        },
        "DescribeInstances",
    )

    with patch("app.log_api_request") as mock_log_api_request:
        with patch("app.get_instance_health") as mock_get_instance_health:
            mock_get_instance_health.side_effect = aws_error

            response = client.get(
                "/api/health/i-0123456789abcdef0",
                headers={"X-API-Key": "dev-key"},
            )

    assert response.status_code == 500
    assert response.get_json() == {"error": "AWS API failed"}
    mock_log_api_request.assert_called_once()
