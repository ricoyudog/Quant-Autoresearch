from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_runner_module():
    spec = importlib.util.spec_from_file_location(
        "autoresearch_runner",
        Path("scripts/autoresearch_runner.py"),
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_backtest_metrics_extracts_required_values():
    runner = _load_runner_module()

    output = """
---
SCORE: 0.7521
NAIVE_SHARPE: 0.8811
NW_SHARPE_BIAS: 0.1290
DEFLATED_SR: 0.6200
BASELINE_SHARPE: 0.4500
---
""".strip()

    metrics = runner.parse_backtest_metrics(output, previous_best=0.62)

    assert metrics["score"] == 0.7521
    assert metrics["baseline_sharpe"] == 0.45
    assert metrics["previous_best"] == 0.62
    assert metrics["naive_sharpe"] == 0.8811
    assert metrics["nw_sharpe_bias"] == 0.129
    assert metrics["deflated_sr"] == 0.62


def test_parse_backtest_metrics_requires_score_and_baseline():
    runner = _load_runner_module()

    with pytest.raises(ValueError, match="Missing required backtest metrics"):
        runner.parse_backtest_metrics("SCORE: 0.75")


def test_normalize_backtest_decision_keeps_when_thresholds_are_beaten():
    runner = _load_runner_module()

    output = """
SCORE: 0.81
BASELINE_SHARPE: 0.45
DEFLATED_SR: 0.72
NW_SHARPE_BIAS: 0.08
""".strip()

    decision = runner.normalize_backtest_decision(output, previous_best=0.62)

    assert decision["decision"] == "keep"
    assert decision["score"] == 0.81
    assert decision["baseline_sharpe"] == 0.45
    assert decision["previous_best"] == 0.62


def test_normalize_backtest_decision_reverts_when_score_does_not_beat_previous_best():
    runner = _load_runner_module()

    output = """
SCORE: 0.60
BASELINE_SHARPE: 0.45
DEFLATED_SR: 0.91
NW_SHARPE_BIAS: 0.01
""".strip()

    decision = runner.normalize_backtest_decision(output, previous_best=0.62)

    assert decision["decision"] == "revert"
    assert "score_not_above_previous_best" in decision["reasons"]
