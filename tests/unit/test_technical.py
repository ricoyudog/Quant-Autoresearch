import pandas as pd

from analysis.technical import (
    analyze_volume,
    calculate_momentum,
    calculate_summary_stats,
    calculate_volatility,
    find_key_levels,
)


def build_market_frame() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=80, freq="D")
    close = pd.Series(range(100, 180), index=dates, dtype=float)
    return pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 1,
            "Low": close - 2,
            "Close": close,
            "Volume": pd.Series(range(1000, 1080), index=dates, dtype=float),
        }
    )


def test_calculate_momentum_returns_expected_keys():
    result = calculate_momentum(build_market_frame())

    assert set(result) == {"roc_5d", "roc_20d", "roc_60d"}
    assert result["roc_5d"] is not None


def test_calculate_volatility_returns_windowed_values():
    result = calculate_volatility(build_market_frame())

    assert set(result) == {"vol_5d", "vol_20d", "vol_60d"}
    assert result["vol_20d"] is not None


def test_volume_levels_and_summary_are_structured():
    volume = analyze_volume(build_market_frame())
    summary = calculate_summary_stats(build_market_frame())
    levels = find_key_levels(build_market_frame())

    assert set(volume) == {"current_volume", "average_volume_20d", "relative_volume", "volume_trend"}
    assert "sharpe" in summary
    assert "high_60d" in levels
