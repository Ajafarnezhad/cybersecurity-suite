from __future__ import annotations

from cybersecurity_suite.utils.validators import sanitize_input, validate_ip, validate_scan_target


def test_validate_ip_accepts_valid_addresses():
    assert validate_ip("192.168.1.1") is True
    assert validate_ip("::1") is True


def test_validate_ip_rejects_invalid_addresses():
    assert validate_ip("invalid") is False
    assert validate_ip("") is False
    # The original regex-based check accepted this (each group is 1-3
    # digits) even though 999 is not a valid octet.
    assert validate_ip("999.999.999.999") is False


def test_validate_scan_target_matches_validate_ip():
    assert validate_scan_target("10.0.0.1") is True
    assert validate_scan_target("not-an-ip") is False


def test_sanitize_input_strips_shell_metacharacters():
    assert sanitize_input("input; malicious|") == "input malicious"
    assert sanitize_input("a`b$c") == "abc"


def test_sanitize_input_handles_none():
    assert sanitize_input(None) == ""
