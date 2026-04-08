import numpy as np
import pandas as pd


def newey_west_sharpe(returns: pd.Series, max_lag: int | None = None) -> float:
    """Calculate the minute-bar annualized Newey-West adjusted Sharpe Ratio."""
    clean_returns = pd.Series(returns).dropna()
    sample_size = len(clean_returns)

    if sample_size < 2:
        return 0.0

    if clean_returns.std() == 0:
        return 0.0

    if max_lag is None:
        max_lag = int(sample_size ** (1 / 3))

    max_lag = max(0, min(max_lag, sample_size - 1))

    gamma_0 = clean_returns.var()
    nw_variance = gamma_0

    for lag in range(1, max_lag + 1):
        gamma_lag = clean_returns.cov(clean_returns.shift(lag))
        if pd.isna(gamma_lag):
            gamma_lag = 0.0

        weight = 1 - lag / (max_lag + 1)
        nw_variance += 2 * weight * gamma_lag

    nw_variance = max(float(nw_variance), 1e-10)
    annualization = np.sqrt(252 * 390)

    return float((clean_returns.mean() / np.sqrt(nw_variance)) * annualization)
