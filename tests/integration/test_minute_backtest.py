from pathlib import Path

import pandas as pd
import pytest

import core.backtester as backtester
from data.duckdb_connector import calculate_walk_forward_windows


EXPECTED_METRIC_KEYS = {
    "SCORE",
    "SORTINO",
    "CALMAR",
    "DRAWDOWN",
    "MAX_DD_DAYS",
    "TRADES",
    "P_VALUE",
    "WIN_RATE",
    "PROFIT_FACTOR",
    "AVG_WIN",
    "AVG_LOSS",
    "BASELINE_SHARPE",
}


def parse_backtest_output(stdout: str) -> tuple[dict[str, str], list[str]]:
    metrics = {}
    per_symbol_lines = []
    in_per_symbol = False

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or line == "---":
            continue
        if line == "PER_SYMBOL:":
            in_per_symbol = True
            continue
        if in_per_symbol:
            per_symbol_lines.append(line)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            metrics[key.strip()] = value.strip()

    return metrics, per_symbol_lines


def build_minute_range_data(symbols: list[str], start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
    frames = {}
    sessions = pd.bdate_range(start_date, end_date)
    for offset, ticker in enumerate(symbols):
        rows = []
        base_price = 100.0 + offset * 10.0
        for session_index, session in enumerate(sessions):
            for minute_index in range(3):
                close = base_price + session_index + minute_index + 1.0
                rows.append(
                    {
                        "ticker": ticker,
                        "session_date": session,
                        "window_start_ns": (session_index * 3 + minute_index + 1) * 60_000_000_000,
                        "open": close - 0.2,
                        "high": close + 0.2,
                        "low": close - 0.4,
                        "close": close,
                        "volume": 1_000 + minute_index * 100,
                        "transactions": 10 + minute_index,
                    }
                )
        frames[ticker] = pd.DataFrame(rows)
    return frames


def configure_strategy_env(monkeypatch, minute_strategy_file: Path) -> None:
    monkeypatch.setenv("STRATEGY_FILE", str(minute_strategy_file))
    monkeypatch.delenv("BACKTEST_START_DATE", raising=False)
    monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
    monkeypatch.delenv("BACKTEST_UNIVERSE_SIZE", raising=False)


def test_minute_backtest_pipeline_outputs_metrics(test_duckdb, sample_daily_data, minute_strategy_file, monkeypatch, capsys):
    configure_strategy_env(monkeypatch, minute_strategy_file)

    monkeypatch.setattr(
        backtester,
        "query_minute_data",
        lambda symbols, start_date, end_date: build_minute_range_data(list(symbols), start_date, end_date),
    )

    backtester.walk_forward_validation()
    metrics, per_symbol_lines = parse_backtest_output(capsys.readouterr().out)

    assert EXPECTED_METRIC_KEYS.issubset(metrics.keys())
    assert per_symbol_lines
    assert any(line.startswith("AAA:") for line in per_symbol_lines)
    assert any(line.startswith("BBB:") for line in per_symbol_lines)
    assert all("CCC:" not in line for line in per_symbol_lines)


def test_minute_backtest_uses_five_window_boundaries(
    test_duckdb,
    sample_daily_data,
    minute_strategy_file,
    monkeypatch,
    capsys,
):
    configure_strategy_env(monkeypatch, minute_strategy_file)
    query_calls = []

    def fake_query_minute_data(symbols, start_date, end_date):
        query_calls.append((list(symbols), start_date, end_date))
        return build_minute_range_data(list(symbols), start_date, end_date)

    monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)

    backtester.walk_forward_validation()
    capsys.readouterr()

    expected_windows = calculate_walk_forward_windows(
        sample_daily_data["session_date"].min().strftime("%Y-%m-%d"),
        sample_daily_data["session_date"].max().strftime("%Y-%m-%d"),
        n_windows=5,
    )

    assert len(query_calls) == 5
    assert [(start_date, end_date) for _, start_date, end_date in query_calls] == [
        (window["test_start"], window["test_end"]) for window in expected_windows
    ]


def test_minute_backtest_queries_only_selected_tickers(
    test_duckdb,
    minute_strategy_file,
    monkeypatch,
    capsys,
):
    configure_strategy_env(monkeypatch, minute_strategy_file)
    query_calls = []

    def fake_query_minute_data(symbols, start_date, end_date):
        query_calls.append(list(symbols))
        return build_minute_range_data(list(symbols), start_date, end_date)

    monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)

    backtester.walk_forward_validation()
    capsys.readouterr()

    assert query_calls
    assert all(symbols == ["AAA", "BBB"] for symbols in query_calls)


def test_minute_backtest_applies_signal_lag(
    test_duckdb,
    minute_strategy_file,
    monkeypatch,
    capsys,
):
    configure_strategy_env(monkeypatch, minute_strategy_file)
    lagged_signals = []
    original_apply_signal_lag = backtester.apply_signal_lag

    def fake_query_minute_data(symbols, start_date, end_date):
        return build_minute_range_data(list(symbols), start_date, end_date)

    def recording_apply_signal_lag(signals_by_ticker):
        shifted = original_apply_signal_lag(signals_by_ticker)
        lagged_signals.append({ticker: series.tolist() for ticker, series in shifted.items()})
        return shifted

    monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)
    monkeypatch.setattr(backtester, "apply_signal_lag", recording_apply_signal_lag)

    backtester.walk_forward_validation()
    capsys.readouterr()

    assert lagged_signals
    assert all(series[0] == 0.0 for window in lagged_signals for series in window.values())


def test_minute_backtest_output_format_includes_per_symbol_section(
    test_duckdb,
    minute_strategy_file,
    monkeypatch,
    capsys,
):
    configure_strategy_env(monkeypatch, minute_strategy_file)

    monkeypatch.setattr(
        backtester,
        "query_minute_data",
        lambda symbols, start_date, end_date: build_minute_range_data(list(symbols), start_date, end_date),
    )

    backtester.walk_forward_validation()
    stdout = capsys.readouterr().out

    assert "---" in stdout
    assert "PER_SYMBOL:" in stdout
    assert "AAA:" in stdout
    assert "BBB:" in stdout


def test_minute_backtest_fails_when_window_is_skipped(
    test_duckdb,
    minute_strategy_file,
    monkeypatch,
):
    configure_strategy_env(monkeypatch, minute_strategy_file)

    windows = [
        {
            "train_start": "2025-11-03",
            "train_end": "2025-11-05",
            "test_start": "2025-11-06",
            "test_end": "2025-11-07",
        },
        {
            "train_start": "2025-11-03",
            "train_end": "2025-11-07",
            "test_start": "2025-11-10",
            "test_end": "2025-11-10",
        },
    ]

    def fake_walk_forward_windows(*args, **kwargs):
        return windows

    def fake_query_minute_data(symbols, start_date, end_date):
        if start_date == windows[0]["test_start"]:
            return {}
        return build_minute_range_data(list(symbols), start_date, end_date)

    monkeypatch.setattr(backtester, "calculate_walk_forward_windows", fake_walk_forward_windows)
    monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)

    with pytest.raises(SystemExit) as excinfo:
        backtester.walk_forward_validation()

    assert excinfo.value.code == 1


def test_minute_backtest_fails_when_query_drops_selected_tickers(
    test_duckdb,
    minute_strategy_file,
    monkeypatch,
):
    configure_strategy_env(monkeypatch, minute_strategy_file)

    windows = [
        {
            "train_start": "2025-11-03",
            "train_end": "2025-11-04",
            "test_start": "2025-11-05",
            "test_end": "2025-11-05",
        }
    ]

    def fake_walk_forward_windows(*args, **kwargs):
        return windows

    def fake_query_minute_data(symbols, start_date, end_date):
        return {
            "AAA": build_minute_range_data(["AAA"], start_date, end_date)["AAA"],
        }

    monkeypatch.setattr(backtester, "calculate_walk_forward_windows", fake_walk_forward_windows)
    monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)

    with pytest.raises(SystemExit) as excinfo:
        backtester.walk_forward_validation()

    assert excinfo.value.code == 1
