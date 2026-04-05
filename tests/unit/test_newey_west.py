import numpy as np
import pandas as pd

from validation.newey_west import newey_west_sharpe


def test_nw_sharpe_empty_series():
    """Empty returns should produce a neutral score."""
    assert newey_west_sharpe(pd.Series(dtype=float)) == 0.0


def test_nw_sharpe_single_value():
    """A single return cannot produce a stable variance estimate."""
    assert newey_west_sharpe(pd.Series([0.01])) == 0.0


def test_nw_sharpe_annualization_with_zero_lag():
    """With zero lag, NW Sharpe should reduce to minute-bar annualized Sharpe."""
    returns = pd.Series([0.01, 0.015, 0.02, 0.005, 0.012])

    result = newey_west_sharpe(returns, max_lag=0)

    expected = (returns.mean() / returns.std()) * np.sqrt(252 * 390)
    assert result == expected


def test_nw_sharpe_serial_correlation_penalty():
    """Positive serial correlation should reduce the adjusted Sharpe."""
    returns = pd.Series([0.03] * 40 + [0.01] * 40 + [0.025] * 40)

    naive_sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 390)
    nw_sharpe = newey_west_sharpe(returns)

    assert nw_sharpe < naive_sharpe


def test_nw_sharpe_negative_autocorrelation_bonus():
    """Alternating returns should shrink long-run variance and lift Sharpe."""
    returns = pd.Series([0.01, 0.03] * 60)

    naive_sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 390)
    nw_sharpe = newey_west_sharpe(returns)

    assert nw_sharpe > naive_sharpe


def test_nw_sharpe_bartlett_weights():
    """Lag covariance should be weighted by the Bartlett kernel."""
    returns = pd.Series([0.01, 0.03, 0.02, 0.04, 0.015, 0.035])

    result = newey_west_sharpe(returns, max_lag=1)

    gamma_0 = returns.var()
    gamma_1 = returns.cov(returns.shift(1))
    expected_variance = gamma_0 + 2 * (1 - 1 / (1 + 1)) * gamma_1
    expected = (returns.mean() / np.sqrt(max(expected_variance, 1e-10))) * np.sqrt(252 * 390)

    assert result == expected
