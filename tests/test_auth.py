"""Tests for API key authentication."""

from auth import is_valid_api_key


def test_valid_api_key_is_accepted(monkeypatch):
    """Valid API keys should be accepted."""
    monkeypatch.setenv("VALID_API_KEYS", "key-one,key-two")

    assert is_valid_api_key("key-one") is True


def test_invalid_api_key_is_rejected(monkeypatch):
    """Invalid API keys should be rejected."""
    monkeypatch.setenv("VALID_API_KEYS", "key-one,key-two")

    assert is_valid_api_key("wrong-key") is False


def test_missing_api_key_is_rejected(monkeypatch):
    """Missing API keys should be rejected."""
    monkeypatch.setenv("VALID_API_KEYS", "key-one,key-two")

    assert is_valid_api_key(None) is False


def test_empty_api_key_config_rejects_all_keys(monkeypatch):
    """No keys should be accepted when no valid keys are configured."""
    monkeypatch.setenv("VALID_API_KEYS", "")

    assert is_valid_api_key("key-one") is False


def test_api_keys_are_trimmed(monkeypatch):
    """Whitespace around configured API keys should be ignored."""
    monkeypatch.setenv("VALID_API_KEYS", " key-one , key-two ")

    assert is_valid_api_key("key-one") is True
    assert is_valid_api_key("key-two") is True


def test_multiple_valid_api_keys_are_supported(monkeypatch):
    """Any configured key in the comma-separated list should be accepted."""
    monkeypatch.setenv("VALID_API_KEYS", "key-one,key-two,key-three")

    assert is_valid_api_key("key-one") is True
    assert is_valid_api_key("key-two") is True
    assert is_valid_api_key("key-three") is True


def test_configured_keys_are_case_sensitive(monkeypatch):
    """API keys should be treated as case-sensitive secrets."""
    monkeypatch.setenv("VALID_API_KEYS", "Key-One")

    assert is_valid_api_key("key-one") is False
    assert is_valid_api_key("Key-One") is True
