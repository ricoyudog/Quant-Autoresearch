import numpy as np
import pandas as pd
from scipy.stats import norm

from validation.deflated_sr import deflated_sharpe_ratio


def _manual_deflated_sharpe_ratio(
    returns: pd.Series,
    n_trials: int,
    skew: float | None = None,
    kurtosis: float | None = None,
) -> float:
    clean_returns = returns.dropna()
    if len(clean_returns) < 2 or clean_returns.std() == 0:
        return 0.5

    sharpe_ratio = (
        clean_returns.mean() / clean_returns.std()
    ) * np.sqrt(252 * 390)

    if skew is None:
        skew = float(clean_returns.skew())

    if kurtosis is None:
        kurtosis = float(clean_returns.kurtosis()) + 3.0

    variance_term = 1 - skew * sharpe_ratio + ((kurtosis - 1) / 4) * sharpe_ratio**2
    se_sr = np.sqrt(max(variance_term, 1e-10) / max(len(clean_returns) - 1, 1))

    if n_trials > 1:
        euler_gamma = 0.5772156649
        sr_star = (
            (1 - euler_gamma) * norm.ppf(1 - 1 / n_trials)
            + euler_gamma * norm.ppf(1 - 1 / (n_trials * np.e))
        )
        sr_star_adjusted = sr_star * se_sr
    else:
        sr_star_adjusted = 0.0

    return float(norm.cdf((sharpe_ratio - sr_star_adjusted) / se_sr))


def test_dsr_single_trial_matches_psr():
    """Single-trial DSR should reduce to PSR."""
    returns = pd.Series([0.002, 0.0015, 0.0025, 0.001, 0.003, 0.0022] * 20)

    result = deflated_sharpe_ratio(returns, n_trials=1)
    expected = _manual_deflated_sharpe_ratio(returns, n_trials=1)

    assert result == expected


def test_dsr_multiple_trials_is_lower_than_single_trial():
    """Multiple-testing adjustment should penalize the score."""
    returns = pd.Series([0.00002, -0.00002, 0.00001, -0.00001, 0.0, 0.0] * 20)

    single_trial = deflated_sharpe_ratio(returns, n_trials=1)
    many_trials = deflated_sharpe_ratio(returns, n_trials=100)

    assert many_trials < single_trial


def test_dsr_high_sharpe_is_close_to_one():
    """Strong returns with few trials should remain highly significant."""
    returns = pd.Series([0.002, 0.0021, 0.0019, 0.0022, 0.0018, 0.00205] * 60)

    result = deflated_sharpe_ratio(returns, n_trials=3)

    assert result > 0.95


def test_dsr_zero_returns_is_indeterminate():
    """Flat returns should yield the neutral midpoint."""
    returns = pd.Series([0.0] * 20)

    assert deflated_sharpe_ratio(returns, n_trials=10) == 0.5


def test_dsr_auto_compute_stats_matches_explicit_stats():
    """Auto-computed distribution moments should match explicit inputs."""
    returns = pd.Series([0.002, -0.001, 0.0025, -0.0005, 0.003, 0.001] * 20)
    explicit_skew = float(returns.skew())
    explicit_kurtosis = float(returns.kurtosis()) + 3.0

    auto_result = deflated_sharpe_ratio(returns, n_trials=8)
    explicit_result = deflated_sharpe_ratio(
        returns,
        n_trials=8,
        skew=explicit_skew,
        kurtosis=explicit_kurtosis,
    )

    assert auto_result == explicit_result


def test_dsr_non_normal_inputs_reduce_significance():
    """More adverse distribution moments should lower the score."""
    returns = pd.Series([0.002, -0.001, 0.0025, -0.0005, 0.003, 0.001] * 20)

    baseline = deflated_sharpe_ratio(returns, n_trials=10, skew=0.0, kurtosis=3.0)
    penalized = deflated_sharpe_ratio(returns, n_trials=10, skew=-1.5, kurtosis=12.0)

    assert penalized < baseline


def test_dsr_stays_in_probability_range():
    """DSR is a probability and must stay within [0, 1]."""
    returns = pd.Series([0.003, -0.002, 0.001, 0.0025, -0.0015, 0.0018] * 15)

    result = deflated_sharpe_ratio(returns, n_trials=25)

    assert 0.0 <= result <= 1.0
