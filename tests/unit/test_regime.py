import pandas as pd

from analysis.regime import classify_regime


def build_uptrend_frame() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=100, freq="D")
    close = pd.Series([100 + i * 0.5 for i in range(100)], index=dates, dtype=float)
    return pd.DataFrame({"Close": close})


def test_classify_regime_returns_current_and_distribution():
    result = classify_regime(build_uptrend_frame())

    assert result["current"] in {
        "bull_quiet",
        "bull_volatile",
        "bear_quiet",
        "bear_volatile",
    }
    assert "distribution" in result
    assert sum(result["distribution"].values()) > 0
