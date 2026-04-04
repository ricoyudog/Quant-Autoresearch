import subprocess
from pathlib import Path

import duckdb
import pandas as pd
import pytest


def _seed_daily_cache(db_path: Path) -> None:
    connection = duckdb.connect(str(db_path))
    connection.execute(
        """
        CREATE TABLE daily_bars (
            ticker VARCHAR,
            session_date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            transactions INTEGER,
            vwap DOUBLE,
            PRIMARY KEY (ticker, session_date)
        )
        """
    )
    connection.execute(
        """
        INSERT INTO daily_bars VALUES
            ('AAPL', '2025-11-03', 270.0, 271.0, 269.5, 270.5, 1000.0, 100, 270.2),
            ('MSFT', '2025-11-03', 500.0, 505.0, 498.0, 504.0, 2000.0, 150, 502.0),
            ('AAPL', '2025-11-04', 271.0, 272.5, 270.5, 272.0, 1100.0, 105, 271.6)
        """
    )
    connection.close()


def test_build_daily_cache_creates_daily_bars_table(tmp_path, monkeypatch):
    from data import duckdb_connector

    output_path = tmp_path / "daily_cache.duckdb"
    month_ranges = [("2025-11-01", "2025-11-30")]
    monkeypatch.setattr(duckdb_connector, "_iter_month_ranges", lambda start, end: month_ranges)

    def fake_run(cmd, check, capture_output, text, timeout):
        assert cmd[1] == "sql"
        assert "--dataset-root" in cmd
        assert timeout == duckdb_connector.QUERY_TIMEOUT_SECONDS
        output_arg = Path(cmd[cmd.index("--output") + 1])
        output_arg.write_text(
            "ticker,session_date,open,high,low,close,volume,transactions,vwap\n"
            "AAPL,2025-11-03,270.0,271.0,269.5,270.5,1000.0,100,270.2\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(duckdb_connector.subprocess, "run", fake_run)

    duckdb_connector.build_daily_cache(output_path)

    connection = duckdb.connect(str(output_path), read_only=True)
    rows = connection.execute("SELECT ticker, session_date, close FROM daily_bars").fetchall()
    schema_rows = connection.execute("PRAGMA table_info('daily_bars')").fetchall()
    connection.close()

    assert [(ticker, session_date.isoformat(), close) for ticker, session_date, close in rows] == [
        ("AAPL", "2025-11-03", 270.5)
    ]
    primary_key_columns = [row[1] for row in schema_rows if row[5]]
    assert primary_key_columns == ["ticker", "session_date"]


def test_build_daily_cache_reports_month_progress(tmp_path, monkeypatch):
    from data import duckdb_connector

    output_path = tmp_path / "daily_cache.duckdb"
    month_ranges = [("2025-11-01", "2025-11-30")]
    progress_updates = []
    monkeypatch.setattr(duckdb_connector, "_iter_month_ranges", lambda start, end: month_ranges)

    def fake_run(cmd, check, capture_output, text, timeout):
        output_arg = Path(cmd[cmd.index("--output") + 1])
        output_arg.write_text(
            "ticker,session_date,open,high,low,close,volume,transactions,vwap\n"
            "AAPL,2025-11-03,270.0,271.0,269.5,270.5,1000.0,100,270.2\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(duckdb_connector.subprocess, "run", fake_run)

    duckdb_connector.build_daily_cache(
        output_path,
        progress_callback=lambda start_date, end_date: progress_updates.append((start_date, end_date)),
    )

    assert progress_updates == [("2025-11-01", "2025-11-30")]


def test_load_daily_data_filters_by_date_range(tmp_path, monkeypatch):
    from data import duckdb_connector

    db_path = tmp_path / "daily_cache.duckdb"
    _seed_daily_cache(db_path)
    monkeypatch.setattr(duckdb_connector, "DEFAULT_CACHE_PATH", db_path)

    result = duckdb_connector.load_daily_data(start_date="2025-11-04", end_date="2025-11-04")

    assert list(result["ticker"]) == ["AAPL"]
    assert list(result["session_date"].dt.strftime("%Y-%m-%d")) == ["2025-11-04"]


def test_get_trading_days_returns_ordered_date_strings(tmp_path, monkeypatch):
    from data import duckdb_connector

    db_path = tmp_path / "daily_cache.duckdb"
    _seed_daily_cache(db_path)
    monkeypatch.setattr(duckdb_connector, "DEFAULT_CACHE_PATH", db_path)

    result = duckdb_connector.get_trading_days(start_date="2025-11-03", end_date="2025-11-04")

    assert result == ["2025-11-03", "2025-11-04"]


def test_query_minute_data_returns_one_dataframe_per_ticker(monkeypatch):
    from data import duckdb_connector

    def fake_run(cmd, check, capture_output, text, timeout):
        assert cmd[1] == "bars"
        assert cmd[cmd.index("--symbols") + 1 : cmd.index("--start")] == ["AAPL", "MSFT"]
        assert timeout == duckdb_connector.QUERY_TIMEOUT_SECONDS
        output_arg = Path(cmd[cmd.index("--output") + 1])
        output_arg.write_text(
            "ticker,session_date,window_start_ns,open,high,low,close,volume,transactions\n"
            "AAPL,2025-11-03,1,270.0,271.0,269.5,270.5,1000,100\n"
            "MSFT,2025-11-03,2,500.0,505.0,498.0,504.0,2000,150\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(duckdb_connector.subprocess, "run", fake_run)

    result = duckdb_connector.query_minute_data(
        tickers=["AAPL", "MSFT"],
        start_date="2025-11-03",
        end_date="2025-11-03",
    )

    assert sorted(result) == ["AAPL", "MSFT"]
    assert list(result["AAPL"]["close"]) == [270.5]
    assert list(result["MSFT"]["close"]) == [504.0]


def test_query_minute_data_raises_timeout_error(monkeypatch):
    from data import duckdb_connector

    def fake_run(cmd, check, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(duckdb_connector.subprocess, "run", fake_run)

    with pytest.raises(TimeoutError):
        duckdb_connector.query_minute_data(
            tickers=["AAPL"],
            start_date="2025-11-03",
            end_date="2025-11-03",
        )
