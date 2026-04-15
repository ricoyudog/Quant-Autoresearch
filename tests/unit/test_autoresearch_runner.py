from __future__ import annotations

import json
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


def test_build_parser_accepts_continuation_manifest_option():
    runner = _load_runner_module()

    args = runner.build_parser().parse_args(
        ["--iterations", "2", "--continuation-manifest", "tmp/manifest.json"]
    )

    assert args.continuation_manifest == "tmp/manifest.json"


def test_summarize_contract_reports_continuation_manifest_context(tmp_path):
    runner = _load_runner_module()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "current_baseline": {"title": "Minimum Hold Duration v1"},
                "failed_branches": [{"title": "Overfit Revert"}],
                "next_recommended_experiment": "Test a momentum-strength threshold",
            }
        )
    )

    args = runner.build_parser().parse_args(
        [
            "--iterations",
            "2",
            "--continuation-manifest",
            str(manifest_path),
            "--dry-run",
        ]
    )
    summary = runner.summarize_contract(args)

    assert f"continuation_manifest={manifest_path}" in summary
    assert "continuation_manifest_exists=True" in summary
    assert "continuation_current_baseline=Minimum Hold Duration v1" in summary
    assert "continuation_failed_branches=1" in summary
    assert "continuation_next_experiment=Test a momentum-strength threshold" in summary


def test_build_parser_accepts_artifact_context_options(tmp_path):
    runner = _load_runner_module()

    args = runner.build_parser().parse_args(
        [
            "--iterations",
            "2",
            "--program",
            "tmp/program.md",
            "--results-file",
            "tmp/results.tsv",
            "--notes-dir",
            "tmp/notes",
            "--recent-notes-limit",
            "5",
            "--claude-wrapper",
            "scripts/run_claude_iteration.sh",
        ]
    )

    assert args.program == "tmp/program.md"
    assert args.results_file == "tmp/results.tsv"
    assert args.notes_dir == "tmp/notes"
    assert args.recent_notes_limit == 5
    assert args.claude_wrapper == "scripts/run_claude_iteration.sh"


def test_execute_dry_run_writes_iteration_bundle(tmp_path):
    runner = _load_runner_module()
    strategy_path = tmp_path / "active_strategy.py"
    program_path = tmp_path / "program.md"
    results_path = tmp_path / "results.tsv"
    notes_dir = tmp_path / "notes"
    state_path = tmp_path / "state.json"
    iteration_root = tmp_path / "iterations"
    manifest_path = tmp_path / "manifest.json"

    strategy_path.write_text("class Strategy:\n    pass\n")
    program_path.write_text("# Program\n")
    results_path.write_text("commit\tscore\nabc\t1.0\n")
    notes_dir.mkdir()
    (notes_dir / "2026-04-15-minimum-hold.md").write_text("# Note\n")
    manifest_path.write_text(
        json.dumps(
            {
                "current_baseline": {
                    "title": "Experiment - Minimum Hold Duration v1",
                    "raw_note_path": "vault/experiments/minimum-hold.md",
                },
                "next_recommended_experiment": "Test a no-trade band",
                "failed_branches": [],
            }
        )
    )

    args = runner.build_parser().parse_args(
        [
            "--iterations",
            "1",
            "--strategy",
            str(strategy_path),
            "--program",
            str(program_path),
            "--results-file",
            str(results_path),
            "--notes-dir",
            str(notes_dir),
            "--state-file",
            str(state_path),
            "--iteration-root",
            str(iteration_root),
            "--continuation-manifest",
            str(manifest_path),
            "--claude-wrapper",
            str(Path("scripts/run_claude_iteration.sh").resolve()),
            "--dry-run",
        ]
    )

    exit_code = runner.execute_dry_run(args)

    run_dirs = list(iteration_root.glob("run-*/iteration-0001"))
    assert exit_code == 0
    assert len(run_dirs) == 1
    iteration_dir = run_dirs[0]
    assert (iteration_dir / "context.json").exists()
    assert (iteration_dir / "context.md").exists()
    assert (iteration_dir / "claude_prompt.md").exists()
    assert (iteration_dir / "decision.json").exists()
    assert (iteration_dir / "iteration_record.json").exists()
    assert (iteration_dir / "experiment_note_draft.md").exists()

    record = json.loads((iteration_dir / "iteration_record.json").read_text())
    assert record["artifact_status"] == "simulated"
    assert record["execution_mode"] == "dry_run"
    assert record["continuation_context"]["current_baseline"]["title"] == "Experiment - Minimum Hold Duration v1"
    assert record["artifact_paths"]["experiment_note_draft"].endswith("experiment_note_draft.md")

    draft = (iteration_dir / "experiment_note_draft.md").read_text()
    assert "pending_explicit_finalize" in draft
    assert "Current baseline: Experiment - Minimum Hold Duration v1" in draft
