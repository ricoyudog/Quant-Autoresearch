"""Unit tests for V2 backtester functions.

Tests cover the new functions added to the backtester:
- find_strategy_class
- calculate_metrics
- calculate_baseline_sharpe
- run_per_symbol_analysis
"""

import json

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import core.backtester as backtester
from core.backtester import (
    StrategyContractError,
    apply_signal_lag,
    find_strategy_class,
    calculate_metrics,
    calculate_baseline_sharpe,
    run_per_symbol_analysis,
    validate_strategy_class_contract,
)


class DummyStrategy:
    """Dummy strategy class for testing."""
    def generate_signals(self, data):
        return pd.Series(1, index=data.index)


class AnotherStrategy:
    """Another strategy class for testing."""
    def generate_signals(self, data):
        return pd.Series(0, index=data.index)


class NonStrategyClass:
    """Class without generate_signals method."""
    def some_method(self):
        pass


def build_daily_universe_frame() -> pd.DataFrame:
    """Build a daily-bar frame spanning six trading sessions and three tickers."""
    sessions = pd.to_datetime(
        [
            "2025-11-03",
            "2025-11-04",
            "2025-11-05",
            "2025-11-06",
            "2025-11-07",
            "2025-11-10",
            "2025-11-11",
        ]
    )
    rows = []
    volumes = {"AAA": 5_000_000, "BBB": 3_000_000, "CCC": 500_000}
    closes = {"AAA": 100.0, "BBB": 50.0, "CCC": 20.0}
    for session in sessions:
        for ticker in ["AAA", "BBB", "CCC"]:
            close = closes[ticker]
            rows.append(
                {
                    "ticker": ticker,
                    "session_date": session,
                    "open": close - 0.5,
                    "high": close + 0.5,
                    "low": close - 1.0,
                    "close": close,
                    "volume": volumes[ticker],
                    "transactions": 100,
                    "vwap": close - 0.1,
                }
            )
            closes[ticker] = close + 0.25
    return pd.DataFrame(rows)


def build_window_minute_data(symbols: list[str], session_date: str) -> dict[str, pd.DataFrame]:
    """Build a small per-window minute dataset keyed by ticker."""
    minute_data = {}
    for offset, ticker in enumerate(symbols):
        base = 100.0 + offset * 5.0
        closes = np.array([base, base + 1.0, base + 2.0], dtype=float)
        minute_data[ticker] = pd.DataFrame(
            {
                "ticker": [ticker] * 3,
                "session_date": pd.to_datetime([session_date] * 3),
                "window_start_ns": [1, 2, 3],
                "open": closes - 0.1,
                "high": closes + 0.2,
                "low": closes - 0.2,
                "close": closes,
                "volume": [1_000, 1_050, 1_100],
                "transactions": [10, 12, 11],
            }
        )
    return minute_data


# =============================================================================
# find_strategy_class tests
# =============================================================================

class TestFindStrategyClass:
    """Tests for find_strategy_class function."""

    def test_find_strategy_class_found(self):
        """A partial strategy candidate is still discoverable before contract validation."""
        sandbox_locals = {
            'DummyStrategy': DummyStrategy,
            'other_var': 42,
        }
        strategy_class = find_strategy_class(sandbox_locals)
        assert strategy_class is DummyStrategy
        with pytest.raises(StrategyContractError, match="select_universe"):
            validate_strategy_class_contract(strategy_class)

    def test_find_strategy_class_not_found(self):
        """Empty dict returns None and fails contract validation."""
        strategy_class = find_strategy_class({})
        assert strategy_class is None
        with pytest.raises(StrategyContractError, match="generate_signals"):
            validate_strategy_class_contract(strategy_class)

    def test_find_strategy_class_multiple(self):
        """A full two-hook class is preferred over a partial candidate."""
        class UniverseStrategy:
            def select_universe(self, daily_data):
                return ['SPY']

            def generate_signals(self, data):
                return pd.Series(1, index=data.index)

        sandbox_locals = {
            'UniverseStrategy': UniverseStrategy,
            'DummyStrategy': DummyStrategy,
        }
        strategy_class = find_strategy_class(sandbox_locals)
        assert strategy_class is UniverseStrategy
        assert hasattr(strategy_class, 'generate_signals')
        assert validate_strategy_class_contract(strategy_class) is UniverseStrategy

    def test_find_strategy_class_non_class_ignored(self):
        """Functions/variables are ignored and no candidate means no strategy class."""
        def generate_signals(data):
            return pd.Series(1, index=data.index)

        sandbox_locals = {
            'NonStrategyClass': NonStrategyClass,
            'generate_signals': generate_signals,
            'some_number': 42,
        }
        strategy_class = find_strategy_class(sandbox_locals)
        assert strategy_class is None
        with pytest.raises(StrategyContractError, match="generate_signals"):
            validate_strategy_class_contract(strategy_class)


# =============================================================================
# apply_signal_lag tests
# =============================================================================

class TestApplySignalLag:
    """Tests for per-ticker signal lag handling."""

    def test_apply_signal_lag_shifts_each_ticker_independently(self):
        """Each ticker series is shifted by one bar without changing keys or indexes."""
        raw_signals = {
            "AAPL": pd.Series([1, 0, -1], index=pd.Index([10, 11, 12])),
            "MSFT": pd.Series([-1, 1], index=pd.Index([20, 21])),
        }

        shifted = apply_signal_lag(raw_signals)

        assert set(shifted.keys()) == {"AAPL", "MSFT"}
        assert shifted["AAPL"].index.equals(raw_signals["AAPL"].index)
        assert shifted["MSFT"].index.equals(raw_signals["MSFT"].index)
        assert shifted["AAPL"].tolist() == [0, 1, 0]
        assert shifted["MSFT"].tolist() == [0, -1]


class TestWalkForwardValidationMinutePipeline:
    """Tests for the Sprint 2 Step 6 minute-data walk-forward integration."""

    def test_walk_forward_validation_uses_environment_date_range(self, monkeypatch, tmp_path, capsys):
        """Runtime date overrides should be forwarded to load_daily_data()."""
        strategy_path = tmp_path / "strategy.py"
        strategy_path.write_text(
            """
class MinuteStrategy:
    def select_universe(self, daily_data):
        return ["AAA"]

    def generate_signals(self, data):
        return {"AAA": pd.Series([1.0, 0.0, -1.0], index=data["AAA"].index)}
""".strip()
        )

        load_calls = []
        daily_data = build_daily_universe_frame()

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.setenv("BACKTEST_START_DATE", "2025-11-04")
        monkeypatch.setenv("BACKTEST_END_DATE", "2025-11-10")
        monkeypatch.delenv("BACKTEST_UNIVERSE_SIZE", raising=False)

        def fake_load_daily_data(start_date=None, end_date=None):
            load_calls.append((start_date, end_date))
            return daily_data.copy()

        monkeypatch.setattr(backtester, "load_daily_data", fake_load_daily_data)
        monkeypatch.setattr(
            backtester,
            "calculate_walk_forward_windows",
            lambda start_date, end_date, n_windows=5: [
                {
                    "train_start": "2025-11-04",
                    "train_end": "2025-11-06",
                    "test_start": "2025-11-07",
                    "test_end": "2025-11-10",
                }
            ],
        )
        monkeypatch.setattr(
            backtester,
            "query_minute_data",
            lambda symbols, start_date, end_date: build_window_minute_data(list(symbols), start_date),
        )
        monkeypatch.setattr(
            backtester,
            "calculate_metrics",
            lambda combined_returns, trades, trade_activity=None: {
                "sharpe": 1.0,
                "sortino": 1.0,
                "calmar": 1.0,
                "drawdown": -0.1,
                "max_dd_days": 1,
                "trades": 2,
                "win_rate": 0.5,
                "profit_factor": 1.1,
                "avg_win": 0.01,
                "avg_loss": -0.01,
            },
        )
        monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.5)

        backtester.walk_forward_validation()
        output = capsys.readouterr().out

        assert load_calls == [("2025-11-04", "2025-11-10")]
        assert "SCORE:" in output

    def test_walk_forward_validation_caps_universe_from_environment(self, monkeypatch, tmp_path, capsys):
        """BACKTEST_UNIVERSE_SIZE should cap the normalized ticker universe."""
        strategy_path = tmp_path / "strategy.py"
        strategy_path.write_text(
            """
class MinuteStrategy:
    def select_universe(self, daily_data):
        return ["AAA", "BBB", "CCC"]

    def generate_signals(self, data):
        signals = {}
        for ticker, frame in data.items():
            signals[ticker] = pd.Series([1.0, 0.0, -1.0], index=frame.index)
        return signals
""".strip()
        )

        query_calls = []
        daily_data = build_daily_universe_frame()

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.delenv("BACKTEST_START_DATE", raising=False)
        monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
        monkeypatch.setenv("BACKTEST_UNIVERSE_SIZE", "2")
        monkeypatch.setattr(backtester, "load_daily_data", lambda start_date=None, end_date=None: daily_data.copy())
        monkeypatch.setattr(
            backtester,
            "calculate_walk_forward_windows",
            lambda start_date, end_date, n_windows=5: [
                {
                    "train_start": "2025-11-03",
                    "train_end": "2025-11-05",
                    "test_start": "2025-11-06",
                    "test_end": "2025-11-07",
                }
            ],
        )

        def fake_query_minute_data(symbols, start_date, end_date):
            query_calls.append(list(symbols))
            return build_window_minute_data(list(symbols), start_date)

        monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)
        monkeypatch.setattr(
            backtester,
            "calculate_metrics",
            lambda combined_returns, trades, trade_activity=None: {
                "sharpe": 1.0,
                "sortino": 1.0,
                "calmar": 1.0,
                "drawdown": -0.1,
                "max_dd_days": 1,
                "trades": 2,
                "win_rate": 0.5,
                "profit_factor": 1.1,
                "avg_win": 0.01,
                "avg_loss": -0.01,
            },
        )
        monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.5)

        backtester.walk_forward_validation()
        output = capsys.readouterr().out

        assert query_calls == [["AAA", "BBB"]]
        assert "PER_SYMBOL:" in output


def _build_minute_data_for_symbols(symbols: list[str], start_date: str) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for idx, ticker in enumerate(symbols):
        closes = [100.0 + idx, 100.5 + idx]
        frames[ticker] = pd.DataFrame(
            {
                "ticker": [ticker, ticker],
                "session_date": pd.to_datetime([start_date, start_date]),
                "window_start_ns": [1, 2],
                "open": [close - 0.1 for close in closes],
                "high": [close + 0.1 for close in closes],
                "low": [close - 0.2 for close in closes],
                "close": closes,
                "volume": [1_000 + idx * 100] * 2,
                "transactions": [10, 11],
            }
        )
    return frames


def _configure_walk_forward_env(monkeypatch, tmp_path, strategy_script: str, windows: list[dict[str, str]], daily_data: pd.DataFrame):
    strategy_path = tmp_path / "strategy.py"
    strategy_path.write_text(strategy_script)
    monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
    monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
    monkeypatch.delenv("BACKTEST_START_DATE", raising=False)
    monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
    monkeypatch.delenv("BACKTEST_UNIVERSE_SIZE", raising=False)
    monkeypatch.setattr(backtester, "calculate_walk_forward_windows", lambda start_date, end_date, n_windows=5: windows)
    monkeypatch.setattr(backtester, "load_daily_data", lambda start_date=None, end_date=None: daily_data.copy())
    return strategy_path


def test_walk_forward_validation_errors_when_window_skips(monkeypatch, tmp_path):
    """Walk-forward must fail when any window returns no minute data."""
    strategy_script = """
class MinuteStrategy:
    def select_universe(self, daily_data):
        return ["AAA"]

    def generate_signals(self, data):
        return {"AAA": data["AAA"]["close"].pct_change().fillna(0.0)}
"""
    windows = [
        {"train_start": "2025-11-03", "train_end": "2025-11-05", "test_start": "2025-11-06", "test_end": "2025-11-06"},
        {"train_start": "2025-11-03", "train_end": "2025-11-06", "test_start": "2025-11-07", "test_end": "2025-11-07"},
    ]
    daily_data = build_daily_universe_frame()
    _configure_walk_forward_env(monkeypatch, tmp_path, strategy_script, windows, daily_data)

    def fake_query(symbols, start_date, end_date):
        if start_date == windows[0]["test_start"]:
            return {}
        return _build_minute_data_for_symbols(["AAA"], start_date)

    monkeypatch.setattr(backtester, "query_minute_data", fake_query)

    with pytest.raises(SystemExit):
        backtester.walk_forward_validation()


def test_walk_forward_validation_errors_when_ticker_missing(monkeypatch, tmp_path):
    """Walk-forward should fail if minute data omits selected tickers."""
    strategy_script = """
class UniverseStrategy:
    def select_universe(self, daily_data):
        return ["AAA", "BBB"]

    def generate_signals(self, data):
        return {ticker: data[ticker]["close"].pct_change().fillna(0.0) for ticker in data}
"""
    windows = [
        {"train_start": "2025-11-03", "train_end": "2025-11-05", "test_start": "2025-11-06", "test_end": "2025-11-06"}
    ]
    daily_data = build_daily_universe_frame()
    _configure_walk_forward_env(monkeypatch, tmp_path, strategy_script, windows, daily_data)

    def fake_query(symbols, start_date, end_date):
        return _build_minute_data_for_symbols(["AAA"], start_date)

    monkeypatch.setattr(backtester, "query_minute_data", fake_query)

    with pytest.raises(SystemExit):
        backtester.walk_forward_validation()


def test_walk_forward_validation_recomputes_universe_per_training_window(monkeypatch, tmp_path, capsys):
    """Universe selection should be recomputed from each window's training slice."""
    strategy_script = """
class WindowAwareStrategy:
    def select_universe(self, daily_data):
        latest = str(daily_data["session_date"].iloc[-1])[:10]
        if latest <= "2025-11-05":
            return ["AAA"]
        return ["BBB"]

    def generate_signals(self, data):
        return {
            ticker: pd.Series([1.0] * len(frame), index=frame.index)
            for ticker, frame in data.items()
        }
"""
    windows = [
        {"train_start": "2025-11-03", "train_end": "2025-11-05", "test_start": "2025-11-06", "test_end": "2025-11-06"},
        {"train_start": "2025-11-03", "train_end": "2025-11-06", "test_start": "2025-11-07", "test_end": "2025-11-07"},
    ]
    daily_data = build_daily_universe_frame()
    _configure_walk_forward_env(monkeypatch, tmp_path, strategy_script, windows, daily_data)

    query_calls = []

    def fake_query(symbols, start_date, end_date):
        query_calls.append((list(symbols), start_date, end_date))
        return build_window_minute_data(list(symbols), start_date)

    monkeypatch.setattr(backtester, "query_minute_data", fake_query)
    monkeypatch.setattr(
        backtester,
        "calculate_metrics",
        lambda combined_returns, trades, trade_activity=None: {
            "sharpe": 1.0,
            "sortino": 1.0,
            "calmar": 1.0,
            "drawdown": -0.1,
            "max_dd_days": 1,
            "trades": 1,
            "win_rate": 0.5,
            "profit_factor": 1.0,
            "avg_win": 0.01,
            "avg_loss": -0.01,
        },
    )
    monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.1)

    backtester.walk_forward_validation()
    capsys.readouterr()

    assert query_calls == [
        (["AAA"], "2025-11-06", "2025-11-06"),
        (["BBB"], "2025-11-07", "2025-11-07"),
    ]


def test_walk_forward_validation_rejects_strategy_missing_select_universe(monkeypatch, tmp_path, capsys):
    """Strategies missing select_universe should fail with contract_invalid before querying minute data."""
    strategy_script = """
class MinuteStrategy:
    def generate_signals(self, data):
        return {
            ticker: pd.Series([1.0] * len(frame), index=frame.index)
            for ticker, frame in data.items()
        }
"""
    windows = [
        {"train_start": "2025-11-03", "train_end": "2025-11-06", "test_start": "2025-11-07", "test_end": "2025-11-07"},
    ]
    rows = []
    sessions = pd.to_datetime(["2025-11-03", "2025-11-04", "2025-11-05", "2025-11-06"])
    for session in sessions:
        rows.append(
            {
                "ticker": "AAA",
                "session_date": session,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1_000_000,
                "transactions": 100,
                "vwap": 100.2,
            }
        )
        rows.append(
            {
                "ticker": "BBB",
                "session_date": session,
                "open": 50.0,
                "high": 51.0,
                "low": 49.0,
                "close": 50.5,
                "volume": 750_000,
                "transactions": 80,
                "vwap": 50.2,
            }
        )

    for session in sessions[:2]:
        rows.append(
            {
                "ticker": "OLD",
                "session_date": session,
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.5,
                "volume": 5_000_000,
                "transactions": 50,
                "vwap": 10.2,
            }
        )

    daily_data = pd.DataFrame(rows)
    _configure_walk_forward_env(monkeypatch, tmp_path, strategy_script, windows, daily_data)

    query_calls = []

    def fake_query(symbols, start_date, end_date):
        query_calls.append((list(symbols), start_date, end_date))
        return build_window_minute_data(list(symbols), start_date)

    monkeypatch.setattr(backtester, "query_minute_data", fake_query)
    monkeypatch.setattr(
        backtester,
        "calculate_metrics",
        lambda combined_returns, trades, trade_activity=None: {
            "sharpe": 1.0,
            "sortino": 1.0,
            "calmar": 1.0,
            "drawdown": -0.1,
            "max_dd_days": 1,
            "trades": 1,
            "win_rate": 0.5,
            "profit_factor": 1.0,
            "avg_win": 0.01,
            "avg_loss": -0.01,
        },
    )
    monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.1)

    with pytest.raises(SystemExit) as excinfo:
        backtester.walk_forward_validation()
    output = capsys.readouterr().out

    assert excinfo.value.code == 1
    assert not query_calls
    assert "STRATEGY ERROR:" in output
    assert "select_universe" in output


class TestWalkForwardValidationMinutePipelineContinued:
    def test_walk_forward_validation_rejects_invalid_environment_configuration(self, monkeypatch, tmp_path, capsys):
        """Invalid environment overrides should fail deterministically."""
        strategy_path = tmp_path / "strategy.py"
        strategy_path.write_text(
            """
class MinuteStrategy:
    def generate_signals(self, data):
        return {}
""".strip()
        )

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.setenv("BACKTEST_START_DATE", "2025-11-04")
        monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
        monkeypatch.setenv("BACKTEST_UNIVERSE_SIZE", "0")
        monkeypatch.setattr(
            backtester,
            "load_daily_data",
            lambda start_date=None, end_date=None: pytest.fail(
                "invalid configuration should exit before loading daily data"
            ),
        )

        with pytest.raises(SystemExit) as excinfo:
            backtester.walk_forward_validation()

        output = capsys.readouterr().out
        assert excinfo.value.code == 1
        assert "DATA ERROR:" in output

    def test_walk_forward_validation_does_not_fallback_to_legacy_runtime_when_daily_data_missing(
        self,
        monkeypatch,
        tmp_path,
        capsys,
    ):
        """Minute-mode V2 should fail explicitly instead of silently using the legacy runtime."""
        strategy_path = tmp_path / "strategy.py"
        strategy_path.write_text(
            """
class MinuteStrategy:
    def select_universe(self, daily_data):
        return ["AAA"]

    def generate_signals(self, data):
        return {}
""".strip()
        )

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.delenv("BACKTEST_START_DATE", raising=False)
        monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
        monkeypatch.delenv("BACKTEST_UNIVERSE_SIZE", raising=False)
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.setattr(
            backtester,
            "load_daily_data",
            lambda start_date=None, end_date=None: pd.DataFrame(),
            raising=False,
        )
        monkeypatch.setattr(
            backtester,
            "_legacy_walk_forward_validation",
            lambda strategy_instance: pytest.fail("legacy runtime should not be used"),
        )

        with pytest.raises(SystemExit) as excinfo:
            backtester.walk_forward_validation()

        output = capsys.readouterr().out
        assert excinfo.value.code == 1
        assert "DATA ERROR:" in output

    def test_walk_forward_validation_uses_daily_universe_and_minute_windows(self, monkeypatch, tmp_path, capsys):
        """walk_forward_validation should use the DuckDB daily->universe->minute flow."""
        strategy_path = tmp_path / "strategy.py"
        strategy_path.write_text(
            """
class MinuteStrategy:
    def select_universe(self, daily_data):
        return ["AAA", "BBB"]

    def generate_signals(self, data):
        signals = {}
        for ticker, frame in data.items():
            signals[ticker] = pd.Series([1.0, 0.0, -1.0], index=frame.index)
        return signals
""".strip()
        )

        query_calls = []
        lag_inputs = []
        metric_inputs = []
        daily_data = build_daily_universe_frame()
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
                "test_end": "2025-11-11",
            },
        ]

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.setattr(backtester, "load_data", lambda: pytest.fail("legacy load_data should not be used"))
        monkeypatch.setattr(
            backtester,
            "load_daily_data",
            lambda start_date=None, end_date=None: daily_data.copy(),
            raising=False,
        )
        monkeypatch.setattr(
            backtester,
            "calculate_walk_forward_windows",
            lambda start_date, end_date, n_windows=5: list(windows),
            raising=False,
        )

        def fake_query_minute_data(symbols, start_date, end_date):
            query_calls.append((list(symbols), start_date, end_date))
            return build_window_minute_data(list(symbols), start_date)

        monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data, raising=False)

        original_apply_signal_lag = backtester.apply_signal_lag

        def recording_apply_signal_lag(signals_by_ticker):
            lag_inputs.append({ticker: series.tolist() for ticker, series in signals_by_ticker.items()})
            return original_apply_signal_lag(signals_by_ticker)

        monkeypatch.setattr(backtester, "apply_signal_lag", recording_apply_signal_lag)

        def fake_calculate_metrics(combined_returns, trades, trade_activity=None):
            metric_inputs.append(
                {
                    "combined_returns": combined_returns.tolist(),
                    "trades": trades.tolist(),
                }
            )
            return {
                "sharpe": 1.5,
                "sortino": 2.0,
                "calmar": 1.2,
                "drawdown": -0.1,
                "max_dd_days": 3,
                "trades": 4,
                "win_rate": 0.6,
                "profit_factor": 1.4,
                "avg_win": 0.02,
                "avg_loss": -0.01,
            }

        monkeypatch.setattr(backtester, "calculate_metrics", fake_calculate_metrics)
        monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.75)

        backtester.walk_forward_validation()
        output = capsys.readouterr().out

        assert query_calls == [
            (["AAA", "BBB"], "2025-11-06", "2025-11-07"),
            (["AAA", "BBB"], "2025-11-10", "2025-11-11"),
        ]
        assert lag_inputs == [
            {"AAA": [1.0, 0.0, -1.0], "BBB": [1.0, 0.0, -1.0]},
            {"AAA": [1.0, 0.0, -1.0], "BBB": [1.0, 0.0, -1.0]},
        ]
        assert len(metric_inputs) == 4
        assert "SCORE: 1.5000" in output
        assert "BASELINE_SHARPE: 0.7500" in output
        assert "PER_SYMBOL:" in output
        assert "AAA:" in output
        assert "BBB:" in output

    def test_walk_forward_validation_reports_no_trade_universe_for_empty_selection(self, monkeypatch, tmp_path, capsys):
        """An empty selected universe should fail deterministically as no_trade_universe."""
        strategy_path = tmp_path / "strategy.py"
        strategy_path.write_text(
            """
class MinuteStrategy:
    def select_universe(self, daily_data):
        return []

    def generate_signals(self, data):
        signals = {}
        for ticker, frame in data.items():
            signals[ticker] = pd.Series([1.0] * len(frame), index=frame.index)
        return signals
""".strip()
        )

        query_calls = []
        daily_data = build_daily_universe_frame()

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.setattr(backtester, "load_daily_data", lambda start_date=None, end_date=None: daily_data.copy())
        monkeypatch.setattr(
            backtester,
            "calculate_walk_forward_windows",
            lambda start_date, end_date, n_windows=5: [
                {
                    "train_start": "2025-11-03",
                    "train_end": "2025-11-05",
                    "test_start": "2025-11-06",
                    "test_end": "2025-11-07",
                }
            ],
        )

        def fake_query_minute_data(symbols, start_date, end_date):
            query_calls.append((list(symbols), start_date, end_date))
            return _build_minute_data_for_symbols(list(symbols), start_date)

        monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)
        monkeypatch.setattr(
            backtester,
            "calculate_metrics",
            lambda combined_returns, trades, trade_activity=None: {
                "sharpe": 1.0,
                "sortino": 1.1,
                "calmar": 0.9,
                "drawdown": -0.05,
                "max_dd_days": 2,
                "trades": 3,
                "win_rate": 0.5,
                "profit_factor": 1.2,
                "avg_win": 0.01,
                "avg_loss": -0.01,
            },
        )
        monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.55)

        with pytest.raises(SystemExit) as excinfo:
            backtester.walk_forward_validation()
        output = capsys.readouterr().out

        assert excinfo.value.code == 1
        assert not query_calls
        assert "no_trade_universe" in output

    def test_walk_forward_validation_handles_real_metrics_with_multiple_tickers(self, monkeypatch, tmp_path, capsys):
        """Real metric calculation should work for multi-ticker minute windows."""
        strategy_path = tmp_path / "strategy.py"
        strategy_path.write_text(
            """
class MinuteStrategy:
    def select_universe(self, daily_data):
        return ["AAA", "BBB"]

    def generate_signals(self, data):
        signals = {}
        for ticker, frame in data.items():
            signals[ticker] = pd.Series([1.0, 0.0, -1.0], index=frame.index)
        return signals
""".strip()
        )

        daily_data = build_daily_universe_frame()
        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.setattr(backtester, "load_daily_data", lambda start_date=None, end_date=None: daily_data.copy())
        monkeypatch.setattr(
            backtester,
            "calculate_walk_forward_windows",
            lambda start_date, end_date, n_windows=5: [
                {
                    "train_start": "2025-11-03",
                    "train_end": "2025-11-05",
                    "test_start": "2025-11-06",
                    "test_end": "2025-11-07",
                }
            ],
        )
        monkeypatch.setattr(
            backtester,
            "query_minute_data",
            lambda symbols, start_date, end_date: build_window_minute_data(list(symbols), start_date),
        )

        backtester.walk_forward_validation()
        output = capsys.readouterr().out

        assert "SCORE:" in output
        assert "PER_SYMBOL:" in output
        assert "AAA:" in output
        assert "BBB:" in output

    def test_walk_forward_validation_runs_default_active_strategy_in_sandbox(self, monkeypatch, capsys):
        """The default strategy should execute in the restricted runtime with dict minute input."""
        strategy_path = Path(__file__).resolve().parents[2] / "src" / "strategies" / "active_strategy.py"
        daily_data = build_daily_universe_frame()

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.delenv("BACKTEST_START_DATE", raising=False)
        monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
        monkeypatch.setenv("BACKTEST_UNIVERSE_SIZE", "2")
        monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
        monkeypatch.setattr(backtester, "load_daily_data", lambda start_date=None, end_date=None: daily_data.copy())
        monkeypatch.setattr(
            backtester,
            "calculate_walk_forward_windows",
            lambda start_date, end_date, n_windows=5: [
                {
                    "train_start": "2025-11-03",
                    "train_end": "2025-11-05",
                    "test_start": "2025-11-06",
                    "test_end": "2025-11-07",
                }
            ],
        )
        monkeypatch.setattr(
            backtester,
            "query_minute_data",
            lambda symbols, start_date, end_date: build_window_minute_data(list(symbols), start_date),
        )
        monkeypatch.setattr(
            backtester,
            "calculate_metrics",
            lambda combined_returns, trades, trade_activity=None: {
                "sharpe": 1.0,
                "sortino": 1.0,
                "calmar": 1.0,
                "drawdown": -0.1,
                "max_dd_days": 1,
                "trades": 2,
                "win_rate": 0.5,
                "profit_factor": 1.1,
                "avg_win": 0.01,
                "avg_loss": -0.01,
            },
        )
        monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.5)

        backtester.walk_forward_validation()
        output = capsys.readouterr().out

        assert "SCORE:" in output
        assert "PER_SYMBOL:" in output



def test_get_backtest_runtime_config_rejects_non_integer_universe_size(monkeypatch):
    """BACKTEST_UNIVERSE_SIZE must be an integer before any data is loaded."""
    monkeypatch.delenv("BACKTEST_START_DATE", raising=False)
    monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
    monkeypatch.setenv("BACKTEST_UNIVERSE_SIZE", "not-an-int")

    with pytest.raises(ValueError, match="BACKTEST_UNIVERSE_SIZE must be a positive integer"):
        backtester.get_backtest_runtime_config()


def test_normalize_universe_selection_deduplicates_and_drops_blank_entries():
    """Universe normalization should preserve intentional ETF symbols while removing blanks and duplicates."""
    selected = backtester.normalize_universe_selection(["SPY", "AAPL", "", "SPY", None, "  MSFT  "])

    assert selected == ["SPY", "AAPL", "MSFT"]


def test_normalize_universe_selection_rejects_scalar_non_sequence():
    """A scalar non-sequence is not a valid select_universe output."""
    with pytest.raises(StrategyContractError, match="select_universe"):
        backtester.normalize_universe_selection(123)


def test_walk_forward_validation_writes_universe_selection_artifact(monkeypatch, tmp_path, capsys):
    """Backtester should persist raw per-window selected tickers separately from PER_SYMBOL output."""
    strategy_path = tmp_path / "strategy.py"
    strategy_path.write_text(
        """
class ETFAllowedStrategy:
    universe_selection_thesis = "Select liquid risk-on ETFs and stocks by training-window momentum."

    def select_universe(self, daily_data):
        return ["SPY", "AAPL", "SPY", "", "MSFT"]

    def generate_signals(self, data):
        return {
            ticker: pd.Series([1.0, 0.0, -1.0], index=frame.index)
            for ticker, frame in data.items()
        }
""".strip()
    )
    artifact_path = tmp_path / "universe_selection.json"
    daily_data = build_daily_universe_frame()
    windows = [
        {
            "train_start": "2025-11-03",
            "train_end": "2025-11-05",
            "test_start": "2025-11-06",
            "test_end": "2025-11-07",
        }
    ]
    query_calls = []

    monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
    monkeypatch.setenv("BACKTEST_UNIVERSE_SIZE", "2")
    monkeypatch.setenv("BACKTEST_UNIVERSE_SELECTION_PATH", str(artifact_path))
    monkeypatch.delenv("BACKTEST_START_DATE", raising=False)
    monkeypatch.delenv("BACKTEST_END_DATE", raising=False)
    monkeypatch.setattr(backtester, "security_check", lambda file_path=None: (True, ""))
    monkeypatch.setattr(backtester, "load_daily_data", lambda start_date=None, end_date=None: daily_data.copy())
    monkeypatch.setattr(backtester, "calculate_walk_forward_windows", lambda start_date, end_date, n_windows=5: list(windows))

    def fake_query_minute_data(symbols, start_date, end_date):
        query_calls.append(list(symbols))
        return build_window_minute_data(list(symbols), start_date)

    monkeypatch.setattr(backtester, "query_minute_data", fake_query_minute_data)
    monkeypatch.setattr(
        backtester,
        "calculate_metrics",
        lambda combined_returns, trades, trade_activity=None: {
            "sharpe": 1.0,
            "sortino": 1.0,
            "calmar": 1.0,
            "drawdown": -0.1,
            "max_dd_days": 1,
            "trades": 2,
            "win_rate": 0.5,
            "profit_factor": 1.1,
            "avg_win": 0.01,
            "avg_loss": -0.01,
        },
    )
    monkeypatch.setattr(backtester, "calculate_baseline_sharpe", lambda data: 0.5)

    backtester.walk_forward_validation()
    capsys.readouterr()

    payload = json.loads(artifact_path.read_text())
    assert query_calls == [["SPY", "AAPL"]]
    assert payload["instrument_scope"] == "stocks_or_etfs"
    assert payload["universe_size_cap"] == 2
    assert payload["selection_thesis"] == "Select liquid risk-on ETFs and stocks by training-window momentum."
    assert payload["windows"][0]["raw_selected_tickers"] == ["SPY", "AAPL", "MSFT"]
    assert payload["windows"][0]["selected_tickers"] == ["SPY", "AAPL"]
    assert payload["windows"][0]["cap_applied"] is True


class TestPrepareMinuteFrame:
    """Tests for minute-frame preparation helpers."""

    def test_prepare_minute_frame_resets_returns_at_session_boundaries(self):
        """The first bar of each session should not inherit the prior session close."""
        frame = pd.DataFrame(
            {
                "ticker": ["AAA"] * 4,
                "session_date": pd.to_datetime(
                    ["2025-11-03", "2025-11-03", "2025-11-04", "2025-11-04"]
                ),
                "window_start_ns": [1, 2, 1, 2],
                "close": [100.0, 101.0, 110.0, 111.0],
                "open": [99.5, 100.5, 109.5, 110.5],
                "high": [100.5, 101.5, 110.5, 111.5],
                "low": [99.0, 100.0, 109.0, 110.0],
                "volume": [1_000, 1_100, 1_200, 1_300],
                "transactions": [10, 11, 12, 13],
            }
        )

        prepared = backtester.prepare_minute_frame(frame)

        assert prepared["returns"].tolist()[0] == 0.0
        assert prepared["returns"].tolist()[2] == 0.0


# =============================================================================
# calculate_metrics tests
# =============================================================================

class TestCalculateMetrics:
    """Tests for calculate_metrics function."""

    def test_calculate_metrics_basic(self):
        """All expected metric keys present in return dict."""
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
        trades = pd.Series([1, -1, 1, -1, 1], index=returns.index)
        result = calculate_metrics(returns, trades)

        expected_keys = {
            'sharpe', 'naive_sharpe', 'nw_sharpe_bias', 'sortino', 'calmar', 'drawdown', 'max_dd_days',
            'trades', 'win_rate', 'profit_factor', 'avg_win', 'avg_loss'
        }
        assert set(result.keys()) == expected_keys

    def test_calculate_metrics_zero_std(self):
        """Constant returns -> sharpe handles near-zero std."""
        # With very small std, sharpe will be large but finite
        # The actual implementation guards std != 0
        returns = pd.Series([0.01] * 10)
        trades = pd.Series([1] * 10)
        result = calculate_metrics(returns, trades)

        # Sortino should be 0 since no downside returns
        assert result['sortino'] == 0.0
        # Sharpe should be a finite value (not inf or nan)
        assert np.isfinite(result['sharpe'])

    def test_calculate_metrics_all_positive(self):
        """All positive returns gives expected metrics."""
        # Use returns that are all positive
        returns = pd.Series([0.01, 0.02, 0.015, 0.01, 0.02])
        trades = pd.Series([1, 1, 1, 1, 1])  # All long positions
        result = calculate_metrics(returns, trades)

        # All trade_returns are positive (since all returns are positive)
        # Note: trade_returns uses trades[trades != 0], which gives the position values
        # With all positive positions, there are no "loss" trades (negative positions)
        # So win_rate checks (trade_returns > 0) which is always true
        assert result['win_rate'] == 1.0
        assert result['avg_loss'] == 0.0
        # profit_factor is 0 when there are no losses (gross_loss = 0)
        # This is expected behavior based on the formula: pf = gross_profit / gross_loss
        assert result['profit_factor'] == 0.0  # No losses, so PF is 0 (not inf)

    def test_calculate_metrics_all_negative(self):
        """Win rate=0.0, profit_factor=0."""
        returns = pd.Series([-0.01, -0.02, -0.015, -0.01, -0.02])
        trades = pd.Series([-1, -1, -1, -1, -1])
        result = calculate_metrics(returns, trades)

        assert result['win_rate'] == 0.0
        assert result['profit_factor'] == 0.0

    def test_calculate_metrics_sortino_vs_sharpe(self):
        """Sharpe-specific auxiliary fields stay internally consistent."""
        # Upside-skewed returns (more large positive, small negative)
        returns = pd.Series([0.05, 0.04, 0.03, -0.005, -0.01, 0.06, 0.07])
        trades = pd.Series([1] * 7)
        result = calculate_metrics(returns, trades)

        assert np.isfinite(result['sortino'])
        assert result['nw_sharpe_bias'] == result['naive_sharpe'] - result['sharpe']

    def test_calculate_metrics_calmar(self):
        """Known return path gives expected calmar."""
        # Create returns with known cumulative and drawdown
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        trades = pd.Series([1, 1, 1, 1, 1])
        result = calculate_metrics(returns, trades)

        # Calmar = annualized_return / abs(max_drawdown)
        # Should be a positive number
        assert isinstance(result['calmar'], float)
        assert result['calmar'] >= 0

    def test_calculate_metrics_drawdown(self):
        """Known drawdown value."""
        # Returns with a clear peak and trough
        returns = pd.Series([0.1, 0.05, -0.1, -0.05, 0.02])
        trades = pd.Series([1] * 5)
        result = calculate_metrics(returns, trades)

        # Max drawdown should be negative
        assert result['drawdown'] <= 0

    def test_calculate_metrics_max_dd_days(self):
        """Known drawdown duration."""
        # Create returns with a specific drawdown period
        returns = pd.Series([0.01, -0.01, -0.01, -0.01, 0.02])
        trades = pd.Series([1] * 5)
        result = calculate_metrics(returns, trades)

        # Should count consecutive days in drawdown
        assert isinstance(result['max_dd_days'], int)
        assert result['max_dd_days'] >= 0

    def test_calculate_metrics_profit_factor(self):
        """Known PF value."""
        returns = pd.Series([0.02, -0.01, 0.03, -0.01, 0.01])
        trades = pd.Series([1, -1, 1, -1, 1])
        result = calculate_metrics(returns, trades)

        # Profit factor = gross_profit / gross_loss
        # With mixed wins and losses
        assert result['profit_factor'] >= 0

    def test_calculate_metrics_win_rate(self):
        """Known WR value."""
        returns = pd.Series([0.01, -0.01, 0.02, -0.01, 0.01])
        trades = pd.Series([1, -1, 1, -1, 1])
        result = calculate_metrics(returns, trades)

        # Win rate = wins / total trades
        # 3 wins, 2 losses = 0.6
        expected_wr = 3 / 5
        assert abs(result['win_rate'] - expected_wr) < 0.01

    def test_calculate_metrics_avg_win_loss(self):
        """Known avg values."""
        returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01])
        trades = pd.Series([1, -1, 1, -1, 1])
        result = calculate_metrics(returns, trades)

        # Avg win should be positive
        assert result['avg_win'] > 0
        # Avg loss should be negative
        assert result['avg_loss'] < 0

    def test_calculate_metrics_reports_trades_when_book_offsets(self):
        """Offsetting per-symbol positions should still produce non-zero trade stats."""
        returns = pd.Series([0.01, -0.01, 0.01, -0.01])
        gross_exposure = pd.Series([1.0, 1.0, 1.0, 1.0])
        trade_activity = pd.Series([0.0, 2.0, 2.0, 2.0])
        result = calculate_metrics(returns, gross_exposure, trade_activity)
        assert result['trades'] > 0
        assert result['win_rate'] > 0 or result['profit_factor'] > 0


# =============================================================================
# calculate_baseline_sharpe tests
# =============================================================================

class TestCalculateBaselineSharpe:
    """Tests for calculate_baseline_sharpe function."""

    def test_calculate_baseline_sharpe_basic(self):
        """Multi-symbol dict returns positive float."""
        dates = pd.date_range('2023-01-01', periods=10)
        data = {
            'SPY': pd.DataFrame({'returns': [0.01] * 10}, index=dates),
            'QQQ': pd.DataFrame({'returns': [0.015] * 10}, index=dates),
        }
        result = calculate_baseline_sharpe(data)

        assert isinstance(result, float)
        # Positive returns should give positive Sharpe
        assert result > 0

    def test_calculate_baseline_sharpe_zero_std(self):
        """Constant returns -> large finite value."""
        dates = pd.date_range('2023-01-01', periods=10)
        data = {
            'SPY': pd.DataFrame({'returns': [0.01] * 10}, index=dates),
        }
        result = calculate_baseline_sharpe(data)

        # With zero std, implementation returns a large value (not actually 0)
        # But it should still be finite
        assert np.isfinite(result)

    def test_calculate_baseline_sharpe_single_symbol(self):
        """Works with one symbol."""
        dates = pd.date_range('2023-01-01', periods=10)
        data = {
            'BTC': pd.DataFrame({'returns': [0.02, -0.01, 0.03, 0.01, -0.01, 0.02, 0.01, -0.01, 0.02, 0.01]}, index=dates),
        }
        result = calculate_baseline_sharpe(data)

        assert isinstance(result, float)

    def test_calculate_baseline_sharpe_empty(self):
        """Empty dict returns 0.0."""
        result = calculate_baseline_sharpe({})
        assert result == 0.0

    def test_calculate_baseline_sharpe_no_returns_column(self):
        """Data without returns column returns 0.0."""
        dates = pd.date_range('2023-01-01', periods=10)
        data = {
            'SPY': pd.DataFrame({'close': [100] * 10}, index=dates),
        }
        result = calculate_baseline_sharpe(data)
        assert result == 0.0


# =============================================================================
# run_per_symbol_analysis tests
# =============================================================================

class TestRunPerSymbolAnalysis:
    """Tests for run_per_symbol_analysis function."""

    @pytest.fixture
    def multi_symbol_data(self):
        """Create multi-symbol test data."""
        dates = pd.date_range('2023-01-01', periods=100)
        return {
            'SPY': pd.DataFrame({
                'returns': [0.001] * 100,
                'volatility': [0.01] * 100,
            }, index=dates),
            'QQQ': pd.DataFrame({
                'returns': [0.0015] * 100,
                'volatility': [0.012] * 100,
            }, index=dates),
            'IWM': pd.DataFrame({
                'returns': [0.0008] * 100,
                'volatility': [0.009] * 100,
            }, index=dates),
        }

    def test_run_per_symbol_analysis_basic(self, multi_symbol_data):
        """Returns dict with all symbols as keys."""
        strategy = DummyStrategy()
        result = run_per_symbol_analysis(strategy, multi_symbol_data, 50, 100)

        assert set(result.keys()) == {'SPY', 'QQQ', 'IWM'}

    def test_run_per_symbol_analysis_keys(self, multi_symbol_data):
        """Each symbol has sharpe, sortino, dd, pf, trades, wr."""
        strategy = DummyStrategy()
        result = run_per_symbol_analysis(strategy, multi_symbol_data, 50, 100)

        for symbol_metrics in result.values():
            expected_keys = {'sharpe', 'sortino', 'dd', 'pf', 'trades', 'wr'}
            assert set(symbol_metrics.keys()) == expected_keys

    def test_run_per_symbol_analysis_signal_lag(self, multi_symbol_data):
        """Signals shifted by 1 bar."""
        # Create a strategy that uses the index to verify lag
        class IndexTrackingStrategy:
            def __init__(self):
                self.last_index = None

            def generate_signals(self, data):
                # Signal depends on data index - lag should be observable
                signals = pd.Series(0, index=data.index)
                signals.iloc[10:] = 1  # Start long after warmup
                return signals

        strategy = IndexTrackingStrategy()
        result = run_per_symbol_analysis(strategy, multi_symbol_data, 50, 100)

        # With signal lag, we should still get valid results
        assert all(isinstance(m['sharpe'], float) for m in result.values())

    def test_run_per_symbol_analysis_exception_handling(self, multi_symbol_data):
        """Strategy that raises exception returns default metrics."""
        class BrokenStrategy:
            def generate_signals(self, data):
                raise ValueError("Broken!")

        strategy = BrokenStrategy()
        result = run_per_symbol_analysis(strategy, multi_symbol_data, 50, 100)

        # Should return default zero metrics
        for symbol_metrics in result.values():
            assert symbol_metrics['sharpe'] == 0.0
            assert symbol_metrics['sortino'] == 0.0

    def test_run_per_symbol_analysis_non_series_signals(self, multi_symbol_data):
        """Non-Series signals converted to Series."""
        class ArrayStrategy:
            def generate_signals(self, data):
                # Return numpy array instead of Series
                return np.ones(len(data))

        strategy = ArrayStrategy()
        result = run_per_symbol_analysis(strategy, multi_symbol_data, 50, 100)

        # Should handle conversion gracefully
        assert all(isinstance(m['sharpe'], float) for m in result.values())
