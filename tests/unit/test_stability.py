"""Unit tests for parameter stability analysis."""

import numpy as np

from validation.stability import (
    extract_numeric_parameters,
    generate_parameter_values,
    parameter_stability_test,
)


class TunableStrategy:
    """Strategy with two numeric parameters and one non-numeric parameter."""

    def __init__(self, lookback=20, threshold=1.5, mode="fast"):
        self.lookback = lookback
        self.threshold = threshold
        self.mode = mode


class NoNumericParamsStrategy:
    """Strategy with no numeric defaults."""

    def __init__(self, mode="fast", regime="bull"):
        self.mode = mode
        self.regime = regime


def test_param_extraction():
    """Numeric __init__ parameters should be extracted."""
    assert extract_numeric_parameters(TunableStrategy) == {"lookback": 20, "threshold": 1.5}


def test_param_extraction_no_params():
    """Strategies without numeric defaults should return an empty dict."""
    assert extract_numeric_parameters(NoNumericParamsStrategy) == {}


def test_perturbation_range():
    """Parameter values should span the full perturbation range."""
    values = generate_parameter_values(default_value=20, perturbation=0.2, steps=5)
    assert values[0] == 16.0
    assert values[-1] == 24.0


def test_perturbation_steps():
    """The number of generated values should match the requested steps."""
    values = generate_parameter_values(default_value=20, perturbation=0.2, steps=7)
    assert len(values) == 7


def test_stability_score_range():
    """Every reported stability score should be a probability."""
    result = parameter_stability_test(
        TunableStrategy,
        data_config={},
        evaluator=lambda strategy, _: 1.0,
    )

    assert 0.0 <= result["overall_stability"] <= 1.0
    assert all(0.0 <= metrics["stability"] <= 1.0 for metrics in result["parameters"].values())


def test_stability_high_stability():
    """Flat performance surface should produce near-perfect stability."""
    result = parameter_stability_test(
        TunableStrategy,
        data_config={},
        evaluator=lambda strategy, _: 1.0,
    )

    assert result["overall_stability"] == 1.0


def test_stability_flat_zero_surface_is_stable():
    """A perfectly flat zero-Sharpe surface should still count as stable."""
    result = parameter_stability_test(
        TunableStrategy,
        data_config={},
        evaluator=lambda strategy, _: 0.0,
    )

    assert result["overall_stability"] == 1.0


def test_stability_flat_negative_surface_is_stable():
    """A perfectly flat negative surface is stable even if performance is poor."""
    result = parameter_stability_test(
        TunableStrategy,
        data_config={},
        evaluator=lambda strategy, _: -1.0,
    )

    assert result["overall_stability"] == 1.0
    assert result["verdict"] == "GOOD"


def test_stability_low_stability():
    """A sharp optimum should produce low stability."""

    def evaluator(strategy, _):
        return 1.0 if strategy.lookback == 20 else 0.1

    result = parameter_stability_test(
        TunableStrategy,
        data_config={},
        perturbation=0.2,
        steps=5,
        evaluator=evaluator,
    )

    assert result["parameters"]["lookback"]["stability"] == 0.2


def test_overall_stability_is_mean():
    """Overall stability should be the mean of per-parameter stabilities."""

    def evaluator(strategy, _):
        lookback_score = 1.0 if strategy.lookback == 20 else 0.1
        threshold_score = 1.0 if strategy.threshold in (1.35, 1.5, 1.65) else 0.1
        return min(lookback_score, threshold_score)

    result = parameter_stability_test(
        TunableStrategy,
        data_config={},
        perturbation=0.2,
        steps=5,
        evaluator=evaluator,
    )

    expected_mean = np.mean(
        [
            result["parameters"]["lookback"]["stability"],
            result["parameters"]["threshold"]["stability"],
        ]
    )
    assert result["overall_stability"] == expected_mean
