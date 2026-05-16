"""Flask application for EC2 health checks."""

from datetime import datetime, timezone

from flask import Flask, jsonify, request

from auth import AUTH_ERROR_RESPONSE, is_valid_api_key


def get_current_timestamp():
    """Return the current UTC timestamp in ISO 8601 format.

    Returns:
        str: Current UTC timestamp formatted for API responses.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_health_response(instance_id):
    """Create a basic health response for an EC2 instance.

    This response is intentionally static for now because the AWS EC2
    integration will be added in a separate commit.

    Args:
        instance_id (str): EC2 instance ID from the URL path.

    Returns:
        dict: Health response payload.
    """
    return {
        "instance_id": instance_id,
        "state": "unknown",
        "status_code": "unknown",
        "health": "unknown",
        "timestamp": get_current_timestamp(),
    }


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

        if not is_valid_api_key(api_key):
            return jsonify(AUTH_ERROR_RESPONSE), 401

        return jsonify(create_health_response(instance_id)), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
