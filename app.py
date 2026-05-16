"""Flask application for EC2 health checks."""

from datetime import datetime, timezone

from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, jsonify, request

from auth import AUTH_ERROR_RESPONSE, is_valid_api_key
from aws_health import get_instance_health
from exceptions import InstanceNotFoundError
from logger import log_api_request


def get_current_timestamp():
    """Return the current UTC timestamp in ISO 8601 format.

    Returns:
        str: Current UTC timestamp formatted for API responses.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_health_response(instance_id, health_result):
    """Create a health response for an EC2 instance.

    Args:
        instance_id (str): EC2 instance ID from the URL path.
        health_result (dict): EC2 health details.

    Returns:
        dict: Health response payload.
    """
    return {
        "instance_id": instance_id,
        "state": health_result["state"],
        "status_code": health_result["status_code"],
        "health": health_result["health"],
        "timestamp": get_current_timestamp(),
    }


def create_error_response(message):
    """Create a consistent error response.

    Args:
        message (str): Error message.

    Returns:
        dict: Error response payload.
    """
    return {"error": message}


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

        if not is_valid_api_key(api_key):
            log_api_request(
                method=method,
                path=path,
                api_key=api_key,
                status_code=401,
                error="Unauthorized",
            )
            return build_response(AUTH_ERROR_RESPONSE, 401)

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
            )
            return build_response(create_error_response(error_message), 404)
        except (BotoCoreError, ClientError):
            error_message = "AWS API failed"
            log_api_request(
                method=method,
                path=path,
                api_key=api_key,
                status_code=500,
                error=error_message,
            )
            return build_response(create_error_response(error_message), 500)

        response_body = create_health_response(instance_id, health_result)

        log_api_request(
            method=method,
            path=path,
            api_key=api_key,
            status_code=200,
            result=response_body["health"],
        )

        return build_response(response_body, 200)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
