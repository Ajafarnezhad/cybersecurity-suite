"""Structured logging setup.

Fixes two bugs in the original implementation:

1. It wrote to ``logs/`` without ever creating that directory, so the first
   log call crashed with ``FileNotFoundError``.
2. It called ``logging.getLogger(name)`` and unconditionally attached new
   handlers every time ``setup_logger`` ran. Since every request re-imports
   (or re-calls) the same logger name, each call *duplicated* the file and
   console handlers, so every log line eventually got printed 2x, 3x, 4x...
"""

from __future__ import annotations

import logging
import os


def setup_logger(name: str, *, log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured (e.g. called again for the same logger name);
        # avoid attaching duplicate handlers.
        return logger

    logger.setLevel(level)

    os.makedirs(log_dir, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(os.path.join(log_dir, f"{name}.log"), encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger


__all__ = ["setup_logger"]
