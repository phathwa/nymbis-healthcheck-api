# Optional Improvements

These changes were added after the core assessment implementation was complete.

The original solution focuses on the assessment requirements: Flask API, EC2
health checks, API key authentication, structured logging, tests, and README
documentation.

The optional improvements are intended to show production-readiness thinking
without changing the core scope.

## Added Improvements

### Developer Workflow Commands

A `Makefile` was added to make common local commands easier to run:

- `make install`
- `make run`
- `make test`
- `make lint`
- `make format`
- `make check`

This improves reviewer experience and makes validation repeatable.

### Request Correlation IDs

Each API response now includes a `request_id`.

The same ID is written to the request log, making it easier to trace a response
back to its log entry during debugging.

### Architecture Notes

`docs/ARCHITECTURE.md` explains:

- request flow
- module responsibilities
- error handling
- testing strategy
- security considerations
- production trade-offs

### OpenAPI Specification

`docs/openapi.yaml` documents the API contract, including:

- endpoint path
- API key authentication
- path parameters
- success response
- error responses

This can be opened in Swagger Editor or imported into Postman.

## Scope Control

No Docker, Terraform, Kubernetes, database, or multi-cloud abstraction was added
because the assessment specifically asked for a simple Flask-based API focused
on AWS EC2.