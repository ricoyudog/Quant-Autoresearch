"""Integration tests for the validate CLI command."""

from collections import OrderedDict
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import pandas as pd
from typer.testing import CliRunner

root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

from cli import app

runner = CliRunner()


class DummyStrategy:
    """Placeholder strategy class for validate command tests."""


def make_cached_data() -> dict[str, pd.DataFrame]:
    """Create deterministic cached data for validate command tests."""
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    close = 100 + np.linspace(0, 10, len(dates))
    returns = np.full(len(dates), 0.01)
    return {
        "SPY": pd.DataFrame(
            {
                "Open": close,
                "High": close + 1,
                "Low": close - 1,
                "Close": close,
                "Volume": np.full(len(dates), 1000),
                "returns": returns,
                "volatility": np.full(len(dates), 0.01),
                "atr": np.full(len(dates), 1.0),
            },
            index=dates,
        )
    }


@patch("validation.cpcv.run_cpcv")
@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_cpcv(mock_load_strategy_class, mock_load_data, mock_run_cpcv):
    """--method cpcv should dispatch to validation.cpcv."""
    mock_load_strategy_class.return_value = DummyStrategy
    mock_load_data.return_value = make_cached_data()
    mock_run_cpcv.return_value = {
        "sharpe_distribution": [0.1, 0.2],
        "mean_sharpe": 0.15,
        "std_sharpe": 0.05,
        "pct_positive": 1.0,
        "worst_sharpe": 0.1,
        "best_sharpe": 0.2,
    }

    result = runner.invoke(app, ["validate", "--method", "cpcv"])

    assert result.exit_code == 0
    assert "MEAN_SHARPE" in result.stdout
    assert "VERDICT" in result.stdout
    mock_run_cpcv.assert_called_once()


@patch("validation.regime.regime_analysis")
@patch("cli.compute_combined_strategy_returns")
@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_regime(
    mock_load_strategy_class,
    mock_load_data,
    mock_compute_combined_returns,
    mock_regime_analysis,
):
    """--method regime should dispatch to validation.regime."""
    mock_load_strategy_class.return_value = DummyStrategy
    cached_data = make_cached_data()
    mock_load_data.return_value = cached_data
    mock_compute_combined_returns.return_value = pd.Series(
        np.full(40, 0.01),
        index=next(iter(cached_data.values())).index,
    )
    mock_regime_analysis.return_value = {
        "bull_quiet": {
            "sharpe": 0.5,
            "return": 0.12,
            "count": 20,
            "win_rate": 0.55,
        }
    }

    result = runner.invoke(app, ["validate", "--method", "regime"])

    assert result.exit_code == 0
    assert "BULL_QUIET" in result.stdout
    assert "VERDICT" in result.stdout
    mock_regime_analysis.assert_called_once()


@patch("validation.stability.parameter_stability_test")
@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_stability(mock_load_strategy_class, mock_load_data, mock_parameter_stability_test):
    """--method stability should dispatch to validation.stability."""
    mock_load_strategy_class.return_value = DummyStrategy
    mock_load_data.return_value = make_cached_data()
    mock_parameter_stability_test.return_value = {
        "overall_stability": 0.8,
        "parameters": {
            "lookback": {
                "stability": 0.8,
                "peak_sharpe": 0.5,
                "min_sharpe": 0.2,
                "sharpes": [0.2, 0.5],
            }
        },
        "verdict": "GOOD",
        "message": "",
    }

    result = runner.invoke(app, ["validate", "--method", "stability"])

    assert result.exit_code == 0
    assert "OVERALL_STABILITY" in result.stdout
    assert "VERDICT" in result.stdout
    mock_parameter_stability_test.assert_called_once()


def test_cli_validate_invalid_method():
    """Invalid methods should exit non-zero."""
    result = runner.invoke(app, ["validate", "--method", "invalid"])
    assert result.exit_code != 0


@patch("validation.cpcv.run_cpcv")
@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_cpcv_custom_groups(mock_load_strategy_class, mock_load_data, mock_run_cpcv):
    """Custom group arguments should be forwarded to CPCV."""
    mock_load_strategy_class.return_value = DummyStrategy
    mock_load_data.return_value = make_cached_data()
    mock_run_cpcv.return_value = {
        "sharpe_distribution": [0.1],
        "mean_sharpe": 0.1,
        "std_sharpe": 0.0,
        "pct_positive": 1.0,
        "worst_sharpe": 0.1,
        "best_sharpe": 0.1,
    }

    result = runner.invoke(app, ["validate", "--method", "cpcv", "--groups", "6", "--test-groups", "1"])

    assert result.exit_code == 0
    assert mock_run_cpcv.call_args.kwargs["n_groups"] == 6
    assert mock_run_cpcv.call_args.kwargs["n_test"] == 1


@patch("validation.stability.parameter_stability_test")
@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_stability_custom_perturbation(
    mock_load_strategy_class,
    mock_load_data,
    mock_parameter_stability_test,
):
    """Custom perturbation arguments should be forwarded to stability validation."""
    mock_load_strategy_class.return_value = DummyStrategy
    mock_load_data.return_value = make_cached_data()
    mock_parameter_stability_test.return_value = {
        "overall_stability": 0.7,
        "parameters": {},
        "verdict": "MODERATE",
        "message": "",
    }

    result = runner.invoke(
        app,
        ["validate", "--method", "stability", "--perturbation", "0.3", "--steps", "7"],
    )

    assert result.exit_code == 0
    assert mock_parameter_stability_test.call_args.kwargs["perturbation"] == 0.3
    assert mock_parameter_stability_test.call_args.kwargs["steps"] == 7


@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_no_data(mock_load_strategy_class, mock_load_data):
    """Missing cached data should produce an informative error."""
    mock_load_strategy_class.return_value = DummyStrategy
    mock_load_data.return_value = {}

    result = runner.invoke(app, ["validate", "--method", "cpcv"])

    assert result.exit_code == 1
    assert "No cached data found" in result.stdout


@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_runtime_validation_errors_are_informative(mock_load_strategy_class, mock_load_data):
    """Validation-time errors should reach stdout instead of bubbling raw exceptions."""
    mock_load_strategy_class.return_value = DummyStrategy
    mock_load_data.return_value = {"SPY": None}

    result = runner.invoke(app, ["validate", "--method", "cpcv"])

    assert result.exit_code == 1
    assert "data_config must contain at least one dataframe" in result.stdout


@patch("validation.regime.regime_analysis")
@patch("cli.compute_combined_strategy_returns")
@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_regime_prefers_spy_benchmark(
    mock_load_strategy_class,
    mock_load_data,
    mock_compute_combined_returns,
    mock_regime_analysis,
):
    """Regime validation should use SPY as the market benchmark when available."""
    mock_load_strategy_class.return_value = DummyStrategy
    cached_data = OrderedDict(
        [
            ("QQQ", make_cached_data()["SPY"].copy()),
            ("SPY", make_cached_data()["SPY"].copy()),
        ]
    )
    cached_data["SPY"]["Close"] = cached_data["SPY"]["Close"] + 5
    mock_load_data.return_value = cached_data
    mock_compute_combined_returns.return_value = pd.Series(
        np.full(40, 0.01),
        index=next(iter(cached_data.values())).index,
    )
    mock_regime_analysis.return_value = {}

    result = runner.invoke(app, ["validate", "--method", "regime"])

    assert result.exit_code == 0
    assert mock_regime_analysis.call_args.args[1] is cached_data["SPY"]


@patch("validation.regime.regime_analysis")
@patch("cli.compute_combined_strategy_returns")
@patch("core.backtester.load_data")
@patch("cli.load_strategy_class")
def test_cli_validate_regime_requires_single_symbol_or_spy(
    mock_load_strategy_class,
    mock_load_data,
    mock_compute_combined_returns,
    mock_regime_analysis,
):
    """Multi-symbol regime validation needs an explicit market benchmark."""
    mock_load_strategy_class.return_value = DummyStrategy
    qqq = make_cached_data()["SPY"].copy()
    qqq["Close"] = qqq["Close"] + 10
    mock_load_data.return_value = OrderedDict([("QQQ", qqq), ("IWM", qqq.copy())])
    mock_compute_combined_returns.return_value = pd.Series(np.full(40, 0.01), index=qqq.index)
    mock_regime_analysis.return_value = {}

    result = runner.invoke(app, ["validate", "--method", "regime"])

    assert result.exit_code == 1
    assert "single symbol or cached SPY benchmark" in result.stdout
