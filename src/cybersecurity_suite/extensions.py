"""Shared Flask extension instances.

Kept separate from ``__init__.py`` so blueprint modules can import them
without triggering circular imports with the application factory.
"""

from __future__ import annotations

from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

__all__ = ["jwt", "limiter"]
