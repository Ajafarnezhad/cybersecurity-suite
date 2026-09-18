"""CyberSecuritySuite: a small, self-hosted authentication + security-scanning
+ encrypted-chat Flask application.

Uses the application-factory pattern so the app can be constructed fresh
per-test (rather than the original module-level ``app = Flask(__name__)``,
which made it impossible to run tests against an isolated instance and, via
the chat blueprint, started a network listener merely by being imported).
"""

from __future__ import annotations

from flask import Flask, jsonify

from .config import Config, validate_production_config
from .extensions import jwt, limiter


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    validate_production_config(app.config)

    jwt.init_app(app)
    limiter.init_app(app)

    from .blueprints.auth import auth_bp
    from .blueprints.chat import chat_bp
    from .blueprints.scanner import scanner_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(scanner_bp, url_prefix="/scan")
    app.register_blueprint(chat_bp, url_prefix="/chat")

    @app.route("/")
    def index():
        return jsonify({"message": "Welcome to CyberSecuritySuite"})

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    if app.config.get("ENABLE_CHAT_DEMO"):
        from .blueprints.chat import start_chat_server

        start_chat_server(host=app.config["CHAT_HOST"], port=app.config["CHAT_PORT"])

    return app


__all__ = ["create_app"]
