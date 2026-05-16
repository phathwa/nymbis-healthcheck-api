"""Structured request logging for the health check API."""

import logging
import os
from datetime import datetime

DEFAULT_LOG_FILE = "logs/api.log"
MISSING_KEY_LABEL = "missing"


def get_log_file_path():
    """Return the configured log file path.

    Returns:
        str: Path to the API log file.
    """
    return os.getenv("LOG_FILE", DEFAULT_LOG_FILE)


def mask_api_key(api_key):
    """Return a safe API key label for logs.

    Args:
        api_key (str | None): API key from the request header.

    Returns:
        str: First 10 characters of the key, or a missing label.
    """
    if not api_key:
        return MISSING_KEY_LABEL

    return api_key[:10]


def configure_logger():
    """Configure and return the API logger.

    Returns:
        logging.Logger: Logger configured to write API audit entries.
    """
    log_file = get_log_file_path()
    log_dir = os.path.dirname(log_file)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("api_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)

    return logger


def log_api_request(
    method,
    path,
    api_key,
    status_code,
    result=None,
    error=None,
    request_id=None,
):
    """Log an API request and outcome.

    Args:
        method (str): HTTP method used for the request.
        path (str): Request path.
        api_key (str | None): API key from the request header.
        status_code (int): HTTP status code returned.
        result (str | None): Health result when the request succeeds.
        error (str | None): Error message when the request fails.
        request_id (str | None): Correlation ID for tracing a request.
    """
    logger = configure_logger()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    key_prefix = mask_api_key(api_key)
    request_label = request_id[:8] if request_id else "none"

    outcome = f"Result: {result}"

    if error:
        outcome = f"Error: {error}"

    logger.info(
        "%s | Request: %s | %s %s | Key: %s | Status: %s | %s",
        timestamp,
        request_label,
        method,
        path,
        key_prefix,
        status_code,
        outcome,
    )
