import pandas as pd

from validation.newey_west import newey_west_sharpe


REGIME_NAMES = (
    "bull_quiet",
    "bull_volatile",
    "bear_quiet",
    "bear_volatile",
)


def _classify_regime_from_daily_series(close: pd.Series, returns: pd.Series) -> pd.Series:
    """Classify regimes from daily close and return series using 20 trading-day windows."""
    rolling_return = close.pct_change(20)
    rolling_volatility = returns.rolling(20).std()
    volatility_median = rolling_volatility.dropna().median()

    regimes = pd.Series(index=close.index, dtype="object")
    regimes[(rolling_return > 0) & (rolling_volatility < volatility_median)] = "bull_quiet"
    regimes[(rolling_return > 0) & (rolling_volatility >= volatility_median)] = "bull_volatile"
    regimes[(rolling_return <= 0) & (rolling_volatility < volatility_median)] = "bear_quiet"
    regimes[(rolling_return <= 0) & (rolling_volatility >= volatility_median)] = "bear_volatile"
    return regimes


def classify_market_regimes(market_data: pd.DataFrame) -> pd.Series:
    """Classify each bar into one of four simple market regimes."""
    if market_data.empty:
        return pd.Series(dtype="object")

    close_column = "Close" if "Close" in market_data.columns else "close"
    if close_column not in market_data.columns:
        raise ValueError("market_data must contain Close or close column")

    if isinstance(market_data.index, pd.DatetimeIndex):
        session_index = market_data.index.normalize()
        daily_close = market_data[close_column].groupby(session_index).last()
        if session_index.nunique() == len(market_data) and "returns" in market_data.columns:
            daily_returns = pd.Series(market_data["returns"].to_numpy(), index=session_index)
        else:
            daily_returns = daily_close.pct_change()
        daily_regimes = _classify_regime_from_daily_series(daily_close, daily_returns)
        return pd.Series(daily_regimes.reindex(session_index).to_numpy(), index=market_data.index, dtype="object")

    returns = market_data["returns"] if "returns" in market_data.columns else market_data[close_column].pct_change()
    return _classify_regime_from_daily_series(market_data[close_column], returns)


def regime_analysis(strategy_returns: pd.Series, market_data: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    """Compute per-regime performance metrics for aligned strategy returns."""
    if strategy_returns.empty or market_data.empty:
        return {}

    regimes = classify_market_regimes(market_data)
    if not regimes.notna().any():
        raise ValueError("insufficient history for 20-day regime classification")
    aligned_returns = strategy_returns.reindex(market_data.index).dropna()

    results = {}
    for regime_name in REGIME_NAMES:
        mask = regimes == regime_name
        if not mask.any():
            continue

        regime_returns = aligned_returns.reindex(regimes[mask].index).dropna()
        if regime_returns.empty:
            continue

        results[regime_name] = {
            "sharpe": float(newey_west_sharpe(regime_returns)),
            "return": float(regime_returns.sum()),
            "count": int(len(regime_returns)),
            "win_rate": float((regime_returns > 0).mean()),
        }

    return results
