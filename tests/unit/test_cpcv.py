"""Unit tests for CPCV validation helpers and runner."""

import numpy as np
import pandas as pd
import pytest

from validation.cpcv import (
    build_group_slices,
    generate_cpcv_paths,
    resolve_train_test_indices,
    run_cpcv,
)


class ZeroSignalStrategy:
    """Strategy that never takes risk."""

    def generate_signals(self, data):
        return pd.Series(0.0, index=data.index)


class BoundarySignalStrategy:
    """Strategy whose first test-bar signal depends on the last visible train bar."""

    def generate_signals(self, data):
        return (data["returns"] > 0.1).astype(float)


class LookaheadSignalStrategy:
    """Non-causal strategy used to detect CPCV leakage across test bars."""

    def generate_signals(self, data):
        return (data["returns"].shift(-1) > 0).astype(float)


class StatefulPrefixStrategy:
    """Strategy used to detect state leakage across repeated prefix evaluations."""

    def __init__(self):
        self.calls = 0

    def generate_signals(self, data):
        self.calls += 1
        value = 1.0 if self.calls > 1 else 0.0
        return pd.Series(value, index=data.index)


def make_validation_data(length: int = 80) -> dict[str, pd.DataFrame]:
    """Create deterministic market data for CPCV tests."""
    dates = pd.date_range("2024-01-01", periods=length, freq="D")
    close = 100 + np.linspace(0, 5, length)
    returns = np.sin(np.linspace(0, 6 * np.pi, length)) * 0.01
    return {
        "SPY": pd.DataFrame(
            {
                "Open": close,
                "High": close + 1,
                "Low": close - 1,
                "Close": close,
                "Volume": np.full(length, 1000),
                "returns": returns,
                "volatility": np.full(length, 0.01),
                "atr": np.full(length, 1.0),
            },
            index=dates,
        )
    }


def test_cpcv_path_count_6_1():
    """C(6,1) should generate 6 test paths."""
    assert len(generate_cpcv_paths(6, 1)) == 6


def test_cpcv_path_count_8_2():
    """C(8,2) should generate 28 test paths."""
    assert len(generate_cpcv_paths(8, 2)) == 28


def test_cpcv_purging():
    """Purging removes training bars adjacent to the test boundary."""
    group_slices = build_group_slices(length=30, n_groups=3)
    train_indices, test_indices = resolve_train_test_indices(
        group_slices=group_slices,
        test_groups=(1,),
        purge_bars=2,
        embargo_bars=0,
    )

    assert 8 not in train_indices
    assert 9 not in train_indices
    assert 20 not in train_indices
    assert 21 not in train_indices
    assert list(test_indices) == list(range(10, 20))


def test_cpcv_embargo():
    """Embargo trims edge bars from the selected test set."""
    group_slices = build_group_slices(length=30, n_groups=3)
    _, test_indices = resolve_train_test_indices(
        group_slices=group_slices,
        test_groups=(1,),
        purge_bars=0,
        embargo_bars=2,
    )

    assert list(test_indices) == list(range(12, 18))


def test_cpcv_no_overlap():
    """Train and test indices should never overlap."""
    group_slices = build_group_slices(length=40, n_groups=4)
    train_indices, test_indices = resolve_train_test_indices(
        group_slices=group_slices,
        test_groups=(1, 2),
        purge_bars=1,
        embargo_bars=1,
    )

    assert set(train_indices).isdisjoint(test_indices)


def test_cpcv_output_format():
    """run_cpcv returns the required summary keys."""
    result = run_cpcv(ZeroSignalStrategy, make_validation_data(), n_groups=6, n_test=1)

    expected_keys = {
        "sharpe_distribution",
        "mean_sharpe",
        "std_sharpe",
        "pct_positive",
        "worst_sharpe",
        "best_sharpe",
    }
    assert set(result.keys()) == expected_keys


def test_cpcv_summary_metrics_match_distribution():
    """Summary metrics should be derived from the returned Sharpe distribution."""
    result = run_cpcv(ZeroSignalStrategy, make_validation_data(), n_groups=6, n_test=1)
    sharpes = np.array(result["sharpe_distribution"], dtype=float)

    assert len(sharpes) == 6
    assert result["mean_sharpe"] == pytest.approx(float(sharpes.mean()))
    assert result["std_sharpe"] == pytest.approx(float(sharpes.std()))
    assert result["worst_sharpe"] == pytest.approx(float(sharpes.min()))
    assert result["best_sharpe"] == pytest.approx(float(sharpes.max()))


def test_cpcv_pct_positive_range():
    """Positive-path share should always be a probability."""
    result = run_cpcv(ZeroSignalStrategy, make_validation_data(), n_groups=6, n_test=1)
    assert 0.0 <= result["pct_positive"] <= 1.0


def test_cpcv_with_constant_strategy():
    """A zero-signal strategy should produce near-zero CPCV sharpes."""
    result = run_cpcv(ZeroSignalStrategy, make_validation_data(), n_groups=6, n_test=1)
    assert all(abs(sharpe) < 1e-9 for sharpe in result["sharpe_distribution"])


def test_cpcv_runner_honors_purging():
    """Purging should change runner output when boundary bars drive the signal."""
    data = make_validation_data(length=30)
    data["SPY"].loc[data["SPY"].index[9], "returns"] = 0.5
    data["SPY"].loc[data["SPY"].index[19], "returns"] = 0.5
    data["SPY"].loc[data["SPY"].index[10:20], "returns"] = 0.01
    data["SPY"].loc[data["SPY"].index[20:30], "returns"] = 0.01

    unpurged = run_cpcv(BoundarySignalStrategy, data, n_groups=3, n_test=1, purge_bars=0)
    purged = run_cpcv(BoundarySignalStrategy, data, n_groups=3, n_test=1, purge_bars=1)

    assert unpurged["pct_positive"] == pytest.approx(1 / 3)
    assert unpurged["best_sharpe"] > 50
    assert purged["sharpe_distribution"] == [0.0, 0.0, 0.0]
    assert purged["mean_sharpe"] == 0.0
    assert purged["std_sharpe"] == 0.0
    assert purged["pct_positive"] == 0.0


def test_cpcv_rejects_none_only_data_config():
    """CPCV should reject configs that contain no usable dataframes."""
    with pytest.raises(ValueError, match="data_config must contain at least one dataframe"):
        run_cpcv(ZeroSignalStrategy, {"SPY": None}, n_groups=3, n_test=1)


def test_cpcv_does_not_leak_future_test_information():
    """Signals for early test bars must not depend on later test bars."""
    data = make_validation_data(length=20)
    data["SPY"]["returns"] = np.array([-0.01] * 10 + [0.01] * 10)
    data["SPY"]["volatility"] = 0.0

    result = run_cpcv(
        LookaheadSignalStrategy,
        data,
        n_groups=2,
        n_test=1,
        purge_bars=0,
        embargo_bars=0,
    )

    assert result["sharpe_distribution"] == [0.0, 0.0]
    assert result["mean_sharpe"] == 0.0
    assert result["pct_positive"] == 0.0


def test_cpcv_prefix_evaluations_do_not_share_strategy_state():
    """Repeated prefix evaluations should not accumulate strategy instance state."""
    result = run_cpcv(
        StatefulPrefixStrategy,
        make_validation_data(length=20),
        n_groups=2,
        n_test=1,
        purge_bars=0,
        embargo_bars=0,
    )

    assert result["sharpe_distribution"] == [0.0, 0.0]
