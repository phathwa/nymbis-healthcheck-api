"""Flask application for EC2 health checks."""

from flask import Flask, jsonify, request

from auth import AUTH_ERROR_RESPONSE, is_valid_api_key


def create_app():
    """Create and configure the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    @app.route("/api/health/<instance_id>", methods=["GET"])
    def get_health(instance_id):
        """Return a placeholder health response for an EC2 instance.

        Args:
            instance_id (str): EC2 instance ID from the URL path.

        Returns:
            Response: JSON response containing health information or an error.
        """
        api_key = request.headers.get("X-API-Key")

        if not is_valid_api_key(api_key):
            return jsonify(AUTH_ERROR_RESPONSE), 401

        return (
            jsonify(
                {
                    "instance_id": instance_id,
                    "state": "unknown",
                    "status_code": "unknown",
                    "health": "unknown",
                }
            ),
            200,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
