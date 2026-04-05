import pandas as pd

from validation.newey_west import newey_west_sharpe


REGIME_NAMES = (
    "bull_quiet",
    "bull_volatile",
    "bear_quiet",
    "bear_volatile",
)


def classify_market_regimes(market_data: pd.DataFrame) -> pd.Series:
    """Classify each bar into one of four simple market regimes."""
    if market_data.empty:
        return pd.Series(dtype="object")

    close_column = "Close" if "Close" in market_data.columns else "close"
    if close_column not in market_data.columns:
        raise ValueError("market_data must contain Close or close column")

    returns = market_data["returns"] if "returns" in market_data.columns else market_data[close_column].pct_change()
    rolling_return = market_data[close_column].pct_change(20)
    rolling_volatility = returns.rolling(20).std()
    volatility_median = rolling_volatility.dropna().median()

    regimes = pd.Series(index=market_data.index, dtype="object")
    regimes[(rolling_return > 0) & (rolling_volatility < volatility_median)] = "bull_quiet"
    regimes[(rolling_return > 0) & (rolling_volatility >= volatility_median)] = "bull_volatile"
    regimes[(rolling_return <= 0) & (rolling_volatility < volatility_median)] = "bear_quiet"
    regimes[(rolling_return <= 0) & (rolling_volatility >= volatility_median)] = "bear_volatile"
    return regimes


def regime_analysis(strategy_returns: pd.Series, market_data: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    """Compute per-regime performance metrics for aligned strategy returns."""
    if strategy_returns.empty or market_data.empty:
        return {}

    regimes = classify_market_regimes(market_data)
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
