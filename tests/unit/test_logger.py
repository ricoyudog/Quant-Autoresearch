import importlib
import logging
import sys

import pytest


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
