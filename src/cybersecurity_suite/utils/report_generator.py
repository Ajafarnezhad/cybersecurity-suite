"""PDF report generation for scan results."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")


def _slugify(value: str) -> str:
    return _SAFE_CHARS.sub("_", value).strip("_") or "target"


def generate_pdf_report(
    results: list[str],
    target: str,
    scan_type: str,
    reports_dir: str = "reports",
) -> str:
    """Render a simple PDF report and return the path it was written to.

    The original implementation named files ``{scan_type}_{date}.pdf``,
    which silently overwrote the previous report for the same scan type run
    on the same day (and never created ``reports/`` if missing). Filenames
    here include the target and a full timestamp to avoid collisions.
    """
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{_slugify(scan_type)}_{_slugify(target)}_{timestamp}.pdf"
    path = os.path.join(reports_dir, filename)

    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 750, f"{scan_type.title()} Scan Report")
    c.setFont("Helvetica", 10)
    c.drawString(72, 730, f"Target: {target}")
    c.drawString(72, 715, f"Generated: {timestamp}")

    y = 690
    c.setFont("Helvetica", 9)
    for line in results or ["No findings."]:
        if y < 72:
            c.showPage()
            c.setFont("Helvetica", 9)
            y = 750
        c.drawString(72, y, str(line))
        y -= 16

    c.save()
    return path


__all__ = ["generate_pdf_report"]
