# Architecture Notes

## Purpose

This project implements a small Flask API for checking the health of AWS EC2
instances.

The goal is to keep the solution simple, testable, and easy to review while
still applying production-aware practices around authentication, logging,
configuration, and error handling.

## Design Goals

- Keep the API focused on the assessment requirements.
- Separate HTTP routing from AWS integration logic.
- Keep authentication, logging, and cloud health checks independently testable.
- Avoid hardcoded secrets and rely on environment-based configuration.
- Mock AWS calls during tests so the test suite is reliable and repeatable.
- Keep the codebase small enough for quick review and maintenance.

## Request Flow

1. A client calls `GET /api/health/<instance_id>`.
2. The API reads the `X-API-Key` header.
3. The API validates the key against `VALID_API_KEYS`.
4. A request correlation ID is generated.
5. The API queries AWS EC2 using `boto3`.
6. EC2 instance state and status checks are mapped to a health value.
7. The API returns a JSON response.
8. The request outcome is written to `logs/api.log`.

## Module Responsibilities

### `app.py`

Owns the Flask application, route definition, HTTP response construction, and
HTTP status code mapping.

It does not directly contain AWS-specific implementation details.

### `auth.py`

Handles API key validation.

The current implementation reads valid keys from the environment because this
keeps the assessment implementation simple and avoids introducing a database or
secret management dependency.

### `aws_health.py`

Contains the EC2 integration logic.

It is responsible for calling AWS, extracting EC2 state/status data, and
deriving the human-readable health value.

### `logger.py`

Handles request logging.

Logs are intentionally human-readable because the assessment asks for logs that
are easy to grep/search. The logger masks API keys and only includes the first
10 characters.

### `config.py`

Contains small environment configuration helpers.

### `exceptions.py`

Defines application-level exceptions used to separate AWS/client failures from
expected application outcomes such as missing instances.

## Error Handling

The API separates expected and unexpected failures:

| Situation | HTTP Status | Response |
|---|---:|---|
| Missing or invalid API key | 401 | `Unauthorized` |
| EC2 instance not found | 404 | `Instance not found` |
| AWS API failure | 500 | `AWS API failed` |

Authentication failures intentionally return the same error message for missing
and invalid keys. This avoids leaking whether a key was absent, malformed, or
incorrect.

## Health Mapping

The API derives health from EC2 state and instance status checks:

| EC2 State | Status Check | Health |
|---|---|---|
| running | ok | healthy |
| running | initializing | initializing |
| running | failed/impaired | unhealthy |
| stopped | any | stopped |
| terminated | any | terminated |
| other | other | unknown |

## Request Correlation

Each request receives a `request_id`.

The full `request_id` is returned in the API response, while the log entry uses
the first eight characters to keep logs readable.

This makes it easier to match a response to the corresponding log entry during
debugging and review.

## Security Considerations

- AWS credentials are never hardcoded.
- API keys are read from environment variables.
- Full API keys are not logged.
- AWS credentials are not logged.
- Missing and invalid API keys return the same error structure.

For a real production system, API keys should be stored hashed or managed
through a dedicated secret manager.

## Testing Strategy

Tests are written with `pytest`.

AWS calls are mocked with `unittest.mock` so tests do not require real AWS
credentials and do not make network calls.

The tests cover:

- API authentication behaviour
- successful health check responses
- not-found responses
- AWS failure responses
- health status derivation
- structured logging behaviour
- API key masking

## Production Considerations

This implementation is intentionally scoped to the assessment. In a production
environment, the following improvements would be considered:

- Store hashed API keys or use a managed identity provider.
- Add rate limiting.
- Add deployment configuration.
- Add centralised logging.
- Add metrics and alerting.
- Add request duration logging.
- Add support for Azure and GCP behind a cloud provider interface.
- Add CI checks for linting and tests.
- Add containerisation only if deployment requirements justify it.

## Trade-offs

The implementation avoids adding Terraform, Docker, Kubernetes, a database, or
multi-cloud abstractions because the assessment explicitly asks for a simple
Flask-based service focused on AWS EC2.

This keeps the project easy to run, easy to test, and easy to review.
