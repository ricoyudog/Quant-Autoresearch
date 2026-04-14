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

from core.backtester import find_strategy_class, security_check
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


# =============================================================================
# Dynamic loading tests
# =============================================================================

class TestDynamicLoading:
    """Tests for dynamic strategy class loading."""

    def test_free_form_class_accepted(self):
        """Custom class name works via find_strategy_class."""
        # Create a custom strategy class
        class MomentumStrategy:
            def generate_signals(self, data):
                return pd.Series(1, index=data.index)

        sandbox_locals = {'MomentumStrategy': MomentumStrategy}
        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        assert strategy_class is MomentumStrategy
        assert strategy_class.__name__ == 'MomentumStrategy'
        assert has_universe is False

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
        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        assert strategy_class is MomentumStrategy
        assert strategy_class.__name__ == 'MomentumStrategy'
        assert has_universe is False

    def test_multiple_methods_allowed(self):
        """Class with generate_signals + select_universe sets has_universe."""
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
        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        assert strategy_class is ComplexStrategy
        assert hasattr(strategy_class, 'generate_signals')
        assert hasattr(strategy_class, '_helper_method')
        assert hasattr(strategy_class, 'another_method')
        assert has_universe is True

    def test_no_generate_signals_rejected(self):
        """Class without generate_signals returns None."""
        class IncompleteStrategy:
            def __init__(self):
                pass

            def some_other_method(self, data):
                return data

        sandbox_locals = {'IncompleteStrategy': IncompleteStrategy}
        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        assert strategy_class is None
        assert has_universe is False

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
        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        # Should find ValidStrategy, not the function
        assert strategy_class is ValidStrategy
        assert has_universe is False


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

        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        assert strategy_class is not None
        assert strategy_class.__name__ == 'TradingStrategy'
        assert has_universe is True

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

    def test_select_universe_returns_ranked_ticker_list(self, strategy_file_path):
        """select_universe returns ticker strings ranked by average daily volume."""
        from strategies.active_strategy import TradingStrategy

        daily_data = pd.DataFrame(
            {
                'ticker': ['AAPL', 'MSFT', 'TSLA', 'AAPL', 'MSFT', 'TSLA'],
                'session_date': pd.to_datetime(
                    ['2024-01-02', '2024-01-02', '2024-01-02', '2024-01-03', '2024-01-03', '2024-01-03']
                ),
                'open': [100, 200, 300, 101, 201, 301],
                'high': [101, 201, 301, 102, 202, 302],
                'low': [99, 199, 299, 100, 200, 300],
                'close': [100.5, 200.5, 300.5, 101.5, 201.5, 301.5],
                'volume': [1000, 1100, 900, 2500, 4000, 1800],
                'transactions': [10, 11, 9, 25, 40, 18],
                'vwap': [100.2, 200.2, 300.2, 101.2, 201.2, 301.2],
            }
        )

        strategy = TradingStrategy()
        universe = strategy.select_universe(daily_data)

        assert universe[:3] == ['MSFT', 'AAPL', 'TSLA']
        assert all(isinstance(ticker, str) for ticker in universe)

    def test_select_universe_uses_20_day_average_volume(self, strategy_file_path):
        """The example strategy ranks tickers by the latest 20-session average volume."""
        from strategies.active_strategy import TradingStrategy

        session_dates = pd.date_range("2024-01-01", periods=21, freq="B")
        rows = []
        for idx, session_date in enumerate(session_dates):
            rows.extend(
                [
                    {
                        "ticker": "AAA",
                        "session_date": session_date,
                        "open": 10.0,
                        "high": 10.5,
                        "low": 9.5,
                        "close": 10.2,
                        "volume": 10_000 if idx == 0 else 1,
                        "transactions": 10,
                        "vwap": 10.1,
                    },
                    {
                        "ticker": "BBB",
                        "session_date": session_date,
                        "open": 20.0,
                        "high": 20.5,
                        "low": 19.5,
                        "close": 20.2,
                        "volume": 200,
                        "transactions": 20,
                        "vwap": 20.1,
                    },
                    {
                        "ticker": "CCC",
                        "session_date": session_date,
                        "open": 30.0,
                        "high": 30.5,
                        "low": 29.5,
                        "close": 30.2,
                        "volume": 0 if idx == 0 else 300,
                        "transactions": 30,
                        "vwap": 30.1,
                    },
                ]
            )

        strategy = TradingStrategy()
        universe = strategy.select_universe(pd.DataFrame(rows))

        assert universe[:3] == ["CCC", "BBB", "AAA"]

    def test_select_universe_excludes_tickers_missing_latest_session(self, strategy_file_path):
        """The example strategy should ignore stale tickers absent from the latest session."""
        from strategies.active_strategy import TradingStrategy

        rows = [
            {
                "ticker": "AAA",
                "session_date": pd.Timestamp("2024-01-01"),
                "open": 10.0,
                "high": 10.5,
                "low": 9.5,
                "close": 10.2,
                "volume": 1_000,
                "transactions": 10,
                "vwap": 10.1,
            },
            {
                "ticker": "AAA",
                "session_date": pd.Timestamp("2024-01-02"),
                "open": 10.0,
                "high": 10.5,
                "low": 9.5,
                "close": 10.2,
                "volume": 1_000,
                "transactions": 10,
                "vwap": 10.1,
            },
            {
                "ticker": "AAA",
                "session_date": pd.Timestamp("2024-01-03"),
                "open": 10.0,
                "high": 10.5,
                "low": 9.5,
                "close": 10.2,
                "volume": 1_000,
                "transactions": 10,
                "vwap": 10.1,
            },
            {
                "ticker": "BBB",
                "session_date": pd.Timestamp("2024-01-01"),
                "open": 20.0,
                "high": 20.5,
                "low": 19.5,
                "close": 20.2,
                "volume": 500,
                "transactions": 20,
                "vwap": 20.1,
            },
            {
                "ticker": "BBB",
                "session_date": pd.Timestamp("2024-01-02"),
                "open": 20.0,
                "high": 20.5,
                "low": 19.5,
                "close": 20.2,
                "volume": 500,
                "transactions": 20,
                "vwap": 20.1,
            },
            {
                "ticker": "BBB",
                "session_date": pd.Timestamp("2024-01-03"),
                "open": 20.0,
                "high": 20.5,
                "low": 19.5,
                "close": 20.2,
                "volume": 500,
                "transactions": 20,
                "vwap": 20.1,
            },
            {
                "ticker": "OLD",
                "session_date": pd.Timestamp("2024-01-01"),
                "open": 30.0,
                "high": 30.5,
                "low": 29.5,
                "close": 30.2,
                "volume": 5_000_000,
                "transactions": 30,
                "vwap": 30.1,
            },
            {
                "ticker": "OLD",
                "session_date": pd.Timestamp("2024-01-02"),
                "open": 30.0,
                "high": 30.5,
                "low": 29.5,
                "close": 30.2,
                "volume": 5_000_000,
                "transactions": 30,
                "vwap": 30.1,
            },
        ]

        strategy = TradingStrategy()
        universe = strategy.select_universe(pd.DataFrame(rows))

        assert "OLD" not in universe
        assert universe[:2] == ["AAA", "BBB"]

    def test_select_universe_marks_bear_volatile_when_spy_is_weak_and_volatile(self, strategy_file_path):
        """SPY daily context should set the simple bear-volatile regime gate."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy()
        universe = strategy.select_universe(build_spy_regime_daily_frame())

        assert strategy.market_regime == "bear_volatile"
        assert "AAA" in universe
        assert "BBB" in universe

    def test_select_universe_defaults_to_neutral_without_spy_context(self, strategy_file_path):
        """Without SPY daily context the strategy should keep the neutral regime."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy()
        universe = strategy.select_universe(build_neutral_daily_frame())

        assert strategy.market_regime == "neutral"
        assert universe[:2] == ["AAA", "BBB"]

    def test_generate_signals_uses_20_bar_momentum(self, strategy_file_path):
        """The example strategy uses 20-bar momentum and emits only after confirmation."""
        from strategies.active_strategy import TradingStrategy

        minute_data = {
            "AAPL": build_minute_frame("AAPL", list(range(100, 125))),
            "MSFT": build_minute_frame("MSFT", list(range(200, 175, -1))),
        }

        strategy = TradingStrategy()
        signals = strategy.generate_signals(minute_data)

        assert signals["AAPL"].iloc[19] == 0.0
        assert signals["MSFT"].iloc[19] == 0.0
        assert signals["AAPL"].iloc[20] == 0.0
        assert signals["MSFT"].iloc[20] == 0.0
        assert signals["AAPL"].iloc[22] == 1.0
        assert signals["MSFT"].iloc[22] == -1.0

    def test_generate_signals_requires_confirmation_bars_before_non_hostile_entry(self, strategy_file_path):
        """Default confirmation bars should delay non-hostile entries until direction persists."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy()
        strategy.select_universe(build_neutral_daily_frame())
        signals = strategy.generate_signals(build_confirmation_minute_data())

        assert signals["AAPL"].iloc[20] == 0.0
        assert signals["MSFT"].iloc[20] == 0.0
        assert signals["AAPL"].iloc[21] == 0.0
        assert signals["MSFT"].iloc[21] == 0.0
        assert signals["AAPL"].iloc[22] == 1.0
        assert signals["MSFT"].iloc[22] == -1.0

    def test_generate_signals_supports_custom_confirmation_length(self, strategy_file_path):
        """Researchers can shorten or lengthen the confirmation window explicitly."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy(confirmation_bars=2)
        strategy.select_universe(build_neutral_daily_frame())
        signals = strategy.generate_signals(build_confirmation_minute_data())

        assert strategy.confirmation_bars == 2
        assert signals["AAPL"].iloc[20] == 0.0
        assert signals["MSFT"].iloc[20] == 0.0
        assert signals["AAPL"].iloc[21] == 1.0
        assert signals["MSFT"].iloc[21] == -1.0

    def test_generate_signals_holds_confirmed_position_for_minimum_bars(self, strategy_file_path):
        """After entry, the strategy should hold the confirmed position for the configured minimum bars."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy(min_hold_bars=5)
        strategy.select_universe(build_neutral_daily_frame())
        signals = strategy.generate_signals({"AAPL": build_hold_minute_frame("AAPL")})

        assert signals["AAPL"].iloc[22] == 1.0
        assert signals["AAPL"].iloc[23] == 1.0
        assert signals["AAPL"].iloc[24] == 1.0
        assert signals["AAPL"].iloc[25] == 1.0
        assert signals["AAPL"].iloc[26] == 1.0
        assert signals["AAPL"].iloc[27] == 0.0
        assert signals["AAPL"].iloc[28] == 0.0
        assert signals["AAPL"].iloc[29] == -1.0

    def test_generate_signals_supports_custom_minimum_hold_length(self, strategy_file_path):
        """Researchers can tune the minimum hold length explicitly."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy(min_hold_bars=2)
        strategy.select_universe(build_neutral_daily_frame())
        signals = strategy.generate_signals({"AAPL": build_hold_minute_frame("AAPL")})

        assert strategy.min_hold_bars == 2
        assert signals["AAPL"].iloc[22] == 1.0
        assert signals["AAPL"].iloc[23] == 1.0
        assert signals["AAPL"].iloc[24] == 0.0
        assert signals["AAPL"].iloc[25] == 0.0
        assert signals["AAPL"].iloc[26] == -1.0

    def test_generate_signals_go_flat_before_reversing_after_brief_contradiction(self, strategy_file_path):
        """Without an added hold layer, confirmation-only logic should still go flat before reversing."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy(min_hold_bars=1)
        strategy.select_universe(build_neutral_daily_frame())
        signals = strategy.generate_signals({"AAPL": build_whipsaw_minute_frame("AAPL")})

        assert signals["AAPL"].iloc[22] == 1.0
        assert signals["AAPL"].iloc[23] == 0.0
        assert signals["AAPL"].iloc[24] == 0.0
        assert signals["AAPL"].iloc[25] == -1.0

    def test_generate_signals_flatten_when_market_regime_is_bear_volatile(self, strategy_file_path):
        """The simple regime gate should flatten all minute signals in bear-volatile conditions."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy()
        strategy.market_regime = "bear_volatile"
        signals = strategy.generate_signals(build_confirmation_minute_data())

        assert signals["AAPL"].eq(0.0).all()
        assert signals["MSFT"].eq(0.0).all()

    def test_bear_volatile_overrides_minimum_hold_immediately(self, strategy_file_path):
        """The hostile regime gate should still flatten even when a hold would otherwise be active."""
        from strategies.active_strategy import TradingStrategy

        strategy = TradingStrategy(min_hold_bars=5)
        strategy.market_regime = "bear_volatile"
        signals = strategy.generate_signals({"AAPL": build_hold_minute_frame("AAPL")})

        assert signals["AAPL"].eq(0.0).all()

    def test_strategy_class_init(self, strategy_file_path):
        """TradingStrategy can be instantiated."""
        from strategies.active_strategy import TradingStrategy

        # Should be able to instantiate with defaults
        strategy = TradingStrategy()
        assert hasattr(strategy, 'fast_ma')
        assert hasattr(strategy, 'slow_ma')
        assert hasattr(strategy, 'confirmation_bars')
        assert hasattr(strategy, 'min_hold_bars')
        assert strategy.confirmation_bars == 3
        assert strategy.min_hold_bars == 5

        # Should be able to instantiate with custom params
        strategy_custom = TradingStrategy(fast_ma=10, slow_ma=30, confirmation_bars=2, min_hold_bars=4)
        assert strategy_custom.fast_ma == 10
        assert strategy_custom.slow_ma == 30
        assert strategy_custom.confirmation_bars == 2
        assert strategy_custom.min_hold_bars == 4


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

        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        assert strategy_class is not None
        assert strategy_class.__name__ == 'MyAlphaStrategy'
        assert has_universe is True

    def test_multiple_strategies_returns_first(self):
        """When multiple classes have generate_signals, first is returned with universe flag."""
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

        strategy_class, has_universe = find_strategy_class(sandbox_locals)

        assert strategy_class is not None
        assert hasattr(strategy_class, 'generate_signals')
        assert strategy_class.__name__ in {'StrategyA', 'StrategyB'}
        assert has_universe is (strategy_class.__name__ == 'StrategyA')
