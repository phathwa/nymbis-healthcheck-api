# Nymbis EC2 Health Check API

A small Flask-based API service for checking the health of AWS EC2 instances.

The service exposes a single authenticated endpoint that accepts an EC2 instance
ID, queries AWS EC2, returns a JSON health response, and logs each request for
audit purposes.

## Features

- Flask REST API endpoint for EC2 health checks
- API key authentication using the `X-API-Key` request header
- AWS EC2 integration using `boto3`
- Human-readable health status derived from EC2 state and status checks
- Structured request logging to `logs/api.log`
- Unit tests using `pytest`
- AWS calls mocked during tests
- Environment-based configuration
- No hardcoded AWS credentials

## Project Structure

```text
.
├── app.py                 # Flask application and API route
├── auth.py                # API key authentication helpers
├── aws_health.py          # AWS EC2 health check logic
├── config.py              # Environment configuration helpers
├── exceptions.py          # Custom application exceptions
├── logger.py              # Structured request logging
├── requirements.txt       # Python dependencies
├── pytest.ini             # Pytest and coverage configuration
├── .env.example           # Example environment configuration
├── logs/
│   └── .gitkeep           # Keeps the logs directory in Git
└── tests/
    ├── test_api.py
    ├── test_auth.py
    ├── test_aws_health.py
    └── test_logger.py
```

## Requirements

- Python 3.x
- AWS credentials configured locally or in the environment
- Access to the AWS account containing the EC2 instances being checked

The application uses the standard `boto3` credential chain. This means AWS
credentials can come from environment variables, AWS CLI profiles, IAM roles, or
AWS credential files.

Do not hardcode AWS credentials in the application code.

## Environment Variables

Create a local `.env` file in the project root:

```env
VALID_API_KEYS=dev-key,another-dev-key
AWS_REGION=eu-west-1
LOG_FILE=logs/api.log
```

### `VALID_API_KEYS`

Comma-separated list of API keys accepted by the service.

Example:

```env
VALID_API_KEYS=dev-key,ops-key
```

### `AWS_REGION`

AWS region used by the EC2 client.

Example:

```env
AWS_REGION=eu-west-1
```

### `LOG_FILE`

Path to the API log file.

Example:

```env
LOG_FILE=logs/api.log
```

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running Locally

Start the Flask app:

```bash
python app.py
```

The API will be available at:

```text
http://127.0.0.1:5000
```

## API Usage

### Health Check Endpoint

```http
GET /api/health/<instance_id>
```

Example:

```bash
curl -i \
  -H "X-API-Key: dev-key" \
  http://127.0.0.1:5000/api/health/i-0123456789abcdef0
```

## Example Responses

### Successful Response

```json
{
  "instance_id": "i-0123456789abcdef0",
  "state": "running",
  "status_code": "ok",
  "health": "healthy",
  "timestamp": "2026-05-16T12:30:45Z"
}
```

### Unauthorized Response

Returned when the `X-API-Key` header is missing or invalid.

```json
{
  "error": "Unauthorized"
}
```

### Instance Not Found Response

```json
{
  "error": "Instance not found"
}
```

### AWS API Failure Response

```json
{
  "error": "AWS API failed"
}
```

## Health Status Mapping

The API derives a human-readable health value from the EC2 instance state and
status checks.

| EC2 State | Status Check | Health |
|---|---|---|
| running | ok | healthy |
| running | initializing | initializing |
| running | failed | unhealthy |
| running | impaired | unhealthy |
| stopped | any | stopped |
| terminated | any | terminated |
| other | other | unknown |

## Authentication

All requests must include an API key:

```http
X-API-Key: dev-key
```

Valid keys are read from the `VALID_API_KEYS` environment variable.

Missing and invalid API keys return the same response:

```json
{
  "error": "Unauthorized"
}
```

This avoids revealing whether a key was missing, malformed, or incorrect.

## Logging

Requests are logged to:

```text
logs/api.log
```

Example success log:

```text
2026-05-16 12:30:45 | GET /api/health/i-012345 | Key: abc123def4 | Status: 200 | Result: healthy
```

Example error log:

```text
2026-05-16 12:31:12 | GET /api/health/i-invalid | Key: abc123def4 | Status: 404 | Error: Instance not found
```

Only the first 10 characters of the API key are logged. Full API keys and AWS
credentials must never be logged.

## Running Tests

Run the test suite:

```bash
python -m pytest
```

The project is configured to show coverage automatically through `pytest.ini`.

To run coverage explicitly:

```bash
python -m pytest --cov=. --cov-report=term-missing
```

AWS calls are mocked in the tests. The test suite should not make real requests
to AWS.

## Linting

Run:

```bash
python -m flake8 .
```

The code should follow PEP 8 conventions, including readable names, clear
function boundaries, and line lengths kept to a reasonable limit.

## Git Workflow

This project was developed using a feature branch:

```bash
git checkout -b feature/ec2-health-api
```

Suggested commit history:

```text
Set up Flask health check API project
Add API key authentication
Add health check API endpoint
Implement EC2 instance health checks
Add structured request logging
Expand pytest coverage for API behaviour
Document setup and usage
```

Each commit should be small, focused, and descriptive.

## Assumptions

- AWS EC2 is the only cloud provider implemented for this assessment.
- AWS credentials are supplied through the standard `boto3` credential chain.
- API keys are stored in environment variables for simplicity.
- Tests mock AWS calls and do not require real AWS credentials.
- The response includes a `health` field because the user stories require a
  derived human-readable status.

## Known Limitations

- The API supports AWS EC2 only.
- API keys are stored as plain environment variable values.
- There is no database-backed audit trail.
- There is no rate limiting.
- The service does not currently support Azure or GCP resources.
- The service is intended as a focused assessment implementation, not a full
  production monitoring platform.

## Future Improvements

- Add support for Azure and GCP health checks.
- Store hashed API keys instead of plain environment values.
- Add request correlation IDs.
- Add rate limiting.
- Add Docker support.
- Add CI pipeline for linting and tests.
- Emit JSON logs for centralised logging platforms if required.
