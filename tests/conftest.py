import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add src and root to path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

import shutil

@pytest.fixture
def sample_data():
    """Provides a small deterministic OHLCV dataset."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    data = pd.DataFrame({
        "Open": np.linspace(100, 110, 100),
        "High": np.linspace(101, 111, 100),
        "Low": np.linspace(99, 109, 100),
        "Close": np.linspace(100.5, 110.5, 100),
        "Volume": [1000] * 100,
        "returns": [0.001] * 100,
        "volatility": [0.01] * 100,
        "atr": [1.0] * 100
    }, index=dates)
    return data

@pytest.fixture
def temp_cache(tmp_path):
    """Temporary directory for data caching tests."""
    cache_dir = tmp_path / "data_cache"
    cache_dir.mkdir()
    return cache_dir

@pytest.fixture
def mock_strategy_file(tmp_path):
    """Creates a temporary strategy.py for testing."""
    strategy_path = tmp_path / "strategy.py"
    content = """
import pandas as pd
class TradingStrategy:
    def __init__(self): pass
    def generate_signals(self, data):
        return pd.Series(1, index=data.index)
"""
    strategy_path.write_text(content)
    return strategy_path


@pytest.fixture
def test_duckdb_path(tmp_path):
    """Temporary DuckDB path for minute-pipeline integration tests."""
    return tmp_path / "daily_cache.duckdb"


@pytest.fixture
def sample_daily_data():
    """Sample daily-bar frame for the DuckDB-backed minute pipeline."""
    sessions = pd.bdate_range("2025-11-03", periods=12)
    rows = []
    volumes = {"AAA": 5_000_000.0, "BBB": 3_000_000.0, "CCC": 500_000.0}
    closes = {"AAA": 100.0, "BBB": 60.0, "CCC": 20.0}

    for session in sessions:
        for ticker in ["AAA", "BBB", "CCC"]:
            close = closes[ticker]
            rows.append(
                {
                    "ticker": ticker,
                    "session_date": session,
                    "open": close - 0.5,
                    "high": close + 0.8,
                    "low": close - 1.0,
                    "close": close,
                    "volume": volumes[ticker],
                    "transactions": 100,
                    "vwap": close - 0.1,
                }
            )
            closes[ticker] = close + 0.5

    return pd.DataFrame(rows)


@pytest.fixture
def test_duckdb(test_duckdb_path, sample_daily_data, monkeypatch):
    """Seed a temp DuckDB cache and point the connector runtime at it."""
    import duckdb

    from data import duckdb_connector

    connection = duckdb.connect(str(test_duckdb_path))
    connection.execute(duckdb_connector.DAILY_BARS_TABLE_SQL)
    connection.register("sample_daily_data_view", sample_daily_data)
    connection.execute(
        """
        INSERT INTO daily_bars
        SELECT
            ticker,
            session_date,
            open,
            high,
            low,
            close,
            volume,
            transactions,
            vwap
        FROM sample_daily_data_view
        """
    )
    connection.close()

    monkeypatch.setattr(duckdb_connector, "DEFAULT_CACHE_PATH", test_duckdb_path)
    return test_duckdb_path


@pytest.fixture
def minute_strategy_file(tmp_path):
    """Minute-mode strategy file that passes the restricted runtime contract."""
    strategy_path = tmp_path / "minute_strategy.py"
    strategy_path.write_text(
        """
class TradingStrategy:
    def select_universe(self, daily_data):
        return ["AAA", "BBB"]

    def generate_signals(self, data):
        signals = {}
        for ticker, frame in data.items():
            momentum = frame["close"].diff().fillna(0.0)
            signals[ticker] = (momentum > 0).astype(float)
        return signals
""".strip()
    )
    return strategy_path
