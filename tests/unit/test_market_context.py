import pandas as pd

from analysis.market_context import calculate_market_context


def build_frame(multiplier: float = 1.0) -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=120, freq="D")
    close = pd.Series([multiplier * (100 + i) for i in range(120)], index=dates, dtype=float)
    return pd.DataFrame({"Close": close})


def test_calculate_market_context_returns_correlation_and_ma_distances():
    result = calculate_market_context(build_frame(1.1), build_frame(1.0))

    assert "correlation_to_spy" in result
    assert "distance_from_50d_ma" in result
    assert "distance_from_200d_ma" in result
