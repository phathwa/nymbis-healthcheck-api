"""Tests for the Flask health check API."""

from unittest.mock import patch

from botocore.exceptions import BotoCoreError, ClientError

from app import create_app
from exceptions import InstanceNotFoundError


def make_client(monkeypatch):
    """Create a test client with a configured API key.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        FlaskClient: Flask test client.
    """
    monkeypatch.setenv("VALID_API_KEYS", "dev-key")
    app = create_app()

    return app.test_client()


def test_health_endpoint_requires_api_key(monkeypatch):
    """Requests without an API key should return 401."""
    client = make_client(monkeypatch)

    with patch("app.log_api_request") as mock_log_api_request:
        response = client.get("/api/health/i-0123456789abcdef0")

    body = response.get_json()
    log_kwargs = mock_log_api_request.call_args.kwargs

    assert response.status_code == 401
    assert body["error"] == "Unauthorized"
    assert "request_id" in body

    assert log_kwargs["method"] == "GET"
    assert log_kwargs["path"] == "/api/health/i-0123456789abcdef0"
    assert log_kwargs["api_key"] is None
    assert log_kwargs["status_code"] == 401
    assert log_kwargs["error"] == "Unauthorized"
    assert log_kwargs["request_id"] == body["request_id"]


def test_health_endpoint_rejects_invalid_api_key(monkeypatch):
    """Requests with invalid API keys should return 401."""
    client = make_client(monkeypatch)

    with patch("app.log_api_request") as mock_log_api_request:
        response = client.get(
            "/api/health/i-0123456789abcdef0",
            headers={"X-API-Key": "wrong-key"},
        )

    body = response.get_json()
    log_kwargs = mock_log_api_request.call_args.kwargs

    assert response.status_code == 401
    assert body["error"] == "Unauthorized"
    assert "request_id" in body

    assert log_kwargs["method"] == "GET"
    assert log_kwargs["path"] == "/api/health/i-0123456789abcdef0"
    assert log_kwargs["api_key"] == "wrong-key"
    assert log_kwargs["status_code"] == 401
    assert log_kwargs["error"] == "Unauthorized"
    assert log_kwargs["request_id"] == body["request_id"]


def test_health_endpoint_accepts_valid_api_key(monkeypatch):
    """Requests with a valid API key should return health JSON."""
    client = make_client(monkeypatch)

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

    body = response.get_json()
    log_kwargs = mock_log_api_request.call_args.kwargs

    assert response.status_code == 200
    assert body["instance_id"] == "i-0123456789abcdef0"
    assert body["state"] == "running"
    assert body["status_code"] == "ok"
    assert body["health"] == "healthy"
    assert "timestamp" in body
    assert "request_id" in body

    mock_get_instance_health.assert_called_once_with("i-0123456789abcdef0")

    assert log_kwargs["method"] == "GET"
    assert log_kwargs["path"] == "/api/health/i-0123456789abcdef0"
    assert log_kwargs["api_key"] == "dev-key"
    assert log_kwargs["status_code"] == 200
    assert log_kwargs["result"] == "healthy"
    assert log_kwargs["request_id"] == body["request_id"]


def test_health_endpoint_uses_instance_id_from_url(monkeypatch):
    """The instance ID should be read from the URL path."""
    client = make_client(monkeypatch)

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
    client = make_client(monkeypatch)

    response = client.post(
        "/api/health/i-0123456789abcdef0",
        headers={"X-API-Key": "dev-key"},
    )

    assert response.status_code == 405


def test_health_endpoint_returns_404_for_unknown_instance(monkeypatch):
    """Unknown EC2 instances should return 404."""
    client = make_client(monkeypatch)

    with patch("app.log_api_request") as mock_log_api_request:
        with patch("app.get_instance_health") as mock_get_instance_health:
            mock_get_instance_health.side_effect = InstanceNotFoundError(
                "Instance not found"
            )

            response = client.get(
                "/api/health/i-invalid",
                headers={"X-API-Key": "dev-key"},
            )

    body = response.get_json()
    log_kwargs = mock_log_api_request.call_args.kwargs

    assert response.status_code == 404
    assert body["error"] == "Instance not found"
    assert "request_id" in body

    assert log_kwargs["method"] == "GET"
    assert log_kwargs["path"] == "/api/health/i-invalid"
    assert log_kwargs["api_key"] == "dev-key"
    assert log_kwargs["status_code"] == 404
    assert log_kwargs["error"] == "Instance not found"
    assert log_kwargs["request_id"] == body["request_id"]


def test_health_endpoint_returns_500_when_client_error_occurs(
    monkeypatch,
):
    """Unexpected AWS client errors should return 500."""
    client = make_client(monkeypatch)

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

    body = response.get_json()
    log_kwargs = mock_log_api_request.call_args.kwargs

    assert response.status_code == 500
    assert body["error"] == "AWS API failed"
    assert "request_id" in body

    assert log_kwargs["method"] == "GET"
    assert log_kwargs["path"] == "/api/health/i-0123456789abcdef0"
    assert log_kwargs["api_key"] == "dev-key"
    assert log_kwargs["status_code"] == 500
    assert log_kwargs["error"] == "AWS API failed"
    assert log_kwargs["request_id"] == body["request_id"]


def test_health_endpoint_returns_500_when_botocore_error_occurs(
    monkeypatch,
):
    """Unexpected boto3 core errors should return 500."""
    client = make_client(monkeypatch)

    with patch("app.log_api_request") as mock_log_api_request:
        with patch("app.get_instance_health") as mock_get_instance_health:
            mock_get_instance_health.side_effect = BotoCoreError()

            response = client.get(
                "/api/health/i-0123456789abcdef0",
                headers={"X-API-Key": "dev-key"},
            )

    body = response.get_json()
    log_kwargs = mock_log_api_request.call_args.kwargs

    assert response.status_code == 500
    assert body["error"] == "AWS API failed"
    assert "request_id" in body

    assert log_kwargs["method"] == "GET"
    assert log_kwargs["path"] == "/api/health/i-0123456789abcdef0"
    assert log_kwargs["api_key"] == "dev-key"
    assert log_kwargs["status_code"] == 500
    assert log_kwargs["error"] == "AWS API failed"
    assert log_kwargs["request_id"] == body["request_id"]


def test_health_endpoint_returns_json_content_type(monkeypatch):
    """Successful API responses should use a JSON content type."""
    client = make_client(monkeypatch)

    with patch("app.log_api_request"):
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
    assert response.content_type.startswith("application/json")


def test_health_endpoint_does_not_call_aws_when_auth_fails(monkeypatch):
    """AWS should not be called when authentication fails."""
    client = make_client(monkeypatch)

    with patch("app.log_api_request"):
        with patch("app.get_instance_health") as mock_get_instance_health:
            response = client.get(
                "/api/health/i-0123456789abcdef0",
                headers={"X-API-Key": "wrong-key"},
            )

    assert response.status_code == 401
    mock_get_instance_health.assert_not_called()
