from collections import Counter
from typing import Dict

import pandas as pd

from .technical import _get_series


def _label_regime(period_return: float, period_vol: float, vol_median: float) -> str:
    if period_return > 0 and period_vol < vol_median:
        return "bull_quiet"
    if period_return > 0 and period_vol >= vol_median:
        return "bull_volatile"
    if period_return <= 0 and period_vol < vol_median:
        return "bear_quiet"
    return "bear_volatile"


def classify_regime(df: pd.DataFrame, window: int = 20, lookback: int = 60) -> Dict[str, object]:
    close = _get_series(df, "Close", "close")
    returns = close.pct_change()
    rolling_return = close.pct_change(window)
    rolling_vol = returns.rolling(window).std()
    valid_vol = rolling_vol.dropna()

    if valid_vol.empty:
        return {
            "current": "unknown",
            "vol_percentile": None,
            "distribution": {},
        }

    current_return = float(rolling_return.dropna().iloc[-1])
    current_vol = float(valid_vol.iloc[-1])
    vol_median = float(valid_vol.median())
    current = _label_regime(current_return, current_vol, vol_median)

    distribution_counter: Counter[str] = Counter()
    for period_return, period_vol in zip(rolling_return.tail(lookback), rolling_vol.tail(lookback)):
        if pd.isna(period_return) or pd.isna(period_vol):
            continue
        distribution_counter[_label_regime(float(period_return), float(period_vol), vol_median)] += 1

    vol_percentile = float((valid_vol <= current_vol).mean() * 100)
    return {
        "current": current,
        "vol_percentile": vol_percentile,
        "distribution": dict(distribution_counter),
    }
