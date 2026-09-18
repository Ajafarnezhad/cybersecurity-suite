"""Input validation helpers.

The original ``validate_ip`` used the regex ``^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$``,
which happily accepts nonsense like ``999.999.999.999`` because it never
checks that each octet is in range. We use the standard library's
``ipaddress`` module instead, which is both correct and shorter.
"""

from __future__ import annotations

import ipaddress
import re

# Defense-in-depth only: every subprocess call in this project uses an
# argument list (never `shell=True`), so shell metacharacters can't reach a
# shell. This still strips characters that have no legitimate reason to
# appear in a target/path string.
_DISALLOWED_CHARS = re.compile(r"[;&|`$<>\n\r]")


def sanitize_input(value: str) -> str:
    """Strip shell-metacharacter-like characters from user-supplied strings."""
    if value is None:
        return ""
    return _DISALLOWED_CHARS.sub("", value)


def validate_ip(target: str) -> bool:
    """Return True if ``target`` is a syntactically valid IPv4 or IPv6 address."""
    if not target:
        return False
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False


def validate_scan_target(target: str) -> bool:
    """Validate a scan target: a literal IP address only.

    Hostnames are deliberately rejected here (rather than resolved) so a scan
    request can't be redirected to an unexpected address via DNS at request
    time; callers that need hostname support should resolve and re-validate
    explicitly.
    """
    return validate_ip(target)


__all__ = ["sanitize_input", "validate_ip", "validate_scan_target"]
