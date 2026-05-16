"""Flask application for EC2 health checks."""

from datetime import datetime, timezone
from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, jsonify, request

from auth import is_valid_api_key
from aws_health import get_instance_health
from exceptions import InstanceNotFoundError
from logger import log_api_request


def get_current_timestamp():
    """Return the current UTC timestamp in ISO 8601 format.

    Returns:
        str: Current UTC timestamp formatted for API responses.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_health_response(instance_id, health_result, request_id):
    """Create a health response for an EC2 instance.

    Args:
        instance_id (str): EC2 instance ID from the URL path.
        health_result (dict): EC2 health details.
        request_id (str): Correlation ID for tracing the request.

    Returns:
        dict: Health response payload.
    """
    return {
        "request_id": request_id,
        "instance_id": instance_id,
        "state": health_result["state"],
        "status_code": health_result["status_code"],
        "health": health_result["health"],
        "timestamp": get_current_timestamp(),
    }


def create_error_response(message, request_id):
    """Create a consistent error response.

    Args:
        message (str): Error message.
        request_id (str): Correlation ID for tracing the request.

    Returns:
        dict: Error response payload.
    """
    return {
        "request_id": request_id,
        "error": message,
    }


def build_response(payload, status_code):
    """Build a Flask JSON response with a status code.

    Args:
        payload (dict): JSON response body.
        status_code (int): HTTP status code.

    Returns:
        tuple: Flask response tuple.
    """
    return jsonify(payload), status_code


def create_app():
    """Create and configure the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    @app.route("/api/health/<instance_id>", methods=["GET"])
    def get_health(instance_id):
        """Return health information for an EC2 instance.

        Args:
            instance_id (str): EC2 instance ID from the URL path.

        Returns:
            Response: JSON response containing health information or an error.
        """
        api_key = request.headers.get("X-API-Key")
        method = request.method
        path = request.path
        request_id = str(uuid4())

        if not is_valid_api_key(api_key):
            log_api_request(
                method=method,
                path=path,
                api_key=api_key,
                status_code=401,
                error="Unauthorized",
                request_id=request_id,
            )
            return build_response(
                create_error_response("Unauthorized", request_id),
                401,
            )

        try:
            health_result = get_instance_health(instance_id)
        except InstanceNotFoundError:
            error_message = "Instance not found"
            log_api_request(
                method=method,
                path=path,
                api_key=api_key,
                status_code=404,
                error=error_message,
                request_id=request_id,
            )
            return build_response(
                create_error_response(error_message, request_id),
                404,
            )
        except (BotoCoreError, ClientError):
            error_message = "AWS API failed"
            log_api_request(
                method=method,
                path=path,
                api_key=api_key,
                status_code=500,
                error=error_message,
                request_id=request_id,
            )
            return build_response(
                create_error_response(error_message, request_id),
                500,
            )

        response_body = create_health_response(
            instance_id,
            health_result,
            request_id,
        )

        log_api_request(
            method=method,
            path=path,
            api_key=api_key,
            status_code=200,
            result=response_body["health"],
            request_id=request_id,
        )

        return build_response(response_body, 200)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
