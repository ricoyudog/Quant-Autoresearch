import inspect

import numpy as np


def extract_numeric_parameters(strategy_class) -> dict[str, int | float]:
    """Extract numeric __init__ defaults from a strategy class."""
    signature = inspect.signature(strategy_class.__init__)
    parameters = {}

    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        default = parameter.default
        if isinstance(default, bool):
            continue
        if isinstance(default, (int, float)):
            parameters[name] = default

    return parameters


def generate_parameter_values(default_value: int | float, perturbation: float, steps: int) -> list[float]:
    """Generate evenly spaced parameter values around the default."""
    if steps <= 0:
        raise ValueError("steps must be positive")

    start = default_value * (1 - perturbation)
    end = default_value * (1 + perturbation)
    return [float(value) for value in np.linspace(start, end, steps)]


def _default_evaluator(strategy, data_config) -> float:
    """Evaluate a perturbed strategy instance with the existing backtester."""
    from core.backtester import run_backtest

    if not data_config:
        return 0.0

    min_length = min(len(df) for df in data_config.values() if df is not None)
    if min_length < 3:
        return 0.0

    start_idx = max(1, min_length // 5)
    end_idx = min_length
    sharpe, _, _ = run_backtest(strategy, data_config, start_idx, end_idx)
    return float(sharpe)


def _stability_verdict(overall_stability: float) -> str:
    """Map an overall stability score to a qualitative verdict."""
    if overall_stability >= 0.7:
        return "GOOD"
    if overall_stability >= 0.5:
        return "MODERATE"
    return "POOR"


def parameter_stability_test(
    strategy_class,
    data_config,
    perturbation: float = 0.2,
    steps: int = 5,
    evaluator=None,
):
    """Evaluate how stable strategy performance is under parameter perturbations."""
    parameters = extract_numeric_parameters(strategy_class)
    if not parameters:
        return {
            "overall_stability": 1.0,
            "parameters": {},
            "verdict": "GOOD",
            "message": "no tuneable parameters",
        }

    scoring_function = evaluator or _default_evaluator
    parameter_results = {}

    for parameter_name, default_value in parameters.items():
        sharpes = []
        original_type = type(default_value)
        for value in generate_parameter_values(default_value, perturbation, steps):
            if original_type is int:
                candidate_value = int(round(value))
            else:
                candidate_value = float(value)

            strategy = strategy_class(**{parameter_name: candidate_value})
            sharpes.append(float(scoring_function(strategy, data_config)))

        peak_sharpe = max(sharpes) if sharpes else 0.0
        threshold = peak_sharpe * 0.5
        stable_count = sum(1 for sharpe in sharpes if sharpe >= threshold)
        stability = stable_count / len(sharpes) if sharpes else 1.0
        parameter_results[parameter_name] = {
            "stability": float(stability),
            "peak_sharpe": float(peak_sharpe),
            "min_sharpe": float(min(sharpes)) if sharpes else 0.0,
            "sharpes": sharpes,
        }

    overall_stability = float(
        np.mean([metrics["stability"] for metrics in parameter_results.values()])
    )
    return {
        "overall_stability": overall_stability,
        "parameters": parameter_results,
        "verdict": _stability_verdict(overall_stability),
        "message": "",
    }
