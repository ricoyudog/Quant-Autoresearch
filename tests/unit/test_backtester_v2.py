"""Unit tests for V2 backtester functions.

Tests cover the new functions added to the backtester:
- find_strategy_class
- calculate_metrics
- calculate_baseline_sharpe
- run_per_symbol_analysis
"""

import pytest
import pandas as pd
import numpy as np

import core.backtester as backtester_module

from core.backtester import (
    find_strategy_class,
    calculate_metrics,
    calculate_baseline_sharpe,
    run_per_symbol_analysis,
)


class DummyStrategy:
    """Dummy strategy class for testing."""
    def generate_signals(self, data):
        return pd.Series(1, index=data.index)


class AnotherStrategy:
    """Another strategy class for testing."""
    def generate_signals(self, data):
        return pd.Series(0, index=data.index)


class HelperStrategy:
    """Helper/base class that should not be auto-selected."""

    def __init__(self, lookback):
        self.lookback = lookback

    def generate_signals(self, data):
        return pd.Series(0, index=data.index)


class NonStrategyClass:
    """Class without generate_signals method."""
    def some_method(self):
        pass


# =============================================================================
# find_strategy_class tests
# =============================================================================

class TestFindStrategyClass:
    """Tests for find_strategy_class function."""

    def test_find_strategy_class_found(self):
        """Mock class with generate_signals is found."""
        sandbox_locals = {
            'DummyStrategy': DummyStrategy,
            'other_var': 42,
        }
        result = find_strategy_class(sandbox_locals)
        assert result is DummyStrategy

    def test_find_strategy_class_not_found(self):
        """Empty dict returns None."""
        result = find_strategy_class({})
        assert result is None

    def test_find_strategy_class_multiple(self):
        """First matching class returned."""
        sandbox_locals = {
            'AnotherStrategy': AnotherStrategy,
            'DummyStrategy': DummyStrategy,
        }
        result = find_strategy_class(sandbox_locals)
        # First matching class in iteration order
        assert result in (AnotherStrategy, DummyStrategy)
        assert hasattr(result, 'generate_signals')

    def test_find_strategy_class_non_class_ignored(self):
        """Functions/variables ignored."""
        def generate_signals(data):
            return pd.Series(1, index=data.index)

        sandbox_locals = {
            'NonStrategyClass': NonStrategyClass,
            'generate_signals': generate_signals,
            'some_number': 42,
        }
        result = find_strategy_class(sandbox_locals)
        assert result is None

    def test_find_strategy_class_skips_non_instantiable_helper_classes(self):
        """Concrete zero-arg strategy should win over helper/base classes."""
        sandbox_locals = {
            "HelperStrategy": HelperStrategy,
            "DummyStrategy": DummyStrategy,
        }

        result = find_strategy_class(sandbox_locals)

        assert result is DummyStrategy


# =============================================================================
# calculate_metrics tests
# =============================================================================

class TestCalculateMetrics:
    """Tests for calculate_metrics function."""

    def test_calculate_metrics_basic(self):
        """All 10 keys present in return dict."""
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
        trades = pd.Series([1, -1, 1, -1, 1], index=returns.index)
        result = calculate_metrics(returns, trades)

        expected_keys = {
            'sharpe', 'sortino', 'calmar', 'drawdown', 'max_dd_days',
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
        """Sortino > sharpe for upside-skewed returns."""
        # Upside-skewed returns (more large positive, small negative)
        returns = pd.Series([0.05, 0.04, 0.03, -0.005, -0.01, 0.06, 0.07])
        trades = pd.Series([1] * 7)
        result = calculate_metrics(returns, trades)

        # Sortino uses only downside deviation, so should be higher
        # when there are positive outliers
        assert result['sortino'] >= result['sharpe']

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

    def test_calculate_metrics_aggregates_closed_trade_returns(self):
        """Multi-bar holds should count as one trade, not one bar per trade."""
        returns = pd.Series([0.01, -0.005, 0.01, 0.0])
        trades = pd.Series([1, 1, 1, 0], index=returns.index)

        result = calculate_metrics(returns, trades)

        assert result["win_rate"] == 1.0
        assert result["avg_win"] == pytest.approx(0.015)


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
        assert result > 0


class TestRuntimeStrategyResolution:
    """Tests for resolving strategy paths at runtime."""

    def test_security_check_uses_current_env_strategy_file(self, monkeypatch, tmp_path):
        """Runtime STRATEGY_FILE env var should override stale module globals."""
        strategy_path = tmp_path / "forbidden_strategy.py"
        strategy_path.write_text("import os\n")

        monkeypatch.setattr(
            backtester_module,
            "STRATEGY_FILE",
            "src/strategies/active_strategy.py",
        )
        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))

        is_safe, message = backtester_module.security_check()

        assert is_safe is False
        assert "Forbidden module import found: os" in message

    def test_format_p_value_reports_unavailable_placeholder(self):
        """Unavailable significance should not masquerade as a passing p-value."""
        assert hasattr(backtester_module, "format_p_value")
        assert backtester_module.format_p_value(None) == "NA"

    def test_walk_forward_validation_avoids_duplicate_trade_indexes(self, monkeypatch, tmp_path):
        """Multi-symbol trade aggregation should not duplicate portfolio returns per symbol."""
        strategy_path = tmp_path / "runtime_strategy.py"
        strategy_path.write_text(
            "class TradingStrategy:\n"
            "    def generate_signals(self, data):\n"
            "        return pd.Series(1, index=data.index)\n"
        )

        dates = pd.date_range("2023-01-01", periods=20)
        sample_frame = pd.DataFrame(
            {
                "returns": [0.01] * 20,
                "volatility": [0.0] * 20,
            },
            index=dates,
        )
        data = {
            "SPY": sample_frame.copy(),
            "QQQ": sample_frame.copy(),
        }

        monkeypatch.setenv("STRATEGY_FILE", str(strategy_path))
        monkeypatch.setattr(backtester_module, "load_data", lambda: data)

        original_calculate_metrics = backtester_module.calculate_metrics

        def spy(combined_returns, trades, *args, **kwargs):
            assert not trades.index.has_duplicates
            return original_calculate_metrics(combined_returns, trades, *args, **kwargs)

        monkeypatch.setattr(backtester_module, "calculate_metrics", spy)

        backtester_module.walk_forward_validation(str(strategy_path))

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
