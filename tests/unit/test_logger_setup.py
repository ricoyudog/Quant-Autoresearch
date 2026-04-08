import importlib
import logging
import sys


def test_logger_import_creates_missing_log_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sys.modules.pop("utils.logger", None)

    logger_module = importlib.import_module("utils.logger")

    assert (tmp_path / "experiments" / "logs").exists()
    assert isinstance(logger_module.logger, logging.Logger)
    logger_module.logger.handlers.clear()
