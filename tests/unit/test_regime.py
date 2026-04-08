"""Unit tests for regime robustness analysis."""

import numpy as np
import pandas as pd
import pytest

from validation.regime import classify_market_regimes, regime_analysis


def make_market_data(returns: list[float]) -> pd.DataFrame:
    """Create deterministic market data from a return path."""
    dates = pd.date_range("2024-01-01", periods=len(returns), freq="D")
    returns_series = pd.Series(returns, index=dates)
    close = 100 * (1 + returns_series).cumprod()
    return pd.DataFrame({"Close": close, "returns": returns_series}, index=dates)


def make_market_data_with_index(index: pd.Index, returns: list[float]) -> pd.DataFrame:
    """Create deterministic market data aligned to a provided index."""
    returns_series = pd.Series(returns, index=index)
    close = 100 * (1 + returns_series).cumprod()
    return pd.DataFrame({"Close": close, "returns": returns_series}, index=index)


def make_strategy_returns(index: pd.Index) -> pd.Series:
    """Create a deterministic strategy return path aligned to market data."""
    values = np.where(np.arange(len(index)) % 3 == 0, 0.01, -0.002)
    return pd.Series(values, index=index)


def test_regime_four_classifications():
    """All four regimes should appear in a mixed market path."""
    bull_quiet = [0.003] * 40
    bull_volatile = ([0.02, -0.005, 0.018, -0.004] * 10)
    bear_quiet = [-0.003] * 40
    bear_volatile = ([-0.02, 0.005, -0.018, 0.004] * 10)
    market_data = make_market_data(bull_quiet + bull_volatile + bear_quiet + bear_volatile)

    regimes = classify_market_regimes(market_data)

    assert set(regimes.dropna().unique()) == {
        "bull_quiet",
        "bull_volatile",
        "bear_quiet",
        "bear_volatile",
    }


def test_regime_bull_quiet_criteria():
    """Positive rolling return and low volatility should classify as bull_quiet."""
    market_data = make_market_data(([0.02, -0.005, 0.018, -0.004] * 10) + ([0.002] * 30))
    regimes = classify_market_regimes(market_data)

    assert regimes.dropna().iloc[-1] == "bull_quiet"


def test_regime_bear_volatile_criteria():
    """Negative rolling return with high volatility should classify as bear_volatile."""
    market_data = make_market_data(([-0.02, 0.005, -0.018, 0.004] * 15))
    regimes = classify_market_regimes(market_data)

    assert regimes.dropna().iloc[-1] == "bear_volatile"


def test_regime_per_regime_sharpe():
    """Each non-empty regime receives its own Newey-West Sharpe."""
    market_data = make_market_data(([0.003] * 40) + ([-0.003] * 40))
    strategy_returns = make_strategy_returns(market_data.index)

    results = regime_analysis(strategy_returns, market_data)

    assert results
    assert all("sharpe" in metrics for metrics in results.values())


def test_regime_all_bull():
    """All-bull market data should not create bear regimes."""
    market_data = make_market_data(([0.002] * 40) + ([0.02, -0.005, 0.018, -0.004] * 10))
    strategy_returns = make_strategy_returns(market_data.index)

    results = regime_analysis(strategy_returns, market_data)

    assert set(results.keys()) <= {"bull_quiet", "bull_volatile"}


def test_regime_empty_strategy_returns():
    """Empty strategy returns should be handled gracefully."""
    market_data = make_market_data([0.002] * 50)

    assert regime_analysis(pd.Series(dtype=float), market_data) == {}


def test_regime_output_keys():
    """Each regime metric block exposes the expected fields."""
    market_data = make_market_data(([0.003] * 40) + ([-0.003] * 40))
    strategy_returns = make_strategy_returns(market_data.index)

    results = regime_analysis(strategy_returns, market_data)

    assert results
    assert all(set(metrics.keys()) == {"sharpe", "return", "count", "win_rate"} for metrics in results.values())


def test_regime_intraday_does_not_classify_before_20_days():
    """Intraday data shorter than 20 days should not produce classified regimes."""
    index = pd.date_range("2024-01-01", periods=200, freq="min")
    close = pd.Series(np.linspace(100, 120, len(index)), index=index)
    market_data = pd.DataFrame({"Close": close}, index=index)

    regimes = classify_market_regimes(market_data)

    assert regimes.notna().sum() == 0


def test_regime_business_day_daily_data_classifies_after_20_trading_days():
    """Business-day daily data should classify once 20 trading days of history exist."""
    index = pd.bdate_range("2024-01-01", periods=40)
    market_data = make_market_data_with_index(index, [0.002] * len(index))

    regimes = classify_market_regimes(market_data)

    assert regimes.first_valid_index() == index[20]
    assert regimes.notna().sum() == len(index) - 20


def test_regime_intraday_multi_day_data_waits_for_20_trading_days():
    """Intraday data should classify by trading-day count, not 20 calendar days."""
    daily_index = pd.bdate_range("2024-01-01", periods=25)
    intraday_index = pd.DatetimeIndex(
        [
            timestamp + pd.Timedelta(hours=9, minutes=30 + minute)
            for timestamp in daily_index
            for minute in range(3)
        ]
    )
    market_data = make_market_data_with_index(intraday_index, [0.001] * len(intraday_index))

    regimes = classify_market_regimes(market_data)

    assert regimes.first_valid_index().normalize() == daily_index[20]


def test_regime_short_history_raises_value_error():
    """regime_analysis should reject data that cannot support 20-day classification."""
    market_data = make_market_data([0.002] * 10)
    strategy_returns = make_strategy_returns(market_data.index)

    with pytest.raises(ValueError, match="insufficient history"):
        regime_analysis(strategy_returns, market_data)


def test_regime_business_day_data_starts_after_20_trading_days():
    """Business-day market data should classify after 20 trading bars, not 20 calendar days."""
    index = pd.bdate_range("2024-01-01", periods=25)
    market_data = make_market_data_with_index(index, ([0.01] * 21) + ([-0.01] * 4))

    regimes = classify_market_regimes(market_data)

    assert regimes.first_valid_index() == index[20]


def test_regime_analysis_supports_business_day_history():
    """Business-day daily data with sufficient history should not be rejected."""
    index = pd.bdate_range("2024-01-01", periods=40)
    market_data = make_market_data_with_index(index, ([0.01] * 20) + ([-0.01] * 20))
    strategy_returns = make_strategy_returns(market_data.index)

    results = regime_analysis(strategy_returns, market_data)

    assert results
