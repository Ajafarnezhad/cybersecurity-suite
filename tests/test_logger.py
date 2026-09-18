from __future__ import annotations

from pathlib import Path

from cybersecurity_suite.utils.logger import setup_logger


def test_setup_logger_creates_log_directory(tmp_path: Path):
    log_dir = tmp_path / "logs"
    logger = setup_logger("test_logger_creates_dir", log_dir=str(log_dir))
    logger.info("hello")
    assert (log_dir / "test_logger_creates_dir.log").exists()


def test_setup_logger_does_not_duplicate_handlers(tmp_path: Path):
    name = "test_logger_no_dupes"
    first = setup_logger(name, log_dir=str(tmp_path))
    handler_count = len(first.handlers)

    second = setup_logger(name, log_dir=str(tmp_path))

    assert second is first
    assert len(second.handlers) == handler_count
