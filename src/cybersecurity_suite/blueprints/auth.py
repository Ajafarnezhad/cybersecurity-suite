"""Authentication blueprint.

OWASP A07 (Identification and Authentication Failures) and A02
(Cryptographic Failures): the original implementation stored the demo
credential as a **plaintext** string and compared it with ``==``, which is
both insecure and, ironically, a textbook example of the exact class of bug
a security-tooling app should be demonstrating how to avoid. This version
hashes the demo credential with Werkzeug's PBKDF2-based helpers and never
holds a plaintext password after startup.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import limiter
from ..utils.logger import setup_logger

auth_bp = Blueprint("auth", __name__)
logger = setup_logger("auth")

# Demo-only in-memory user store. In a real deployment this would be a
# database table with per-user salts, not a module-level dict.
_USERS = {"admin": generate_password_hash("change-me-please")}


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    password_hash = _USERS.get(username)
    if password_hash and check_password_hash(password_hash, password):
        access_token = create_access_token(identity=username)
        logger.info("User '%s' logged in", username)
        return jsonify({"access_token": access_token})

    logger.warning("Failed login attempt for '%s'", username)
    return jsonify({"error": "Invalid credentials"}), 401


__all__ = ["auth_bp"]
