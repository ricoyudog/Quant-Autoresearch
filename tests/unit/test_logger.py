import importlib
import logging
import sys
from pathlib import Path

import pytest

from utils.logger import setup_logging


def test_logger_import_creates_missing_log_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    logger = logging.getLogger("quant_autoresearch")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    sys.modules.pop("utils.logger", None)

    try:
        importlib.import_module("utils.logger")
    except FileNotFoundError as exc:
        pytest.fail(f"utils.logger import should create the log directory: {exc}")

    assert (tmp_path / "experiments" / "logs").is_dir()


def test_setup_logging_creates_parent_directory(tmp_path):
    """Logger setup should create the target directory when it does not exist."""
    log_file = tmp_path / "nested" / "logs" / "run.log"
    logger = setup_logging(name="test_logger_creates_dir", log_file=str(log_file))

    assert log_file.parent.exists()
    assert isinstance(log_file, Path)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
