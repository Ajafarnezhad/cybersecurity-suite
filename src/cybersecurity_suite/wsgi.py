"""WSGI/CLI entry point.

Run with: ``python -m cybersecurity_suite.wsgi`` or via ``flask run`` with
``FLASK_APP=cybersecurity_suite.wsgi``.
"""

from __future__ import annotations

from . import create_app

app = create_app()

if __name__ == "__main__":
    # Binding all interfaces is intentional here: this entry point is meant
    # to run inside a container behind a reverse proxy/firewall, not to be
    # exposed directly on a developer's machine. Use `flask run` (which
    # defaults to 127.0.0.1) for local development instead.
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])  # nosec B104
