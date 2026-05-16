"""Application configuration helpers."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_valid_api_keys():
    """Return valid API keys from the VALID_API_KEYS environment variable.

    The environment variable should be a comma-separated list, for example:

    VALID_API_KEYS=key-one,key-two,key-three

    Returns:
        set[str]: A set of configured API keys.
    """
    raw_keys = os.getenv("VALID_API_KEYS", "")

    return {key.strip() for key in raw_keys.split(",") if key.strip()}
