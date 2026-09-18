"""Application configuration.

Secrets are read from the environment. Unlike a typical "quick demo"
config, production mode refuses to start with a missing secret rather than
silently falling back to a hardcoded value baked into every checkout of this
repository -- that fallback is exactly the kind of bug a security-tooling
app should be demonstrating how to avoid.

Values are read at import time (module-level, matching the original
design), but validation of *production* requirements is deferred to
:func:`validate_production_config`, which the app factory calls explicitly.
This keeps merely importing the config (e.g. to build a `TestConfig`-based
app in tests) side-effect-free.
"""

from __future__ import annotations

import logging
import os
import secrets


class ConfigError(RuntimeError):
    """Raised when required production configuration is missing."""


def _debug_enabled() -> bool:
    return os.environ.get("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}


def _secret_or_dev_default(env_var: str) -> str | None:
    value = os.environ.get(env_var)
    if value:
        return value
    if _debug_enabled():
        # Fine for local development: a fresh throwaway secret means tokens
        # simply won't survive a restart, rather than silently reusing a
        # well-known default that ships with every checkout of this repo.
        return secrets.token_hex(32)
    return None  # validated by validate_production_config() before serving traffic


class Config:
    DEBUG = _debug_enabled()
    TESTING = False

    SECRET_KEY = _secret_or_dev_default("SECRET_KEY")
    JWT_SECRET_KEY = _secret_or_dev_default("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", "3600"))

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    LOG_DIR = os.environ.get("LOG_DIR", "logs")
    REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")

    # Directory that `scan/static` is allowed to analyze. Requests for paths
    # outside this root are rejected, closing off the arbitrary-file-read /
    # path-traversal hole in the original implementation.
    SCAN_ALLOWED_ROOT = os.path.abspath(os.environ.get("SCAN_ALLOWED_ROOT", "."))

    # Port scanning is intentionally capped: this is a local/authorized-use
    # utility, not a mass-scanning tool.
    SCAN_MAX_PORT_RANGE = int(os.environ.get("SCAN_MAX_PORT_RANGE", "1024"))
    SCAN_SOCKET_TIMEOUT = float(os.environ.get("SCAN_SOCKET_TIMEOUT", "0.5"))

    RATE_LIMIT_DEFAULT = os.environ.get("RATE_LIMIT_DEFAULT", "200 per day;50 per hour")

    # Off by default: the demo encrypted chat server binds a local TCP
    # socket, which is a side effect a web app should not trigger just by
    # being imported (as the original implementation did).
    ENABLE_CHAT_DEMO = os.environ.get("ENABLE_CHAT_DEMO", "false").lower() in {"1", "true", "yes"}
    CHAT_HOST = os.environ.get("CHAT_HOST", "127.0.0.1")
    CHAT_PORT = int(os.environ.get("CHAT_PORT", "8888"))


class TestConfig(Config):
    DEBUG = True
    TESTING = True
    SECRET_KEY = "test-secret-key-0123456789abcdef"
    JWT_SECRET_KEY = "test-jwt-secret-key-0123456789abcdef"
    ENABLE_CHAT_DEMO = False
    SCAN_SOCKET_TIMEOUT = 0.05


def validate_production_config(config: dict) -> None:
    """Raise :class:`ConfigError` if required secrets are missing outside debug/test mode."""
    if config.get("DEBUG") or config.get("TESTING"):
        return
    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        if not config.get(key):
            raise ConfigError(
                f"Environment variable '{key}' must be set when FLASK_DEBUG is not enabled."
            )


def get_log_level() -> int:
    return getattr(logging, Config.LOG_LEVEL, logging.INFO)


__all__ = ["Config", "ConfigError", "TestConfig", "get_log_level", "validate_production_config"]
