"""Tests for structured request logging."""

import logging

from logger import mask_api_key


def test_mask_api_key_returns_first_ten_characters():
    """Only the first 10 API key characters should be logged."""
    assert mask_api_key("abcdefghijklmnopqrstuvwxyz") == "abcdefghij"


def test_mask_api_key_returns_missing_for_empty_key():
    """Empty API keys should be logged as missing."""
    assert mask_api_key("") == "missing"


def test_mask_api_key_returns_missing_for_none():
    """Missing API keys should be logged as missing."""
    assert mask_api_key(None) == "missing"


def test_configure_logger_writes_to_file(monkeypatch, tmp_path):
    """The API logger should write human-readable entries to a file."""
    log_file = tmp_path / "api.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))

    import logger as api_logger_module

    api_logger = api_logger_module.configure_logger()

    api_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    api_logger.addHandler(file_handler)

    api_logger_module.log_api_request(
        method="GET",
        path="/api/health/i-012345",
        api_key="abc123def456789",
        status_code=200,
        result="healthy",
    )

    log_content = log_file.read_text(encoding="utf-8")

    assert "GET /api/health/i-012345" in log_content
    assert "Key: abc123def4" in log_content
    assert "Status: 200" in log_content
    assert "Result: healthy" in log_content
    assert "abc123def456789" not in log_content


def test_log_api_request_writes_errors(monkeypatch, tmp_path):
    """Failed API requests should include an error message."""
    log_file = tmp_path / "api.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))

    import logger as api_logger_module

    api_logger = api_logger_module.configure_logger()
    api_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    api_logger.addHandler(file_handler)

    api_logger_module.log_api_request(
        method="GET",
        path="/api/health/i-invalid",
        api_key="abc123def456789",
        status_code=404,
        error="Instance not found",
    )

    log_content = log_file.read_text(encoding="utf-8")

    assert "GET /api/health/i-invalid" in log_content
    assert "Key: abc123def4" in log_content
    assert "Status: 404" in log_content
    assert "Error: Instance not found" in log_content
    assert "abc123def456789" not in log_content
