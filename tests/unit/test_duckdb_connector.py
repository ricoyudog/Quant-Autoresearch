import subprocess
from pathlib import Path

import duckdb
import pandas as pd
import pytest


def _make_trading_days(count: int) -> list[str]:
    """Create an ordered list of business-day strings."""
    return pd.bdate_range("2025-11-03", periods=count).strftime("%Y-%m-%d").tolist()


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


def test_calculate_walk_forward_windows_returns_five_expanding_windows(monkeypatch):
    from data import duckdb_connector

    trading_days = _make_trading_days(12)
    monkeypatch.setattr(duckdb_connector, "get_trading_days", lambda start_date, end_date: trading_days)

    windows = duckdb_connector.calculate_walk_forward_windows("2025-11-03", "2025-11-20", n_windows=5)

    assert windows == [
        {
            "train_start": trading_days[0],
            "train_end": trading_days[1],
            "test_start": trading_days[2],
            "test_end": trading_days[3],
        },
        {
            "train_start": trading_days[0],
            "train_end": trading_days[3],
            "test_start": trading_days[4],
            "test_end": trading_days[5],
        },
        {
            "train_start": trading_days[0],
            "train_end": trading_days[5],
            "test_start": trading_days[6],
            "test_end": trading_days[7],
        },
        {
            "train_start": trading_days[0],
            "train_end": trading_days[7],
            "test_start": trading_days[8],
            "test_end": trading_days[9],
        },
        {
            "train_start": trading_days[0],
            "train_end": trading_days[9],
            "test_start": trading_days[10],
            "test_end": trading_days[11],
        },
    ]


def test_calculate_walk_forward_windows_uses_trading_day_boundaries_without_gaps(monkeypatch):
    from data import duckdb_connector

    trading_days = [
        "2025-11-03",
        "2025-11-04",
        "2025-11-06",
        "2025-11-07",
        "2025-11-10",
        "2025-11-11",
        "2025-11-13",
        "2025-11-14",
        "2025-11-17",
        "2025-11-18",
        "2025-11-20",
        "2025-11-21",
    ]
    monkeypatch.setattr(duckdb_connector, "get_trading_days", lambda start_date, end_date: trading_days)

    windows = duckdb_connector.calculate_walk_forward_windows("2025-11-03", "2025-11-21", n_windows=5)

    covered_test_days = []
    for window in windows:
        train_end_idx = trading_days.index(window["train_end"])
        test_start_idx = trading_days.index(window["test_start"])
        test_end_idx = trading_days.index(window["test_end"])

        assert train_end_idx < test_start_idx
        covered_test_days.extend(trading_days[test_start_idx : test_end_idx + 1])

    assert covered_test_days == trading_days[2:]


def test_calculate_walk_forward_windows_last_window_absorbs_remainder_days(monkeypatch):
    from data import duckdb_connector

    trading_days = _make_trading_days(13)
    monkeypatch.setattr(duckdb_connector, "get_trading_days", lambda start_date, end_date: trading_days)

    windows = duckdb_connector.calculate_walk_forward_windows("2025-11-03", "2025-11-21", n_windows=5)

    assert len(windows) == 5
    assert windows[-1]["test_end"] == trading_days[-1]


def test_calculate_walk_forward_windows_raises_for_insufficient_trading_days(monkeypatch):
    from data import duckdb_connector

    monkeypatch.setattr(duckdb_connector, "get_trading_days", lambda start_date, end_date: [])

    with pytest.raises(ValueError, match="at least"):
        duckdb_connector.calculate_walk_forward_windows("2025-11-03", "2025-11-21", n_windows=5)


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
