"""Unit tests for dynamic strategy loading and strategy interface.

Tests cover:
- Dynamic loading of strategy classes with custom names
- Free-form strategy file structure (no EDITABLE REGION)
- Strategy interface compliance
"""

import pytest
import pandas as pd
import numpy as np
import ast
import os
from pathlib import Path

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safer_getattr, full_write_guard
from RestrictedPython.Eval import default_guarded_getiter, default_guarded_getitem

from core.backtester import StrategyContractError, find_strategy_class, security_check, validate_strategy_class_contract
import strategies.active_strategy


def build_minute_frame(ticker: str, closes: list[float]) -> pd.DataFrame:
    """Build a minute-bar frame matching the Sprint 2 schema."""
    row_count = len(closes)
    return pd.DataFrame(
        {
            "ticker": [ticker] * row_count,
            "session_date": pd.to_datetime(["2025-11-03"] * row_count),
            "window_start_ns": np.arange(row_count, dtype=np.int64) * 60_000_000_000,
            "open": np.array(closes, dtype=float) - 0.1,
            "high": np.array(closes, dtype=float) + 0.2,
            "low": np.array(closes, dtype=float) - 0.2,
            "close": np.array(closes, dtype=float),
            "volume": np.linspace(1_000, 2_000, row_count),
            "transactions": np.arange(1, row_count + 1),
        }
    )


def build_spy_regime_daily_frame() -> pd.DataFrame:
    """Build daily data where SPY ends in a bear-volatile state."""
    sessions = pd.bdate_range("2024-01-01", periods=25)
    closes = []
    price = 100.0
    for idx in range(len(sessions)):
        drift = -0.6
        shock = 2.5 if idx % 2 == 0 else -2.3
        price = price + drift + shock
        closes.append(price)

    rows = []
    for session, close in zip(sessions, closes):
        rows.append(
            {
                "ticker": "SPY",
                "session_date": session,
                "open": close - 0.4,
                "high": close + 0.5,
                "low": close - 0.7,
                "close": close,
                "volume": 10_000_000,
                "transactions": 1_000,
                "vwap": close - 0.1,
            }
        )
        rows.append(
            {
                "ticker": "AAA",
                "session_date": session,
                "open": 20.0,
                "high": 20.5,
                "low": 19.5,
                "close": 20.2,
                "volume": 2_000,
                "transactions": 20,
                "vwap": 20.1,
            }
        )
        rows.append(
            {
                "ticker": "BBB",
                "session_date": session,
                "open": 30.0,
                "high": 30.5,
                "low": 29.5,
                "close": 30.2,
                "volume": 1_500,
                "transactions": 30,
                "vwap": 30.1,
            }
        )

    return pd.DataFrame(rows)


def build_neutral_daily_frame() -> pd.DataFrame:
    """Build daily data without SPY so the strategy falls back to a neutral regime."""
    return pd.DataFrame(
        {
            "ticker": ["AAA", "AAA", "BBB", "BBB"],
            "session_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]),
            "open": [10.0, 10.0, 20.0, 20.0],
            "high": [10.5, 10.5, 20.5, 20.5],
            "low": [9.5, 9.5, 19.5, 19.5],
            "close": [10.2, 10.3, 20.2, 20.3],
            "volume": [1_000, 1_200, 900, 1_100],
            "transactions": [10, 12, 9, 11],
            "vwap": [10.1, 10.2, 20.1, 20.2],
        }
    )


def build_confirmation_minute_data() -> dict[str, pd.DataFrame]:
    """Build trending minute frames long enough to test confirmation windows."""
    return {
        "AAPL": build_minute_frame("AAPL", list(range(100, 130))),
        "MSFT": build_minute_frame("MSFT", list(range(200, 170, -1))),
    }


def build_whipsaw_minute_frame(ticker: str) -> pd.DataFrame:
    """Build a frame that confirms long, goes flat on a brief contradiction, then confirms short."""
    closes = list(range(100, 123)) + [80, 79, 78, 110, 111]
    return build_minute_frame(ticker, closes)


def build_hold_minute_frame(ticker: str) -> pd.DataFrame:
    """Build a frame that confirms long, then quickly confirms short while hold should still apply."""
    closes = list(range(100, 123)) + [80, 79, 78, 77, 76, 75, 74]
    return build_minute_frame(ticker, closes)


def build_low_magnitude_trend_frame(ticker: str, start: float, end: float, periods: int = 30) -> pd.DataFrame:
    """Build a gentle trend where absolute momentum is directional but percent change stays small."""
    closes = np.linspace(start, end, periods).tolist()
    return build_minute_frame(ticker, closes)


def build_leader_daily_frame() -> pd.DataFrame:
    """Build deterministic daily bars for the Phase 4 hot-leader ranking heuristic."""
    sessions = pd.date_range("2024-01-01", periods=21, freq="B")
    specs = {
        "MOMO": {"start": 10.0, "end": 18.0, "volume": 900_000, "range_pct": 0.070},
        "DOLLAR": {"start": 20.0, "end": 36.0, "volume": 2_000_000, "range_pct": 0.080},
        "ALPHA": {"start": 8.0, "end": 11.0, "volume": 1_500_000, "range_pct": 0.060},
        "BETA": {"start": 12.0, "end": 16.5, "volume": 1_000_000, "range_pct": 0.060},
        "SLOW": {"start": 40.0, "end": 42.0, "volume": 5_000_000, "range_pct": 0.055},
        "LOWADR": {"start": 30.0, "end": 39.0, "volume": 6_000_000, "range_pct": 0.030},
        "FALL": {"start": 50.0, "end": 45.0, "volume": 9_000_000, "range_pct": 0.090},
        "OLD": {"start": 5.0, "end": 15.0, "volume": 10_000_000, "range_pct": 0.100},
    }
    rows = []
    for ticker, spec in specs.items():
        ticker_sessions = sessions[:-1] if ticker == "OLD" else sessions
        closes = np.linspace(spec["start"], spec["end"], len(ticker_sessions))
        for session, close in zip(ticker_sessions, closes):
            half_range = close * spec["range_pct"] / 2.0
            rows.append(
                {
                    "ticker": ticker,
                    "session_date": session,
                    "open": close * 0.99,
                    "high": close + half_range,
                    "low": close - half_range,
                    "close": close,
                    "volume": spec["volume"],
                    "transactions": 100,
                    "vwap": close,
                }
            )
    return pd.DataFrame(rows)


def build_orh_minute_frame(
    ticker: str,
    closes: list[float],
    highs: list[float],
    lows: list[float],
) -> pd.DataFrame:
    """Build a minute frame with explicit OHLC values for ORH/stop/EMA tests."""
    row_count = len(closes)
    start = pd.Timestamp("2024-05-14 09:30")
    timestamps = pd.date_range(start, periods=row_count, freq="min")
    return pd.DataFrame(
        {
            "ticker": [ticker] * row_count,
            "session_date": pd.to_datetime([start.date()] * row_count),
            "window_start_ns": timestamps.view("int64"),
            "open": np.array(closes, dtype=float),
            "high": np.array(highs, dtype=float),
            "low": np.array(lows, dtype=float),
            "close": np.array(closes, dtype=float),
            "volume": np.linspace(10_000, 20_000, row_count),
            "transactions": np.arange(1, row_count + 1),
        }
    )


# =============================================================================
# Dynamic loading tests
# =============================================================================

class TestDynamicLoading:
    """Tests for dynamic strategy class loading."""

    def test_free_form_class_accepted(self):
        """Custom class name is discoverable before strict contract validation."""
        # Create a custom strategy class
        class MomentumStrategy:
            def generate_signals(self, data):
                return pd.Series(1, index=data.index)

        sandbox_locals = {'MomentumStrategy': MomentumStrategy}
        strategy_class = find_strategy_class(sandbox_locals)

        assert strategy_class is MomentumStrategy
        assert strategy_class.__name__ == 'MomentumStrategy'
        with pytest.raises(StrategyContractError, match="select_universe"):
            validate_strategy_class_contract(strategy_class)

    def test_custom_class_name(self):
        """'MomentumStrategy' loads correctly."""
        class MomentumStrategy:
            def __init__(self, period=20):
                self.period = period

            def generate_signals(self, data):
                return pd.Series(1, index=data.index)

        sandbox_locals = {
            'MomentumStrategy': MomentumStrategy,
            'TradingStrategy': None,
        }
        strategy_class = find_strategy_class(sandbox_locals)

        assert strategy_class is MomentumStrategy
        assert strategy_class.__name__ == 'MomentumStrategy'
        with pytest.raises(StrategyContractError, match="select_universe"):
            validate_strategy_class_contract(strategy_class)

    def test_multiple_methods_allowed(self):
        """Class with both hooks passes strict contract validation."""
        class ComplexStrategy:
            def __init__(self):
                self.param = 10

            def _helper_method(self, data):
                """Private helper method."""
                return data.mean()

            def another_method(self, x):
                """Another public method."""
                return x * 2

            def select_universe(self, daily_data):
                return ['AAPL']

            def generate_signals(self, data):
                signals = pd.Series(0, index=data.index)
                signals.iloc[10:] = 1
                return signals

        sandbox_locals = {'ComplexStrategy': ComplexStrategy}
        strategy_class = find_strategy_class(sandbox_locals)

        assert strategy_class is ComplexStrategy
        assert hasattr(strategy_class, 'generate_signals')
        assert hasattr(strategy_class, '_helper_method')
        assert hasattr(strategy_class, 'another_method')
        assert validate_strategy_class_contract(strategy_class) is ComplexStrategy

    def test_no_generate_signals_rejected(self):
        """Class without generate_signals returns None."""
        class IncompleteStrategy:
            def __init__(self):
                pass

            def some_other_method(self, data):
                return data

        sandbox_locals = {'IncompleteStrategy': IncompleteStrategy}
        strategy_class = find_strategy_class(sandbox_locals)

        assert strategy_class is None
        with pytest.raises(StrategyContractError, match="generate_signals"):
            validate_strategy_class_contract(strategy_class)

    def test_non_class_with_generate_signals_ignored(self):
        """Function named generate_signals ignored."""
        def generate_signals(data):
            return pd.Series(1, index=data.index)

        class ValidStrategy:
            def generate_signals(self, data):
                return pd.Series(1, index=data.index)

        sandbox_locals = {
            'generate_signals': generate_signals,  # Function, not class
            'ValidStrategy': ValidStrategy,
        }
        strategy_class = find_strategy_class(sandbox_locals)

        # Should find ValidStrategy, not the function
        assert strategy_class is ValidStrategy
        with pytest.raises(StrategyContractError, match="select_universe"):
            validate_strategy_class_contract(strategy_class)


# =============================================================================
# Strategy file tests
# =============================================================================

class TestStrategyFile:
    """Tests for active_strategy.py file structure and content."""

    @pytest.fixture
    def strategy_file_path(self):
        """Path to active_strategy.py."""
        return Path(__file__).parent.parent.parent / 'src' / 'strategies' / 'active_strategy.py'

    def test_editable_region_removed(self, strategy_file_path):
        """No EDITABLE REGION in active_strategy.py."""
        content = strategy_file_path.read_text()

        assert 'EDITABLE REGION BREAK' not in content
        assert 'EDITABLE REGION END' not in content

    def test_strategy_file_exists(self, strategy_file_path):
        """Strategy file exists at expected location."""
        assert strategy_file_path.exists()

    def test_strategy_file_valid_python(self, strategy_file_path):
        """Strategy file is valid Python syntax."""
        content = strategy_file_path.read_text()

        # Should parse without errors
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"active_strategy.py has syntax error: {e}")

    def test_strategy_has_trading_strategy_class(self, strategy_file_path):
        """File contains TradingStrategy class."""
        content = strategy_file_path.read_text()
        tree = ast.parse(content)

        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert 'TradingStrategy' in classes

    def test_trading_strategy_has_generate_signals(self, strategy_file_path):
        """TradingStrategy class has generate_signals method."""
        content = strategy_file_path.read_text()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'TradingStrategy':
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert 'generate_signals' in methods
                return

        pytest.fail("TradingStrategy class not found")

    def test_trading_strategy_has_select_universe(self, strategy_file_path):
        """TradingStrategy class exposes select_universe."""
        content = strategy_file_path.read_text()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'TradingStrategy':
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert 'select_universe' in methods
                return

        pytest.fail("TradingStrategy class not found")

    def test_strategy_has_imports(self, strategy_file_path):
        """File has pandas and numpy imports."""
        content = strategy_file_path.read_text()

        # Check for import statements
        assert 'import pandas' in content or 'import pd' in content
        assert 'import numpy' in content or 'import np' in content

    def test_strategy_in_sandbox(self, strategy_file_path):
        """active_strategy.py compiles in RestrictedPython."""
        content = strategy_file_path.read_text()

        # Strip import statements for restricted execution (same as backtester does)
        sanitized_lines = []
        for line in content.split('\n'):
            if not (line.strip().startswith("import ") or line.strip().startswith("from ")):
                sanitized_lines.append(line)
        sanitized_code = '\n'.join(sanitized_lines)

        # Define restricted environment - include __build_class__ for class definitions
        safe_builtins = {
            '__build_class__': __builtins__['__build_class__'],
            '_write_': lambda x: x,
            '_getattr_': safer_getattr,
        }
        safe_globals = {
            '__builtins__': safe_builtins,
            '_getattr_': safer_getattr,
            '_write_': lambda x: x,
            '_getiter_': default_guarded_getiter,
            '_getitem_': default_guarded_getitem,
            '__name__': 'sandbox',
            '__metaclass__': type,
            'pd': pd,
            'np': np,
        }

        # Should compile without errors
        try:
            byte_code = compile_restricted(sanitized_code, filename='active_strategy.py', mode='exec')
            sandbox_locals = {}
            exec(byte_code, safe_globals, sandbox_locals)
        except Exception as e:
            pytest.fail(f"active_strategy.py failed to compile in RestrictedPython: {e}")

    def test_active_strategy_passes_security_check(self, strategy_file_path):
        """The default strategy file should pass the AST security guard."""
        is_safe, msg = security_check(str(strategy_file_path))

        assert is_safe
        assert msg == ""

    def test_active_strategy_discovery_reports_universe_support(self, strategy_file_path):
        """The real TradingStrategy example is discoverable and reports select_universe support."""
        content = strategy_file_path.read_text()

        sanitized_lines = []
        for line in content.split('\n'):
            if not (line.strip().startswith("import ") or line.strip().startswith("from ")):
                sanitized_lines.append(line)
        sanitized_code = '\n'.join(sanitized_lines)

        safe_builtins = {
            '__build_class__': __builtins__['__build_class__'],
            '_write_': lambda x: x,
            '_getattr_': safer_getattr,
        }
        safe_globals = {
            '__builtins__': safe_builtins,
            '_getattr_': safer_getattr,
            '_write_': lambda x: x,
            '_getiter_': default_guarded_getiter,
            '_getitem_': default_guarded_getitem,
            '__name__': 'sandbox',
            '__metaclass__': type,
            'pd': pd,
            'np': np,
        }

        byte_code = compile_restricted(sanitized_code, filename='active_strategy.py', mode='exec')
        sandbox_locals = {}
        exec(byte_code, safe_globals, sandbox_locals)

        strategy_class = find_strategy_class(sandbox_locals)

        assert strategy_class is not None
        assert strategy_class.__name__ == 'TradingStrategy'
        assert validate_strategy_class_contract(strategy_class) is strategy_class

    def test_strategy_returns_signal_dict(self, strategy_file_path):
        """generate_signals returns one signal Series per ticker."""
        from strategies.active_strategy import TradingStrategy

        minute_data = {
            "AAPL": build_minute_frame("AAPL", np.linspace(100, 110, 80).tolist()),
            "MSFT": build_minute_frame("MSFT", np.linspace(210, 195, 60).tolist()),
        }

        strategy = TradingStrategy()
        signals = strategy.generate_signals(minute_data)

        assert isinstance(signals, dict)
        assert set(signals.keys()) == {"AAPL", "MSFT"}
        assert all(isinstance(series, pd.Series) for series in signals.values())

    def test_strategy_signal_indexes_align_with_minute_frames(self, strategy_file_path):
        """Each returned Series stays aligned with its ticker frame index."""
        from strategies.active_strategy import TradingStrategy

        minute_data = {
            "AAPL": build_minute_frame("AAPL", np.linspace(100, 110, 80).tolist()),
            "MSFT": build_minute_frame("MSFT", np.linspace(210, 195, 60).tolist()),
        }

        strategy = TradingStrategy()
        signals = strategy.generate_signals(minute_data)

        for ticker, frame in minute_data.items():
            assert signals[ticker].index.equals(frame.index)
            assert len(signals[ticker]) == len(frame)

    def test_strategy_signal_range(self, strategy_file_path):
        """Minute-mode signals stay in {-1, 0, 1}."""
        from strategies.active_strategy import TradingStrategy

        minute_data = {
            "AAPL": build_minute_frame("AAPL", np.linspace(100, 110, 80).tolist()),
            "MSFT": build_minute_frame("MSFT", np.linspace(210, 195, 60).tolist()),
        }

        strategy = TradingStrategy()
        signals = strategy.generate_signals(minute_data)

        for ticker_signals in signals.values():
            unique_values = set(ticker_signals.dropna().unique())
            for val in unique_values:
                assert val in {-1.0, 0.0, 1.0}, f"Unexpected signal value: {val}"

    def test_select_universe_ranks_latest_hot_leaders(self, strategy_file_path):
        """Phase 4 universe selection ranks latest active hot leaders by return, dollar volume, and ticker."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy()
        universe = strategy.select_universe(build_leader_daily_frame())

        assert universe[:4] == ["DOLLAR", "MOMO", "ALPHA", "BETA"]
        assert universe.index("ALPHA") < universe.index("BETA")
        assert "SLOW" in universe
        assert "LOWADR" not in universe
        assert "FALL" not in universe
        assert "OLD" not in universe
        assert all(isinstance(ticker, str) for ticker in universe)

    def test_select_universe_excludes_tickers_missing_latest_session(self, strategy_file_path):
        """Phase 4 only considers tickers active in the latest daily session."""
        from strategies.active_strategy import TradingStrategy

        daily_data = build_leader_daily_frame()
        strategy = TradingStrategy()
        universe = strategy.select_universe(daily_data)

        latest_session = daily_data["session_date"].max()
        latest_tickers = set(daily_data.loc[daily_data["session_date"] == latest_session, "ticker"])

        assert set(universe).issubset(latest_tickers)
        assert "OLD" not in universe

    def test_generate_signals_enters_long_on_orh_breakout_after_opening_range(self, strategy_file_path):
        """Phase 4 enters long only after an opening-range-high close above the 9 EMA."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "ORH",
            closes=[10.00, 10.05, 10.00, 10.10, 10.00, 10.35, 10.45, 10.55],
            highs=[10.20, 10.25, 10.15, 10.30, 10.20, 10.45, 10.55, 10.65],
            lows=[9.80, 9.85, 9.82, 9.88, 9.84, 10.25, 10.35, 10.45],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"ORH": frame})

        series = signals["ORH"]
        assert series.iloc[: strategy.opening_range_bars].eq(0.0).all()
        assert series.iloc[strategy.opening_range_bars] == 1.0
        assert series.iloc[-1] == 1.0

    def test_generate_signals_hard_stop_flattens_at_opening_range_low(self, strategy_file_path):
        """After ORH entry, a low breach of the setup low flattens the long."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "STOP",
            closes=[10.00, 10.05, 10.00, 10.10, 10.00, 10.35, 10.45, 10.40, 9.85],
            highs=[10.20, 10.25, 10.15, 10.30, 10.20, 10.45, 10.55, 10.50, 9.95],
            lows=[9.80, 9.85, 9.82, 9.88, 9.84, 10.25, 10.35, 10.30, 9.75],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"STOP": frame})
        trace = strategy.get_signal_trace()

        series = signals["STOP"]
        assert series.iloc[5] == 1.0
        assert series.iloc[6] == 1.0
        assert series.iloc[7] == 1.0
        assert series.iloc[8] == 0.0

        assert trace["schema_version"] == "martinluk_public_signal_trace_v1"
        assert trace["replication_target"] == "public_operation_reproducibility"
        assert len(trace["signals"]) == 1
        signal = trace["signals"][0]
        assert signal["symbol"] == "STOP"
        assert signal["setup_type"] == "leader_pullback_orh"
        assert signal["entry_trigger"] == "opening_range_high_breakout"
        assert signal["entry_type"] == "opening_range_high_breakout"
        assert signal["trim_type"] == "no_partial_trim_phase4"
        assert signal["exit_type"] == "hard_stop"
        assert signal["mae_unit"] == "R"
        assert signal["mfe_unit"] == "R"
        assert signal["stop_width_pct"] > 0.0
        assert signal["holding_period_bars"] == 4

    def test_generate_signals_exits_on_9ema_close_break(self, strategy_file_path):
        """If the hard stop is not hit, a close below the 9 EMA flattens the long."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "EMA",
            closes=[10.00, 10.05, 10.00, 10.10, 10.00, 10.35, 11.20, 11.30, 10.20],
            highs=[10.20, 10.25, 10.15, 10.30, 10.20, 10.45, 11.35, 11.40, 10.30],
            lows=[9.80, 9.85, 9.82, 9.88, 9.84, 10.25, 11.05, 11.20, 10.15],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"EMA": frame})
        trace = strategy.get_signal_trace()

        series = signals["EMA"]
        assert series.iloc[5] == 1.0
        assert series.iloc[6] == 1.0
        assert series.iloc[7] == 1.0
        assert series.iloc[8] == 0.0
        assert trace["signals"][0]["exit_type"] == "nine_ema_close_break"
        assert trace["signals"][0]["trim_type"] == "no_partial_trim_phase4"

    def test_generate_signals_rejects_long_support_touch_without_breakout(self, strategy_file_path):
        """A leader support touch alone is not a long entry without ORH/range-high confirmation."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "TOUCH",
            closes=[10.00, 10.05, 10.00, 10.10, 10.00, 10.02, 10.08, 10.12],
            highs=[10.20, 10.25, 10.15, 10.30, 10.20, 10.18, 10.22, 10.25],
            lows=[9.80, 9.85, 9.82, 9.88, 9.84, 9.90, 9.96, 10.00],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"TOUCH": frame})

        assert signals["TOUCH"].eq(0.0).all()
        assert strategy.get_signal_trace()["signals"] == []

    def test_generate_signals_enters_short_on_declining_ema_resistance_rejection(self, strategy_file_path):
        """Short v1 enters only after a declining-EMA resistance bounce fails through range support."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "SHRT",
            closes=[10.00, 9.90, 9.80, 9.70, 9.60, 9.45, 9.35, 9.25],
            highs=[10.10, 10.00, 9.90, 9.80, 9.70, 9.78, 9.48, 9.38],
            lows=[9.90, 9.80, 9.70, 9.60, 9.50, 9.40, 9.25, 9.15],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"SHRT": frame})
        trace = strategy.get_signal_trace()

        series = signals["SHRT"]
        assert series.iloc[: strategy.opening_range_bars].eq(0.0).all()
        assert series.iloc[5] == -1.0
        assert series.iloc[-1] == -1.0

        assert len(trace["signals"]) == 1
        signal = trace["signals"][0]
        assert signal["symbol"] == "SHRT"
        assert signal["direction"] == "short"
        assert signal["setup_type"] == "declining_ema_avwap_bounce_short"
        assert signal["entry_trigger"] == "resistance_rejection_breakdown"
        assert signal["entry_type"] == "resistance_rejection_breakdown"
        assert signal["trim_type"] == "quick_swing_cover_v1"
        assert signal["exit_type"] == "open"
        assert signal["r_multiple"] is None
        assert signal["mae_unit"] == "R"
        assert signal["mfe_unit"] == "R"
        assert signal["stop_width_pct"] > 0.0
        assert "diagnostics" not in signal

    def test_generate_signals_rejects_short_without_failure_trigger(self, strategy_file_path):
        """A bounce into resistance is not a short entry until price fails through support."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "NOFAIL",
            closes=[10.00, 9.90, 9.80, 9.70, 9.60, 9.55, 9.58, 9.56],
            highs=[10.10, 10.00, 9.90, 9.80, 9.70, 9.78, 9.76, 9.74],
            lows=[9.90, 9.80, 9.70, 9.60, 9.50, 9.52, 9.50, 9.51],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"NOFAIL": frame})

        assert signals["NOFAIL"].eq(0.0).all()
        assert strategy.get_signal_trace()["signals"] == []

    def test_generate_signals_short_hard_stop_trace_is_direction_aware(self, strategy_file_path):
        """Short hard stops use short-side risk math and direct validator-compatible fields."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "SSTOP",
            closes=[10.00, 9.90, 9.80, 9.70, 9.60, 9.45, 9.95],
            highs=[10.10, 10.00, 9.90, 9.80, 9.70, 9.78, 10.20],
            lows=[9.90, 9.80, 9.70, 9.60, 9.50, 9.40, 9.70],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"SSTOP": frame})
        trace = strategy.get_signal_trace()

        series = signals["SSTOP"]
        assert series.iloc[5] == -1.0
        assert series.iloc[6] == 0.0
        signal = trace["signals"][0]
        assert signal["direction"] == "short"
        assert signal["exit_type"] == "hard_stop"
        assert signal["r_multiple"] == pytest.approx(-1.0)
        assert signal["mae"] <= 0.0
        assert signal["mfe"] >= 0.0
        assert signal["holding_period_bars"] == 2

    def test_generate_signals_short_quick_cover_trace_is_validator_compatible(self, strategy_file_path):
        """Short quick-cover traces keep diagnostics on direct fields without profit claims."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "SCOV",
            closes=[10.00, 9.90, 9.80, 9.70, 9.60, 9.45, 8.85],
            highs=[10.10, 10.00, 9.90, 9.80, 9.70, 9.78, 9.00],
            lows=[9.90, 9.80, 9.70, 9.60, 9.50, 9.40, 8.70],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals({"SCOV": frame})
        trace = strategy.get_signal_trace()

        series = signals["SCOV"]
        assert series.iloc[5] == -1.0
        assert series.iloc[6] == 0.0
        signal = trace["signals"][0]
        assert signal["direction"] == "short"
        assert signal["exit_type"] == "support_cover"
        assert signal["r_multiple"] > 0.0
        for field in (
            "r_multiple",
            "mae",
            "mae_unit",
            "mfe",
            "mfe_unit",
            "stop_width_pct",
            "entry_type",
            "trim_type",
            "exit_type",
        ):
            assert field in signal
        assert "diagnostics" not in signal

    def test_generate_signals_keeps_validator_trace_side_band(self, strategy_file_path):
        """generate_signals keeps returning runtime Series while trace data is exposed through a getter."""
        from strategies.active_strategy import TradingStrategy

        frame = build_orh_minute_frame(
            "TRACE",
            closes=[10.00, 10.05, 10.00, 10.10, 10.00, 10.35, 10.45, 9.85],
            highs=[10.20, 10.25, 10.15, 10.30, 10.20, 10.45, 10.55, 9.95],
            lows=[9.80, 9.85, 9.82, 9.88, 9.84, 10.25, 10.35, 9.75],
        )

        strategy = TradingStrategy(max_stop_pct=10.0)
        signals = strategy.generate_signals(frame)
        trace = strategy.get_signal_trace()

        assert isinstance(signals, pd.Series)
        assert signals.index.equals(frame.index)
        assert isinstance(trace, dict)
        assert trace["signals"][0]["case_id"] == "PHASE4-TRACE-ORH"
        assert trace["signals"][0]["direction"] == "long"
        assert trace["signals"][0]["data_status"] == "available"
        assert "diagnostics" not in trace["signals"][0]

    def test_strategy_class_init(self, strategy_file_path):
        """TradingStrategy exposes bounded Phase 4 primitive parameters and trace state."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy()
        assert strategy.risk_per_trade_pct == pytest.approx(0.5)
        assert strategy.max_stop_pct == pytest.approx(2.5)
        assert strategy.opening_range_bars == 5
        assert strategy.ema_exit_period == 9
        assert strategy.leader_adr_min_pct == pytest.approx(5.0)
        assert strategy.get_signal_trace()["signals"] == []

        strategy_custom = TradingStrategy(
            risk_per_trade_pct=1.0,
            max_stop_pct=4.0,
            opening_range_bars=3,
            ema_exit_period=4,
            leader_adr_min_pct=6.5,
        )
        assert strategy_custom.risk_per_trade_pct == pytest.approx(1.0)
        assert strategy_custom.max_stop_pct == pytest.approx(4.0)
        assert strategy_custom.opening_range_bars == 3
        assert strategy_custom.ema_exit_period == 4
        assert strategy_custom.leader_adr_min_pct == pytest.approx(6.5)


# =============================================================================
# Free-form strategy tests (custom class names)
# =============================================================================

class TestFreeFormStrategies:
    """Tests for various free-form strategy implementations."""

    def test_custom_named_strategy_via_sandbox(self):
        """Custom class name loads correctly through sandbox."""
        # Simulate sandbox execution with custom class name
        strategy_code = """
class MyAlphaStrategy:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def select_universe(self, daily_data):
        return ['AAPL', 'MSFT']

    def generate_signals(self, data):
        signals = pd.Series(0, index=data.index)
        signals.iloc[10:] = 1
        return signals

class HelperClass:
    pass
"""

        # Include __build_class__ for class definition support
        safe_builtins = {
            '__build_class__': __builtins__['__build_class__'],
        }
        safe_globals = {
            '__builtins__': safe_builtins,
            '_getattr_': safer_getattr,
            '_write_': lambda x: x,
            '_getiter_': default_guarded_getiter,
            '_getitem_': default_guarded_getitem,
            '__name__': 'sandbox',
            '__metaclass__': type,
            'pd': pd,
            'np': np,
        }

        byte_code = compile_restricted(strategy_code, filename='test.py', mode='exec')
        sandbox_locals = {}
        exec(byte_code, safe_globals, sandbox_locals)

        strategy_class = find_strategy_class(sandbox_locals)

        assert strategy_class is not None
        assert strategy_class.__name__ == 'MyAlphaStrategy'
        assert validate_strategy_class_contract(strategy_class) is strategy_class

    def test_multiple_strategies_returns_first(self):
        """When multiple classes exist, a full two-hook class is preferred."""
        strategy_code = """
class StrategyA:
    def select_universe(self, daily_data):
        return ['AAPL']

    def generate_signals(self, data):
        return pd.Series(1, index=data.index)

class StrategyB:
    def generate_signals(self, data):
        return pd.Series(-1, index=data.index)
"""

        # Include __build_class__ for class definition support
        safe_builtins = {
            '__build_class__': __builtins__['__build_class__'],
        }
        safe_globals = {
            '__builtins__': safe_builtins,
            '_getattr_': safer_getattr,
            '_write_': lambda x: x,
            '_getiter_': default_guarded_getiter,
            '_getitem_': default_guarded_getitem,
            '__name__': 'sandbox',
            '__metaclass__': type,
            'pd': pd,
            'np': np,
        }

        byte_code = compile_restricted(strategy_code, filename='test.py', mode='exec')
        sandbox_locals = {}
        exec(byte_code, safe_globals, sandbox_locals)

        strategy_class = find_strategy_class(sandbox_locals)

        assert strategy_class is not None
        assert hasattr(strategy_class, 'generate_signals')
        assert strategy_class.__name__ == 'StrategyA'
        assert validate_strategy_class_contract(strategy_class) is strategy_class
