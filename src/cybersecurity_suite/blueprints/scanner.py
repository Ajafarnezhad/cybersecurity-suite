"""Scanning endpoints: port scanning, dependency auditing, static analysis.

.. important::
    **Authorized use only.** Only scan hosts, networks, or codebases you own
    or have explicit written permission to test. Port-scanning systems you
    do not control may violate the law (e.g. the U.S. Computer Fraud and
    Abuse Act or equivalent legislation elsewhere) even when no vulnerability
    is exploited.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from ..utils.logger import setup_logger
from ..utils.report_generator import generate_pdf_report
from ..utils.validators import sanitize_input, validate_scan_target

scanner_bp = Blueprint("scanner", __name__)
logger = setup_logger("scanner")


def _parse_port_range(raw: str, max_range: int) -> tuple[int, int]:
    try:
        start_str, end_str = raw.split("-")
        start, end = int(start_str), int(end_str)
    except (ValueError, AttributeError) as exc:
        raise ValueError("ports must be formatted as '<start>-<end>'") from exc

    if not (0 < start <= end <= 65535):
        raise ValueError("port range must satisfy 0 < start <= end <= 65535")
    if end - start + 1 > max_range:
        raise ValueError(f"port range too large; maximum span is {max_range} ports")
    return start, end


def _scan_one_port(target: str, port: int, timeout: float) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((target, port)) == 0


@scanner_bp.route("/port", methods=["POST"])
@jwt_required()
def scan_ports():
    data = request.get_json(silent=True) or {}
    target = sanitize_input(data.get("target", ""))
    ports_raw = data.get("ports", "1-1024")

    if not validate_scan_target(target):
        return jsonify({"error": "Invalid target: must be a literal IPv4/IPv6 address"}), 400

    try:
        start, end = _parse_port_range(ports_raw, current_app.config["SCAN_MAX_PORT_RANGE"])
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    timeout = current_app.config["SCAN_SOCKET_TIMEOUT"]
    ports = range(start, end + 1)
    with ThreadPoolExecutor(max_workers=min(100, len(ports))) as pool:
        open_flags = pool.map(lambda p: _scan_one_port(target, p, timeout), ports)

    results = [f"Port {port} is open" for port, is_open in zip(ports, open_flags) if is_open]
    logger.info("Port scan of %s:%s-%s found %d open port(s)", target, start, end, len(results))

    report_path = generate_pdf_report(
        results, target, "port_scan", reports_dir=current_app.config["REPORTS_DIR"]
    )
    return jsonify({"results": results, "report": report_path})


@scanner_bp.route("/dependencies", methods=["POST"])
@jwt_required()
def scan_dependencies():
    """Run `safety` against the project's installed dependencies (OWASP A06)."""
    try:
        result = subprocess.run(
            ["safety", "check", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        logger.error("`safety` is not installed")
        return jsonify({"error": "The 'safety' tool is not installed on this server."}), 503
    except subprocess.TimeoutExpired:
        logger.error("Dependency scan timed out")
        return jsonify({"error": "Dependency scan timed out."}), 504

    try:
        vulnerabilities = json.loads(result.stdout) if result.stdout else []
    except json.JSONDecodeError:
        logger.error("Could not parse `safety` output: %s", result.stderr)
        return jsonify({"error": "Could not parse dependency scan output."}), 502

    return jsonify({"vulnerabilities": vulnerabilities})


@scanner_bp.route("/static", methods=["POST"])
@jwt_required()
def static_analysis():
    """Run `bandit` against a path within the configured scan root (OWASP A03)."""
    data = request.get_json(silent=True) or {}
    requested_path = sanitize_input(data.get("path", ""))
    if not requested_path:
        return jsonify({"error": "path is required"}), 400

    allowed_root = current_app.config["SCAN_ALLOWED_ROOT"]
    resolved = os.path.realpath(os.path.join(allowed_root, requested_path))

    # Reject any path that escapes the configured root (path traversal, e.g.
    # `../../etc/passwd`); the original endpoint passed the raw user path
    # straight to `bandit` with no such check.
    if os.path.commonpath([allowed_root, resolved]) != allowed_root:
        logger.warning("Rejected out-of-root static analysis path: %s", requested_path)
        return jsonify({"error": "path must be within the allowed scan root"}), 400

    if not os.path.exists(resolved):
        return jsonify({"error": "path does not exist"}), 404

    try:
        result = subprocess.run(
            ["bandit", "-r", resolved, "-f", "json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        logger.error("`bandit` is not installed")
        return jsonify({"error": "The 'bandit' tool is not installed on this server."}), 503
    except subprocess.TimeoutExpired:
        logger.error("Static analysis timed out")
        return jsonify({"error": "Static analysis timed out."}), 504

    try:
        issues = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        logger.error("Could not parse `bandit` output: %s", result.stderr)
        return jsonify({"error": "Could not parse static analysis output."}), 502

    return jsonify({"issues": issues})


__all__ = ["scanner_bp"]
