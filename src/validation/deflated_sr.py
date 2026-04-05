import numpy as np
import pandas as pd
from scipy.stats import norm


def deflated_sharpe_ratio(
    returns: pd.Series,
    n_trials: int,
    skew: float | None = None,
    kurtosis: float | None = None,
) -> float:
    """Calculate the Deflated Sharpe Ratio for a return series."""
    clean_returns = pd.Series(returns).dropna()
    sample_size = len(clean_returns)

    if sample_size < 2 or clean_returns.std() == 0:
        return 0.5

    sharpe_ratio = (clean_returns.mean() / clean_returns.std()) * np.sqrt(252 * 390)

    if skew is None:
        skew = float(clean_returns.skew())

    if kurtosis is None:
        kurtosis = float(clean_returns.kurtosis()) + 3.0

    variance_term = 1 - skew * sharpe_ratio + ((kurtosis - 1) / 4) * sharpe_ratio**2
    se_sr = np.sqrt(max(float(variance_term), 1e-10) / max(sample_size - 1, 1))

    adjusted_trials = max(int(n_trials), 1)
    if adjusted_trials > 1:
        euler_gamma = 0.5772156649
        sr_star = (
            (1 - euler_gamma) * norm.ppf(1 - 1 / adjusted_trials)
            + euler_gamma * norm.ppf(1 - 1 / (adjusted_trials * np.e))
        )
        sr_star_adjusted = sr_star * se_sr
    else:
        sr_star_adjusted = 0.0

    return float(norm.cdf((sharpe_ratio - sr_star_adjusted) / se_sr))
