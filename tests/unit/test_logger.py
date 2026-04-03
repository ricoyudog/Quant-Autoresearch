"""Unit tests for logger setup."""

from pathlib import Path

from utils.logger import setup_logging


def test_setup_logging_creates_parent_directory(tmp_path):
    """Logger setup should create the log directory when it does not exist."""
    log_file = tmp_path / "nested" / "logs" / "run.log"
    logger = setup_logging(name="test_logger_creates_dir", log_file=str(log_file))

    assert log_file.parent.exists()
    assert isinstance(log_file, Path)

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
