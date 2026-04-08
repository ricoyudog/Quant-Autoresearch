from typing import Dict

import pandas as pd

from .technical import _get_series


def calculate_market_context(
    symbol_df: pd.DataFrame,
    benchmark_df: pd.DataFrame | None = None,
) -> Dict[str, float | None]:
    close = _get_series(symbol_df, "Close", "close")

    correlation_to_spy = None
    if benchmark_df is not None:
        benchmark_close = _get_series(benchmark_df, "Close", "close")
        joined = pd.concat(
            [
                close.pct_change().rename("symbol"),
                benchmark_close.pct_change().rename("benchmark"),
            ],
            axis=1,
        ).dropna()
        if not joined.empty:
            correlation_to_spy = float(joined["symbol"].corr(joined["benchmark"]))

    ma_50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
    ma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    current_close = float(close.iloc[-1]) if not close.empty else None

    distance_from_50d_ma = None
    distance_from_200d_ma = None
    if current_close is not None and ma_50 not in (None, 0):
        distance_from_50d_ma = float(current_close / ma_50 - 1)
    if current_close is not None and ma_200 not in (None, 0):
        distance_from_200d_ma = float(current_close / ma_200 - 1)

    return {
        "correlation_to_spy": correlation_to_spy,
        "distance_from_50d_ma": distance_from_50d_ma,
        "distance_from_200d_ma": distance_from_200d_ma,
    }
