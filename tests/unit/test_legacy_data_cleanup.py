from pathlib import Path


def test_legacy_data_modules_are_removed():
    assert not Path("src/data/connector.py").exists()
    assert not Path("src/data/preprocessor.py").exists()


def test_surviving_modules_do_not_import_legacy_data_paths():
    cli_source = Path("cli.py").read_text(encoding="utf-8")
    backtester_source = Path("src/core/backtester.py").read_text(encoding="utf-8")
    cache_connector_source = Path("src/data/cache_connector.py").read_text(encoding="utf-8")

    assert "from data.connector import DataConnector" not in cli_source
    assert "from data.connector import DataConnector" not in backtester_source
    assert "data.preprocessor" not in cli_source
    assert "DataConnector" not in cli_source
    assert "DataConnector" not in backtester_source
    assert "class DataConnector" not in cache_connector_source
