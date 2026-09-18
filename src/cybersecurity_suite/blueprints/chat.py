"""Encrypted local chat demo (OWASP A02: Cryptographic Failures, done right).

Demonstrates symmetric encryption (Fernet/AES) over a raw TCP socket. This is
a teaching example, not an internet-facing service: it binds to
``127.0.0.1`` by default and must be started explicitly.

The original implementation started a background thread that opened a TCP
listener **as a side effect of importing the module** -- meaning merely
importing the Flask app (e.g. to run its test suite) silently spun up a
network server. That is fixed here: :func:`start_chat_server` must be called
explicitly, and the app factory only does so when ``ENABLE_CHAT_DEMO`` is set.
"""

from __future__ import annotations

import socket
import threading

from cryptography.fernet import Fernet
from flask import Blueprint, current_app, jsonify

from ..utils.logger import setup_logger

chat_bp = Blueprint("chat", __name__)
logger = setup_logger("chat")

# A fresh key per process: restarting the server invalidates old sessions,
# which is the correct behavior for a local demo (there is no persistent
# key management here -- see the README for what production key handling
# would require).
_cipher = Fernet(Fernet.generate_key())


@chat_bp.route("/status", methods=["GET"])
def status():
    return jsonify({"enabled": current_app.config.get("ENABLE_CHAT_DEMO", False)})


def _handle_client(client: socket.socket, addr: tuple[str, int]) -> None:
    with client:
        while True:
            try:
                encrypted_msg = client.recv(1024)
                if not encrypted_msg:
                    break
                message = _cipher.decrypt(encrypted_msg).decode()
                logger.info("Decrypted message from %s", addr)
                client.send(_cipher.encrypt(message.encode()))
            except Exception:
                logger.exception("Chat connection error from %s", addr)
                break


def start_chat_server(host: str = "127.0.0.1", port: int = 8888) -> threading.Thread:
    """Start the demo chat server in a background daemon thread and return it."""

    def _serve() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(1)
            logger.info("Chat demo server listening on %s:%s", host, port)
            while True:
                client, addr = server.accept()
                logger.info("Chat connection from %s", addr)
                threading.Thread(target=_handle_client, args=(client, addr), daemon=True).start()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    return thread


__all__ = ["chat_bp", "start_chat_server"]
