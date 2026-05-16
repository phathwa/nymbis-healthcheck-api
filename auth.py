"""API key authentication helpers."""

from config import get_valid_api_keys

AUTH_ERROR_RESPONSE = {"error": "Unauthorized"}


def is_valid_api_key(api_key):
    """Check whether the provided API key is valid.

    Args:
        api_key (str | None): API key received from the request header.

    Returns:
        bool: True if the API key is configured and valid.
    """
    if not api_key:
        return False

    valid_keys = get_valid_api_keys()

    return api_key in valid_keys
