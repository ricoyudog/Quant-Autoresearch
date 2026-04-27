from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

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


def _build_args(
    tmp_path: Path,
    *,
    iterations: int = 1,
    target_score: float | None = None,
    max_no_improve: int | None = None,
    recent_notes_limit: int = 3,
):
    strategy_path = tmp_path / "active_strategy.py"
    strategy_path.write_text("VALUE = 0\n")

    program_path = tmp_path / "program.md"
    program_path.write_text("# Program\n\nRespect deterministic evaluation.\n")

    results_path = tmp_path / "results.tsv"
    results_path.write_text(
        "commit\tscore\tbaseline_sharpe\tstatus\tdescription\n"
        "working\t0.500000\t0.400000\tpending\tbaseline\n"
    )

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "idea.md").write_text("# Idea\n\nTry a bounded improvement.\n")

    return argparse.Namespace(
        iterations=iterations,
        strategy=str(strategy_path),
        state_file=str(tmp_path / "autoresearch_state.json"),
        iteration_root=str(tmp_path / "iterations"),
        target_score=target_score,
        max_no_improve=max_no_improve,
        dry_run=False,
        program=str(program_path),
        results_file=str(results_path),
        notes_dir=str(notes_dir),
        recent_notes_limit=recent_notes_limit,
        claude_wrapper="scripts/run_claude_iteration.sh",
        continuation_manifest=str(tmp_path / "continuation.json"),
        status_only=False,
    )


def _command_arg(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


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



def test_parse_iteration_summary_preserves_strategy_knowledge_fields():
    """Iteration summaries should carry proofable idea and universe-selection explanations."""
    runner = _load_runner_module()
    payload = {
        "hypothesis": "Exploit volume-confirmed momentum after market-wide risk-on days.",
        "strategy_change_summary": "Rank daily momentum and trade intraday continuation.",
        "universe_selection_summary": "Select SPY plus liquid high-momentum stocks; ETFs are intentional regime instruments.",
        "proofable_idea_sources": ["vault/research/momentum.md", {"path": "vault/experiments/baseline.md"}],
        "files_touched": ["src/strategies/active_strategy.py"],
    }

    summary = runner.parse_iteration_summary(json.dumps(payload))

    assert summary["universe_selection_summary"] == payload["universe_selection_summary"]
    assert summary["proofable_idea_sources"] == payload["proofable_idea_sources"]


def test_parse_iteration_summary_defaults_missing_strategy_knowledge_fields():
    """Older wrapper output should stay parseable but be marked as unspecified."""
    runner = _load_runner_module()

    summary = runner.parse_iteration_summary(json.dumps({"hypothesis": "h", "strategy_change_summary": "s"}))

    assert summary["universe_selection_summary"] == "No universe selection summary reported."
    assert summary["proofable_idea_sources"] == []


def test_default_run_state_matches_expected_schema():
    runner = _load_runner_module()

    state = runner.default_run_state()

    assert state == {
        "run_id": None,
        "status": "pending",
        "current_iteration": 0,
        "iteration_budget": None,
        "target_score": None,
        "max_no_improve": None,
        "no_improve_streak": 0,
        "best_score": None,
        "best_iteration": None,
        "best_strategy_reference": None,
        "last_decision": None,
        "updated_at": None,
    }


def test_create_strategy_snapshot_uses_iteration_numbered_path(tmp_path):
    runner = _load_runner_module()

    strategy_path = tmp_path / "active_strategy.py"
    strategy_path.write_text("print('alpha')\n")

    snapshot = runner.create_strategy_snapshot(strategy_path, 12, tmp_path / "iterations")

    assert snapshot["snapshot_path"].endswith("iteration-0012-active_strategy.py")
    assert Path(snapshot["snapshot_path"]).read_text() == "print('alpha')\n"
    assert snapshot["restored"] is False


def test_restore_strategy_snapshot_requires_strategy_path_for_raw_snapshot(tmp_path):
    runner = _load_runner_module()

    snapshot_path = tmp_path / "snapshot.py"
    snapshot_path.write_text("print('alpha')\n")

    with pytest.raises(ValueError, match="strategy_file is required"):
        runner.restore_strategy_snapshot(snapshot_path)


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


def test_run_autoresearch_executes_bounded_multi_round_lifecycle(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=2, target_score=0.7)
    scores = iter([0.61, 0.74])

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            iteration = int(command[2])
            strategy_path = Path(_command_arg(command, "--strategy"))
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / f"iteration-{iteration:04d}"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            strategy_path.write_text(f"VALUE = {iteration}\n")
            stdout = json.dumps(
                {
                    "hypothesis": f"Round {iteration} hypothesis",
                    "strategy_change_summary": f"Set VALUE to {iteration}",
                }
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        score = next(scores)
        stdout = (
            f"SCORE: {score}\n"
            "BASELINE_SHARPE: 0.50\n"
            "DEFLATED_SR: 0.80\n"
            "NW_SHARPE_BIAS: 0.10\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    exit_code = runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    run_root = Path(args.iteration_root) / saved_state["run_id"]
    first_record = json.loads((run_root / "iteration-0001" / "iteration_record.json").read_text())
    second_record = json.loads((run_root / "iteration-0002" / "iteration_record.json").read_text())

    assert exit_code == 0
    assert saved_state["status"] == "completed"
    assert saved_state["current_iteration"] == 2
    assert saved_state["best_score"] == pytest.approx(0.74)
    assert saved_state["best_iteration"] == 2
    assert saved_state["last_decision"]["decision"] == "keep"
    assert first_record["decision"] == "keep"
    assert second_record["decision"] == "keep"
    assert first_record["hypothesis"] == "Round 1 hypothesis"
    assert second_record["strategy_change_summary"] == "Set VALUE to 2"
    assert (run_root / "iteration-0001" / "context.md").exists()
    assert (run_root / "iteration-0002" / "context.md").exists()


def test_keep_path_retains_strategy_and_updates_best_reference(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=1)

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            strategy_path = Path(_command_arg(command, "--strategy"))
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / "iteration-0001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            strategy_path.write_text("VALUE = 99\n")
            stdout = json.dumps(
                {
                    "hypothesis": "Improve entry timing",
                    "strategy_change_summary": "Set VALUE to 99",
                }
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        stdout = (
            "SCORE: 0.81\n"
            "BASELINE_SHARPE: 0.50\n"
            "DEFLATED_SR: 0.72\n"
            "NW_SHARPE_BIAS: 0.08\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    best_reference = Path(saved_state["best_strategy_reference"])

    assert Path(args.strategy).read_text() == "VALUE = 99\n"
    assert saved_state["best_score"] == pytest.approx(0.81)
    assert saved_state["no_improve_streak"] == 0
    assert best_reference.exists()
    assert best_reference.read_text() == "VALUE = 99\n"


def test_revert_path_restores_prior_strategy_snapshot(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=1)
    Path(args.strategy).write_text("VALUE = 7\n")

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            strategy_path = Path(_command_arg(command, "--strategy"))
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / "iteration-0001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            strategy_path.write_text("VALUE = 99\n")
            stdout = json.dumps(
                {
                    "hypothesis": "Try a noisy tweak",
                    "strategy_change_summary": "Set VALUE to 99",
                }
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        stdout = (
            "SCORE: 0.35\n"
            "BASELINE_SHARPE: 0.40\n"
            "DEFLATED_SR: 0.70\n"
            "NW_SHARPE_BIAS: 0.05\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    iteration_record = json.loads(
        (Path(args.iteration_root) / saved_state["run_id"] / "iteration-0001" / "iteration_record.json").read_text()
    )

    assert Path(args.strategy).read_text() == "VALUE = 7\n"
    assert saved_state["best_score"] is None
    assert saved_state["no_improve_streak"] == 1
    assert saved_state["last_decision"]["decision"] == "revert"
    assert iteration_record["decision"] == "revert"
    assert iteration_record["snapshot"]["restored"] is True


def test_resume_uses_recorded_best_strategy_reference_before_next_round(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=2)

    run_root = Path(args.iteration_root) / "run-existing"
    retained_dir = run_root / "retained"
    retained_dir.mkdir(parents=True, exist_ok=True)
    best_reference = retained_dir / "iteration-0001-active_strategy.py"
    best_reference.write_text("VALUE = 21\n")
    Path(args.strategy).write_text("VALUE = -5\n")
    Path(args.state_file).write_text(
        json.dumps(
            {
                "run_id": "run-existing",
                "status": "running",
                "current_iteration": 1,
                "iteration_budget": 2,
                "target_score": None,
                "max_no_improve": None,
                "no_improve_streak": 0,
                "best_score": 0.63,
                "best_iteration": 1,
                "best_strategy_reference": str(best_reference),
                "last_decision": {"decision": "keep", "score": 0.63},
                "updated_at": "2026-04-13T00:00:00+00:00",
            },
            indent=2,
        )
    )

    observed_pre_edit = []

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            strategy_path = Path(_command_arg(command, "--strategy"))
            observed_pre_edit.append(strategy_path.read_text())
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / "iteration-0002"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            strategy_path.write_text("VALUE = 22\n")
            stdout = json.dumps(
                {
                    "hypothesis": "Resume from best retained baseline",
                    "strategy_change_summary": "Set VALUE to 22",
                }
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        stdout = (
            "SCORE: 0.80\n"
            "BASELINE_SHARPE: 0.50\n"
            "DEFLATED_SR: 0.83\n"
            "NW_SHARPE_BIAS: 0.04\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())

    assert observed_pre_edit == ["VALUE = 21\n"]
    assert saved_state["current_iteration"] == 2
    assert saved_state["best_score"] == pytest.approx(0.80)
    assert Path(args.strategy).read_text() == "VALUE = 22\n"


def test_invalid_backtest_output_reverts_strategy_and_records_failed_decision(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=1)
    Path(args.strategy).write_text("VALUE = 7\n")

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            strategy_path = Path(_command_arg(command, "--strategy"))
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / "iteration-0001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            strategy_path.write_text("VALUE = 100\n")
            stdout = json.dumps(
                {
                    "hypothesis": "Try a malformed evaluator round",
                    "strategy_change_summary": "Set VALUE to 100",
                }
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        stdout = "SCORE: 0.91\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    iteration_record = json.loads(
        (Path(args.iteration_root) / saved_state["run_id"] / "iteration-0001" / "iteration_record.json").read_text()
    )

    assert Path(args.strategy).read_text() == "VALUE = 7\n"
    assert saved_state["last_decision"]["decision"] == "failed"
    assert saved_state["no_improve_streak"] == 1
    assert iteration_record["decision"] == "failed"
    assert "backtest_output_invalid" in iteration_record["decision_reason"]
    assert iteration_record["snapshot"]["restored"] is True


def test_run_autoresearch_retries_rate_limit_then_completes_iteration(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=1)
    wrapper_calls = []
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    responses = iter(
        [
            subprocess.CompletedProcess(
                ["bash", "scripts/run_claude_iteration.sh"],
                1,
                stdout=(
                    "Claude Code iteration wrapper\n"
                    "API Error: 429 "
                    '{"error":{"code":"1302","message":"Rate limit reached for requests"}}'
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                ["bash", "scripts/run_claude_iteration.sh"],
                0,
                stdout=json.dumps(
                    {
                        "hypothesis": "Retry after rate limit",
                        "strategy_change_summary": "Keep existing strategy unchanged",
                    }
                ),
                stderr="",
            ),
        ]
    )

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            wrapper_calls.append(list(command))
            return next(responses)

        stdout = (
            "SCORE: 0.81\n"
            "BASELINE_SHARPE: 0.50\n"
            "DEFLATED_SR: 0.72\n"
            "NW_SHARPE_BIAS: 0.08\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)
    monkeypatch.setattr(runner.time, "sleep", fake_sleep)

    exit_code = runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    iteration_record = json.loads(
        (Path(args.iteration_root) / saved_state["run_id"] / "iteration-0001" / "iteration_record.json").read_text()
    )

    assert exit_code == 0
    assert len(wrapper_calls) == 2
    assert sleep_calls == [runner.CLAUDE_RETRY_BASE_DELAY_SECONDS]
    assert saved_state["status"] == "completed"
    assert saved_state["current_iteration"] == 1
    assert saved_state["no_improve_streak"] == 0
    assert saved_state["last_decision"]["decision"] == "keep"
    assert iteration_record["decision"] == "keep"
    assert iteration_record["claude_attempts"] == 2
    assert iteration_record["claude_retry_delays"] == [runner.CLAUDE_RETRY_BASE_DELAY_SECONDS]


def test_run_autoresearch_blocks_on_persistent_rate_limit_without_consuming_iteration(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=3, max_no_improve=2)
    wrapper_calls = []
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            wrapper_calls.append(list(command))
            return subprocess.CompletedProcess(
                command,
                1,
                stdout=(
                    "Claude Code iteration wrapper\n"
                    "API Error: 429 "
                    '{"error":{"code":"1302","message":"Rate limit reached for requests"}}'
                ),
                stderr="",
            )

        pytest.fail("Backtest should not run when Claude is still rate limited")

    monkeypatch.setattr(runner, "run_command", fake_run_command)
    monkeypatch.setattr(runner.time, "sleep", fake_sleep)

    exit_code = runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    run_root = Path(args.iteration_root) / saved_state["run_id"]
    iteration_record = json.loads((run_root / "iteration-0001" / "iteration_record.json").read_text())

    assert exit_code == 1
    assert len(wrapper_calls) == runner.CLAUDE_MAX_RETRY_ATTEMPTS
    assert sleep_calls == [
        runner.CLAUDE_RETRY_BASE_DELAY_SECONDS,
        runner.CLAUDE_RETRY_BASE_DELAY_SECONDS * 2,
    ]
    assert saved_state["status"] == "blocked"
    assert saved_state["stop_reason"] == "claude_rate_limited"
    assert saved_state["current_iteration"] == 0
    assert saved_state["no_improve_streak"] == 0
    assert saved_state["active_iteration"] is None
    assert saved_state["last_decision"]["decision"] == "failed"
    assert "claude_iteration_rate_limited" in saved_state["last_decision"]["reasons"]
    assert iteration_record["decision"] == "failed"
    assert iteration_record["claude_attempts"] == runner.CLAUDE_MAX_RETRY_ATTEMPTS
    assert iteration_record["claude_retry_delays"] == [
        runner.CLAUDE_RETRY_BASE_DELAY_SECONDS,
        runner.CLAUDE_RETRY_BASE_DELAY_SECONDS * 2,
    ]
    assert iteration_record["snapshot"]["restored"] is True
    assert iteration_record["artifact_status"] == "blocked"
    assert iteration_record["canonical_note_status"]["status"] == "skipped"
    assert "pre-evidence blocked" in iteration_record["canonical_note_status"]["reason"]
    assert "raw_experiment_note" not in iteration_record["artifact_paths"]
    assert "continuation_refresh" not in iteration_record
    assert not (run_root / "rejection_map.json").exists()


def test_worker_failure_skips_canonical_memory_promotion(tmp_path, monkeypatch):
    """Worker failures before candidate evidence should remain runtime audit, not experiment memory."""
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=1)

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            return subprocess.CompletedProcess(command, 2, stdout="", stderr="wrapper crashed before candidate")

        pytest.fail("Backtest should not run when the iteration worker fails before producing a candidate")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    exit_code = runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    run_root = Path(args.iteration_root) / saved_state["run_id"]
    iteration_record = json.loads((run_root / "iteration-0001" / "iteration_record.json").read_text())

    assert exit_code == 0
    assert saved_state["current_iteration"] == 1
    assert iteration_record["artifact_status"] == "blocked"
    assert iteration_record["canonical_note_status"]["status"] == "skipped"
    assert "worker failed before producing" in iteration_record["canonical_note_status"]["reason"]
    assert "raw_experiment_note" not in iteration_record["artifact_paths"]
    assert "continuation_refresh" not in iteration_record
    assert not (run_root / "rejection_map.json").exists()


def test_main_status_only_does_not_require_iterations(tmp_path, capsys):
    runner = _load_runner_module()
    state_path = tmp_path / "autoresearch_state.json"
    state_path.write_text(
        json.dumps(
            {
                "run_id": "run-existing",
                "status": "running",
                "current_iteration": 2,
                "iteration_budget": 5,
                "best_score": 0.81,
                "best_iteration": 2,
                "no_improve_streak": 0,
                "stop_reason": None,
                "last_decision": {"decision": "keep", "score": 0.81},
            }
        )
    )

    exit_code = runner.main(["--status-only", "--state-file", str(state_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run_id=run-existing" in captured.out
    assert "status=running" in captured.out


def test_load_or_initialize_run_preserves_persisted_stop_conditions_when_not_overridden(tmp_path):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=4)
    Path(args.state_file).write_text(
        json.dumps(
            {
                "run_id": "run-existing",
                "status": "running",
                "current_iteration": 1,
                "iteration_budget": 4,
                "target_score": 0.7,
                "max_no_improve": 2,
                "no_improve_streak": 1,
                "best_score": 0.6,
                "best_iteration": 1,
                "best_strategy_reference": None,
                "last_decision": {"decision": "keep", "score": 0.6},
            },
            indent=2,
        )
    )

    state = runner.load_or_initialize_run(args)

    assert state["target_score"] == pytest.approx(0.7)
    assert state["max_no_improve"] == 2


def test_load_or_initialize_run_clears_prior_stop_reason_when_resuming(tmp_path):
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=3)
    Path(args.state_file).write_text(
        json.dumps(
            {
                "run_id": "run-blocked",
                "status": "blocked",
                "current_iteration": 0,
                "iteration_budget": 3,
                "target_score": None,
                "max_no_improve": 2,
                "no_improve_streak": 0,
                "best_score": None,
                "best_iteration": None,
                "best_strategy_reference": None,
                "last_decision": {"decision": "failed"},
                "stop_reason": "claude_rate_limited",
            },
            indent=2,
        )
    )

    state = runner.load_or_initialize_run(args)

    assert state["status"] == "running"
    assert state["stop_reason"] is None


def test_should_stop_does_not_end_fresh_run_when_max_no_improve_is_zero():
    runner = _load_runner_module()

    should_end, stop_reason = runner.should_stop(
        {
            "current_iteration": 0,
            "iteration_budget": 3,
            "best_score": None,
            "target_score": None,
            "max_no_improve": 0,
            "no_improve_streak": 0,
        }
    )

    assert should_end is False
    assert stop_reason is None


def test_should_stop_ends_after_first_non_improving_round_when_max_no_improve_is_zero():
    runner = _load_runner_module()

    should_end, stop_reason = runner.should_stop(
        {
            "current_iteration": 1,
            "iteration_budget": 3,
            "best_score": None,
            "target_score": None,
            "max_no_improve": 0,
            "no_improve_streak": 1,
        }
    )

    assert should_end is True
    assert stop_reason == "max_no_improve_reached"


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
            "--program",
            "program.md",
            "--results-file",
            "experiments/results.tsv",
            "--notes-dir",
            "experiments/notes",
            "--claude-wrapper",
            "scripts/run_claude_iteration.sh",
        ]
    )
    summary = runner.summarize_contract(args)

    assert f"continuation_manifest={manifest_path}" in summary
    assert "continuation_manifest_exists=True" in summary
    assert "continuation_current_baseline=Minimum Hold Duration v1" in summary
    assert "continuation_failed_branches=1" in summary
    assert "continuation_next_experiment=Test a momentum-strength threshold" in summary


def test_execute_dry_run_writes_iteration_bundle(tmp_path):
    runner = _load_runner_module()
    strategy_path = tmp_path / "active_strategy.py"
    strategy_path.write_text("class Strategy:\n    pass\n")
    program_path = tmp_path / "program.md"
    program_path.write_text("# Program\n")
    results_path = tmp_path / "results.tsv"
    results_path.write_text("commit\tscore\nabc\t1.0\n")
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "2026-04-15-minimum-hold.md").write_text("# Note\n")
    manifest_path = tmp_path / "manifest.json"
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
            "--iterations", "1",
            "--strategy", str(strategy_path),
            "--program", str(program_path),
            "--results-file", str(results_path),
            "--notes-dir", str(notes_dir),
            "--state-file", str(tmp_path / "state.json"),
            "--iteration-root", str(tmp_path / "iterations"),
            "--continuation-manifest", str(manifest_path),
            "--claude-wrapper", str(Path("scripts/run_claude_iteration.sh").resolve()),
            "--dry-run",
        ]
    )

    exit_code = runner.execute_dry_run(args)
    run_dirs = list((tmp_path / "iterations").glob("run-*/iteration-0001"))

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


def test_run_autoresearch_writes_universe_selection_and_raw_note(tmp_path, monkeypatch):
    """A live completed round should link summary, universe audit, raw note, and continuation refresh evidence."""
    runner = _load_runner_module()
    vault_root = tmp_path / "vault"
    notes_dir = vault_root / "quant-autoresearch" / "experiments"
    notes_dir.mkdir(parents=True)
    args = _build_args(tmp_path, iterations=1)
    args.notes_dir = str(notes_dir)
    args.continuation_manifest = str(tmp_path / "current_research_base.json")
    Path(args.strategy).write_text("VALUE = 7\n")

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            strategy_path = Path(_command_arg(command, "--strategy"))
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / "iteration-0001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            strategy_path.write_text("VALUE = 42\n")
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(
                    {
                        "hypothesis": "ETF-aware continuation idea",
                        "strategy_change_summary": "Select ETF plus stock momentum basket",
                        "universe_selection_summary": "SPY is intentionally selected as an ETF regime anchor.",
                        "proofable_idea_sources": ["vault/research/etf-momentum.md"],
                        "files_touched": [str(strategy_path)],
                    }
                ),
                stderr="",
            )

        universe_path = Path(env["BACKTEST_UNIVERSE_SELECTION_PATH"])
        universe_path.write_text(
            json.dumps(
                {
                    "instrument_scope": "stocks_or_etfs",
                    "universe_size_cap": None,
                    "selection_thesis": "SPY is intentionally selected as an ETF regime anchor.",
                    "windows": [
                        {
                            "window_index": 1,
                            "raw_selected_tickers": ["SPY", "AAPL"],
                            "selected_tickers": ["SPY", "AAPL"],
                        }
                    ],
                }
            )
        )
        stdout = "SCORE: 0.81\nBASELINE_SHARPE: 0.50\nDEFLATED_SR: 0.72\nNW_SHARPE_BIAS: 0.08\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))
    monkeypatch.setattr(runner, "run_command", fake_run_command)

    exit_code = runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    run_root = Path(args.iteration_root) / saved_state["run_id"]
    iteration_dir = run_root / "iteration-0001"
    record = json.loads((iteration_dir / "iteration_record.json").read_text())
    raw_notes = sorted(notes_dir.glob("*.md"))
    manifest = json.loads(Path(args.continuation_manifest).read_text())

    assert exit_code == 0
    assert (iteration_dir / "universe_selection.json").exists()
    assert record["summary"]["universe_selection_summary"].startswith("SPY is intentionally")
    assert record["summary"]["proofable_idea_sources"] == ["vault/research/etf-momentum.md"]
    assert record["artifact_paths"]["universe_selection"].endswith("universe_selection.json")
    assert record["artifact_paths"]["raw_experiment_note"].endswith(raw_notes[0].name)
    raw_note_text = raw_notes[0].read_text()
    assert raw_note_text.count("SPY is intentionally selected") >= 1
    assert "baseline_reference:" in raw_note_text
    assert "analysis_context:" in raw_note_text
    assert "idea_trace:" in raw_note_text
    assert "turnover_fee_lesson:" in raw_note_text
    assert "next_experiment:" in raw_note_text
    assert "raw_note_path:" in raw_note_text
    assert str(raw_notes[0]) in raw_note_text
    assert "## Unrestricted Result" in raw_note_text
    assert "## Turnover / Fee Lesson" in raw_note_text
    assert manifest["experiments"][0]["universe_selection_summary"].startswith("SPY is intentionally")


def test_revert_round_updates_rejection_map_for_next_iteration(tmp_path, monkeypatch):
    """A reverted candidate should be persisted as anti-repeat guidance for later contexts."""
    runner = _load_runner_module()
    args = _build_args(tmp_path, iterations=1)
    Path(args.strategy).write_text("VALUE = 7\n")

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            strategy_path = Path(_command_arg(command, "--strategy"))
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / "iteration-0001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            strategy_path.write_text("VALUE = 99\n")
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(
                    {
                        "hypothesis": "Repeat a high-churn momentum variant",
                        "strategy_change_summary": "Raised churn via narrow momentum threshold",
                        "universe_selection_summary": "Select high-churn momentum names from the daily cache.",
                    }
                ),
                stderr="",
            )

        Path(env["BACKTEST_UNIVERSE_SELECTION_PATH"]).write_text(
            json.dumps({"windows": [{"selected_tickers": ["AAA"], "raw_selected_tickers": ["AAA"]}]})
        )
        stdout = "SCORE: 0.35\nBASELINE_SHARPE: 0.40\nDEFLATED_SR: 0.70\nNW_SHARPE_BIAS: 0.05\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    runner.run_autoresearch(args)

    saved_state = json.loads(Path(args.state_file).read_text())
    rejection_map = json.loads((Path(args.iteration_root) / saved_state["run_id"] / "rejection_map.json").read_text())

    assert rejection_map["rejections"][0]["decision"] == "revert"
    assert rejection_map["rejections"][0]["hypothesis"] == "Repeat a high-churn momentum variant"
    assert "score_not_above_baseline" in rejection_map["rejections"][0]["decision_reasons"]
    assert "avoid materially equivalent repeats" in rejection_map["anti_repeat_guidance"].lower()
