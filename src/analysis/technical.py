import math
from typing import Any, Dict

import pandas as pd


def _get_series(df: pd.DataFrame, *names: str) -> pd.Series:
    for name in names:
        if name in df.columns:
            return df[name]
    raise KeyError(f"Missing required columns: {names}")


def _annualized_volatility(returns: pd.Series, window: int) -> float | None:
    sample = returns.tail(window).dropna()
    if sample.empty:
        return None
    return float(sample.std() * math.sqrt(252))


def calculate_momentum(df: pd.DataFrame) -> Dict[str, float | None]:
    close = _get_series(df, "Close", "close")

    def rate_of_change(window: int) -> float | None:
        if len(close) <= window:
            return None
        base = close.iloc[-window - 1]
        if base == 0:
            return None
        return float(close.iloc[-1] / base - 1)

    return {
        "roc_5d": rate_of_change(5),
        "roc_20d": rate_of_change(20),
        "roc_60d": rate_of_change(60),
    }


def calculate_volatility(df: pd.DataFrame) -> Dict[str, float | None]:
    close = _get_series(df, "Close", "close")
    returns = close.pct_change()
    return {
        "vol_5d": _annualized_volatility(returns, 5),
        "vol_20d": _annualized_volatility(returns, 20),
        "vol_60d": _annualized_volatility(returns, 60),
    }


def analyze_volume(df: pd.DataFrame) -> Dict[str, float | None]:
    volume = _get_series(df, "Volume", "volume")
    current_volume = float(volume.iloc[-1]) if not volume.empty else None
    average_volume_20d = float(volume.tail(20).mean()) if not volume.empty else None
    prior_average = float(volume.tail(40).head(20).mean()) if len(volume) >= 40 else None

    relative_volume = None
    if current_volume is not None and average_volume_20d not in (None, 0):
        relative_volume = float(current_volume / average_volume_20d)

    volume_trend = None
    if average_volume_20d not in (None, 0) and prior_average not in (None, 0):
        volume_trend = float(average_volume_20d / prior_average - 1)

    return {
        "current_volume": current_volume,
        "average_volume_20d": average_volume_20d,
        "relative_volume": relative_volume,
        "volume_trend": volume_trend,
    }


def find_key_levels(df: pd.DataFrame, lookback: int = 60) -> Dict[str, float | None]:
    high = _get_series(df, "High", "high")
    low = _get_series(df, "Low", "low")
    close = _get_series(df, "Close", "close")
    volume = _get_series(df, "Volume", "volume")

    recent_high = high.tail(lookback)
    recent_low = low.tail(lookback)
    recent_close = close.tail(lookback)
    recent_volume = volume.tail(lookback)

    current_close = float(close.iloc[-1]) if not close.empty else None
    high_60d = float(recent_high.max()) if not recent_high.empty else None
    low_60d = float(recent_low.min()) if not recent_low.empty else None
    vwap = None
    if not recent_close.empty and float(recent_volume.sum()) != 0:
        vwap = float((recent_close * recent_volume).sum() / recent_volume.sum())

    pct_from_high = None
    pct_from_low = None
    if current_close is not None and high_60d not in (None, 0):
        pct_from_high = float(current_close / high_60d - 1)
    if current_close is not None and low_60d not in (None, 0):
        pct_from_low = float(current_close / low_60d - 1)

    return {
        "high_60d": high_60d,
        "low_60d": low_60d,
        "close": current_close,
        "pct_from_high": pct_from_high,
        "pct_from_low": pct_from_low,
        "vwap": vwap,
    }


def calculate_summary_stats(df: pd.DataFrame, lookback: int = 60) -> Dict[str, float | None]:
    close = _get_series(df, "Close", "close")
    high = _get_series(df, "High", "high")
    low = _get_series(df, "Low", "low")
    returns = close.pct_change().tail(lookback).dropna()

    sharpe = None
    if not returns.empty and float(returns.std()) != 0:
        sharpe = float((returns.mean() / returns.std()) * math.sqrt(252))

    cumulative = (1 + returns).cumprod()
    max_drawdown = None
    if not cumulative.empty:
        drawdown = cumulative / cumulative.cummax() - 1
        max_drawdown = float(drawdown.min())

    win_rate = float((returns > 0).mean()) if not returns.empty else None
    avg_daily_range = None
    if not close.tail(lookback).empty:
        daily_range = (high.tail(lookback) - low.tail(lookback)) / close.tail(lookback)
        avg_daily_range = float(daily_range.mean())

    return {
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "avg_daily_range": avg_daily_range,
    }
