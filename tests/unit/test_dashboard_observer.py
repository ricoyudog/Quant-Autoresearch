from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.dashboard.observer import observe_dashboard_state


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _touch_at(path: Path, timestamp: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(path.read_text(encoding="utf-8") if path.exists() else "", encoding="utf-8")
    path.touch()
    path.chmod(0o644)
    import os

    os.utime(path, (timestamp, timestamp))


def _write_results_tsv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\t".join(
            [
                "commit",
                "score",
                "naive_sharpe",
                "deflated_sr",
                "sortino",
                "calmar",
                "drawdown",
                "max_dd_days",
                "trades",
                "win_rate",
                "profit_factor",
                "avg_win",
                "avg_loss",
                "baseline_sharpe",
                "nw_bias",
                "status",
                "description",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "working",
                "0.720000",
                "0.800000",
                "0.610000",
                "1.100000",
                "0.900000",
                "-0.080000",
                "12",
                "34",
                "0.590000",
                "1.400000",
                "0.020000",
                "-0.010000",
                "0.500000",
                "0.070000",
                "pending",
                "first round",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_multirow_results_tsv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\t".join(
            [
                "iteration",
                "commit",
                "score",
                "naive_sharpe",
                "deflated_sr",
                "sortino",
                "calmar",
                "drawdown",
                "max_dd_days",
                "trades",
                "win_rate",
                "profit_factor",
                "avg_win",
                "avg_loss",
                "baseline_sharpe",
                "nw_bias",
                "status",
                "description",
            ]
        )
        + "\n"
        + "\n".join(
            [
                "\t".join(
                    [
                        "1",
                        "first",
                        "0.720000",
                        "0.800000",
                        "0.610000",
                        "1.100000",
                        "0.900000",
                        "-0.080000",
                        "12",
                        "34",
                        "0.590000",
                        "1.400000",
                        "0.020000",
                        "-0.010000",
                        "0.500000",
                        "0.070000",
                        "kept",
                        "first round",
                    ]
                ),
                "\t".join(
                    [
                        "2",
                        "second",
                        "0.810000",
                        "0.900000",
                        "0.690000",
                        "1.200000",
                        "1.000000",
                        "-0.060000",
                        "10",
                        "24",
                        "0.630000",
                        "1.600000",
                        "0.025000",
                        "-0.008000",
                        "0.500000",
                        "0.050000",
                        "kept",
                        "second round",
                    ]
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_ambiguous_multirow_results_tsv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\t".join(
            [
                "commit",
                "score",
                "naive_sharpe",
                "deflated_sr",
                "sortino",
                "calmar",
                "drawdown",
                "max_dd_days",
                "trades",
                "win_rate",
                "profit_factor",
                "avg_win",
                "avg_loss",
                "baseline_sharpe",
                "nw_bias",
                "status",
                "description",
            ]
        )
        + "\n"
        + "\n".join(
            [
                "\t".join(
                    [
                        "unkeyed-first",
                        "0.720000",
                        "0.800000",
                        "0.610000",
                        "1.100000",
                        "0.900000",
                        "-0.080000",
                        "12",
                        "34",
                        "0.590000",
                        "1.400000",
                        "0.020000",
                        "-0.010000",
                        "0.500000",
                        "0.070000",
                        "kept",
                        "first round",
                    ]
                ),
                "\t".join(
                    [
                        "unkeyed-second",
                        "0.810000",
                        "0.900000",
                        "0.690000",
                        "1.200000",
                        "1.000000",
                        "-0.060000",
                        "10",
                        "24",
                        "0.630000",
                        "1.600000",
                        "0.025000",
                        "-0.008000",
                        "0.500000",
                        "0.050000",
                        "kept",
                        "second round",
                    ]
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_observe_dashboard_state_ingests_sources_and_uses_log_heartbeat(tmp_path):
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    repo_root = tmp_path
    run_root = repo_root / "experiments" / "iterations" / "run-001"
    iteration_dir = run_root / "iteration-0001"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-001",
            "status": "running",
            "current_iteration": 1,
            "active_iteration": 2,
            "iteration_budget": 5,
            "best_score": 0.72,
            "best_iteration": 1,
            "updated_at": "2026-04-19T11:59:00+00:00",
        },
    )
    _write_json(
        iteration_dir / "iteration_record.json",
        {
            "run_id": "run-001",
            "iteration_number": 1,
            "artifact_status": "completed",
            "execution_mode": "live",
            "summary": {
                "hypothesis": "Reduce turnover with a no-trade band",
                "strategy_change_summary": "Added a bounded entry threshold",
                "files_touched": ["src/strategies/active_strategy.py"],
            },
            "decision": "keep",
            "decision_reason": ["score_above_baseline_and_previous_best"],
            "artifact_paths": {
                "claude_stdout": str(iteration_dir / "claude.stdout.log"),
                "backtest_stdout": str(iteration_dir / "backtest.stdout.log"),
                "decision": str(iteration_dir / "decision.json"),
            },
        },
    )
    _write_json(
        iteration_dir / "decision.json",
        {
            "decision": "keep",
            "reasons": ["score_above_baseline_and_previous_best"],
            "score": 0.72,
            "baseline_sharpe": 0.5,
            "deflated_sr": 0.61,
        },
    )
    (iteration_dir / "claude.stdout.log").write_text("fresh heartbeat\n", encoding="utf-8")
    _touch_at(iteration_dir / "claude.stdout.log", now.timestamp() - 4)
    (iteration_dir / "backtest.stdout.log").write_text("SCORE: 0.72\n", encoding="utf-8")
    _touch_at(iteration_dir / "backtest.stdout.log", now.timestamp() - 30)
    _write_results_tsv(repo_root / "experiments" / "results.tsv")

    dashboard = observe_dashboard_state(repo_root, now=now, stale_after_seconds=60)

    assert dashboard["run"]["status"] == "Busy"
    assert dashboard["run"]["heartbeat"]["source_role"] == "log"
    assert dashboard["run"]["heartbeat"]["age_seconds"] == pytest.approx(4)
    assert dashboard["run"]["active_iteration"] == 2
    assert dashboard["iterations"][0]["status"] == "Kept"
    assert dashboard["iterations"][0]["hypothesis"] == "Reduce turnover with a no-trade band"
    assert dashboard["iterations"][0]["metrics"]["score"] == pytest.approx(0.72)
    assert dashboard["iterations"][0]["metrics"]["baseline_delta"] == pytest.approx(0.22)
    assert dashboard["ledger"]["rows"][0]["deflated_sr"] == pytest.approx(0.61)


def test_observe_dashboard_state_marks_stalled_when_heartbeat_is_stale(tmp_path):
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    repo_root = tmp_path
    iteration_dir = repo_root / "experiments" / "iterations" / "run-stale" / "iteration-0002"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-stale",
            "status": "running",
            "current_iteration": 1,
            "active_iteration": 2,
            "iteration_budget": 3,
            "updated_at": "2026-04-19T11:00:00+00:00",
        },
    )
    (iteration_dir / "claude.stdout.log").parent.mkdir(parents=True, exist_ok=True)
    (iteration_dir / "claude.stdout.log").write_text("old heartbeat\n", encoding="utf-8")
    _touch_at(iteration_dir / "claude.stdout.log", now.timestamp() - 7200)

    dashboard = observe_dashboard_state(repo_root, now=now, stale_after_seconds=300)

    assert dashboard["run"]["status"] == "Stalled"
    assert dashboard["run"]["diagnosis"]["reason"] == "heartbeat_stale"
    assert dashboard["run"]["diagnosis"]["affected_iteration"] == 2
    assert dashboard["run"]["heartbeat"]["source_role"] == "state"
    assert dashboard["run"]["heartbeat"]["age_seconds"] == pytest.approx(3600)


def test_observe_dashboard_state_explains_blocked_run_and_failed_iteration(tmp_path):
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    repo_root = tmp_path
    iteration_dir = repo_root / "experiments" / "iterations" / "run-blocked" / "iteration-0001"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-blocked",
            "status": "blocked",
            "current_iteration": 0,
            "active_iteration": None,
            "iteration_budget": 3,
            "stop_reason": "claude_rate_limited",
            "last_error": "claude_iteration_rate_limited; API limit",
            "last_decision": {
                "decision": "failed",
                "reasons": ["claude_iteration_rate_limited", "API limit"],
            },
            "updated_at": "2026-04-19T11:59:30+00:00",
        },
    )
    _write_json(
        iteration_dir / "iteration_record.json",
        {
            "run_id": "run-blocked",
            "iteration_number": 1,
            "artifact_status": "failed",
            "execution_mode": "live",
            "summary": {
                "hypothesis": "Try rate-limited iteration",
                "strategy_change_summary": "No change landed",
                "files_touched": [],
            },
            "decision": "failed",
            "decision_reason": ["claude_iteration_rate_limited", "API limit"],
            "artifact_paths": {},
        },
    )

    dashboard = observe_dashboard_state(repo_root, now=now, stale_after_seconds=300)

    assert dashboard["run"]["status"] == "Blocked"
    assert dashboard["run"]["diagnosis"]["reason"] == "claude_rate_limited"
    assert dashboard["run"]["diagnosis"]["details"] == ["claude_iteration_rate_limited", "API limit"]
    assert dashboard["iterations"][0]["status"] == "Failed"
    assert dashboard["iterations"][0]["decision_reasons"] == ["claude_iteration_rate_limited", "API limit"]


def test_observe_dashboard_state_marks_waiting_and_completed_runs_with_diagnosis(tmp_path):
    waiting_dashboard = observe_dashboard_state(tmp_path, now=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc))

    assert waiting_dashboard["run"]["status"] == "Waiting"
    assert waiting_dashboard["run"]["diagnosis"]["reason"] == "awaiting_state"

    _write_json(
        tmp_path / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-complete",
            "status": "completed",
            "current_iteration": 3,
            "active_iteration": None,
            "last_completed_iteration": 3,
            "stop_reason": "iteration_budget_reached",
            "updated_at": "2026-04-19T11:59:30+00:00",
        },
    )

    completed_dashboard = observe_dashboard_state(
        tmp_path,
        now=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
    )

    assert completed_dashboard["run"]["status"] == "Completed"
    assert completed_dashboard["run"]["diagnosis"]["reason"] == "iteration_budget_reached"
    assert completed_dashboard["run"]["diagnosis"]["details"] == ["last_completed_iteration=3"]


def test_observe_dashboard_state_tracks_partial_and_pending_iteration_diagnosis(tmp_path):
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    repo_root = tmp_path
    partial_dir = repo_root / "experiments" / "iterations" / "run-partial" / "iteration-0001"
    pending_dir = repo_root / "experiments" / "iterations" / "run-partial" / "iteration-0002"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-partial",
            "status": "running",
            "current_iteration": 2,
            "active_iteration": 2,
            "updated_at": "2026-04-19T11:59:30+00:00",
        },
    )
    (partial_dir / "claude.stdout.log").parent.mkdir(parents=True, exist_ok=True)
    (partial_dir / "claude.stdout.log").write_text("iteration still working\n", encoding="utf-8")
    _touch_at(partial_dir / "claude.stdout.log", now.timestamp() - 5)
    (partial_dir / "context.json").write_text("{}", encoding="utf-8")

    _write_json(
        pending_dir / "iteration_record.json",
        {
            "run_id": "run-partial",
            "iteration_number": 2,
            "artifact_status": "completed",
            "execution_mode": "live",
            "summary": {
                "hypothesis": "Need evaluator decision",
                "strategy_change_summary": "Candidate change landed",
                "files_touched": ["src/strategies/active_strategy.py"],
            },
            "evaluation_summary": {"score": 0.55, "baseline_sharpe": 0.50},
            "artifact_paths": {
                "context_json": str(pending_dir / "context.json"),
            },
        },
    )
    (pending_dir / "context.json").write_text("{}", encoding="utf-8")

    dashboard = observe_dashboard_state(repo_root, now=now, stale_after_seconds=60)
    partial = dashboard["iterations"][0]
    pending = dashboard["iterations"][1]

    assert partial["status"] == "In Progress"
    assert partial["diagnosis"]["reason"] == "artifacts_pending"
    assert "decision" in partial["diagnosis"]["missing_artifacts"]
    assert "iteration_record" in partial["diagnosis"]["missing_artifacts"]

    assert pending["status"] == "Decision Pending"
    assert pending["diagnosis"]["reason"] == "decision_pending"
    assert pending["diagnosis"]["details"] == ["Awaiting decision artifact or final keep/revert outcome."]


def test_observe_dashboard_state_adds_iteration_analysis_comparisons(tmp_path):
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    repo_root = tmp_path
    first_dir = repo_root / "experiments" / "iterations" / "run-compare" / "iteration-0001"
    second_dir = repo_root / "experiments" / "iterations" / "run-compare" / "iteration-0002"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-compare",
            "status": "running",
            "current_iteration": 2,
            "active_iteration": None,
            "best_score": 0.81,
            "best_iteration": 2,
            "updated_at": "2026-04-19T11:59:30+00:00",
        },
    )
    _write_json(
        first_dir / "iteration_record.json",
        {
            "run_id": "run-compare",
            "iteration_number": 1,
            "artifact_status": "completed",
            "summary": {
                "hypothesis": "Reduce turnover with a no-trade band",
                "strategy_change_summary": "Added a bounded entry threshold",
                "files_touched": ["src/strategies/active_strategy.py"],
            },
            "decision": "keep",
            "decision_reason": ["score_above_baseline_and_previous_best"],
        },
    )
    _write_json(
        second_dir / "iteration_record.json",
        {
            "run_id": "run-compare",
            "iteration_number": 2,
            "artifact_status": "completed",
            "summary": {
                "hypothesis": "Tighten the no-trade band during low-volatility windows",
                "strategy_change_summary": "Reduced turnover by gating entries on realized volatility",
                "files_touched": ["src/strategies/active_strategy.py", "config/strategy.json"],
            },
            "decision": "keep",
            "decision_reason": ["score_above_previous_iteration", "turnover_reduced"],
            "artifact_paths": {
                "context_json": str(second_dir / "context.json"),
                "backtest_stdout": str(second_dir / "backtest.stdout.log"),
            },
        },
    )
    (second_dir / "context.json").write_text("{}", encoding="utf-8")
    (second_dir / "backtest.stdout.log").write_text("SCORE: 0.81\n", encoding="utf-8")
    _write_multirow_results_tsv(repo_root / "experiments" / "results.tsv")

    dashboard = observe_dashboard_state(repo_root, now=now, stale_after_seconds=60)
    second = dashboard["iterations"][1]

    assert "Previous: Reduce turnover with a no-trade band" in second["analysis"]["hypothesis_diff"]
    assert "Current: Tighten the no-trade band during low-volatility windows" in second["analysis"]["hypothesis_diff"]
    assert "config/strategy.json" in second["analysis"]["strategy_diff"]
    assert second["artifact_references"][0]["name"] == "context_json"
    assert [comparison["label"] for comparison in second["metric_breakdown"]["comparisons"]] == [
        "vs previous iteration",
        "vs current baseline",
        "vs best iteration in current run",
    ]
    assert second["metric_breakdown"]["comparisons"][0]["deltas"]["score"] == pytest.approx(0.09)
    assert second["metric_breakdown"]["comparisons"][1]["deltas"]["score"] == pytest.approx(0.31)
    assert second["metric_breakdown"]["comparisons"][2]["reference_iteration"] == 2


def test_observe_dashboard_state_resolves_repo_relative_artifact_paths(tmp_path):
    repo_root = tmp_path
    iteration_dir = repo_root / "experiments" / "iterations" / "run-relative" / "iteration-0001"
    repo_relative_context = Path("experiments/iterations/run-relative/iteration-0001/context.json")
    repo_relative_report = Path("experiments/reports/run-relative-summary.md")

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-relative",
            "status": "running",
            "current_iteration": 1,
            "active_iteration": 1,
            "updated_at": "2026-04-19T11:59:30+00:00",
        },
    )
    _write_json(
        iteration_dir / "iteration_record.json",
        {
            "run_id": "run-relative",
            "iteration_number": 1,
            "artifact_status": "completed",
            "decision": "keep",
            "artifact_paths": {
                "context_json": str(repo_relative_context),
                "summary_report": str(repo_relative_report),
            },
        },
    )
    _write_json(repo_root / repo_relative_context, {"iteration": 1})
    (repo_root / repo_relative_report).parent.mkdir(parents=True, exist_ok=True)
    (repo_root / repo_relative_report).write_text("# Summary\n", encoding="utf-8")

    dashboard = observe_dashboard_state(
        repo_root,
        now=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
        stale_after_seconds=60,
    )

    references = {item["name"]: item for item in dashboard["iterations"][0]["artifact_references"]}
    assert references["context_json"]["path"] == str(repo_root / repo_relative_context)
    assert references["context_json"]["exists"] is True
    assert references["summary_report"]["path"] == str(repo_root / repo_relative_report)
    assert references["summary_report"]["exists"] is True


def test_observe_dashboard_state_withholds_ambiguous_ledger_metrics(tmp_path):
    repo_root = tmp_path
    first_dir = repo_root / "experiments" / "iterations" / "run-ambiguous" / "iteration-0001"
    second_dir = repo_root / "experiments" / "iterations" / "run-ambiguous" / "iteration-0002"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-ambiguous",
            "status": "running",
            "current_iteration": 2,
            "active_iteration": None,
            "updated_at": "2026-04-19T11:59:30+00:00",
        },
    )
    for iteration_number, iteration_dir in ((1, first_dir), (2, second_dir)):
        _write_json(
            iteration_dir / "iteration_record.json",
            {
                "run_id": "run-ambiguous",
                "iteration_number": iteration_number,
                "artifact_status": "completed",
                "decision": "keep",
            },
        )
    _write_ambiguous_multirow_results_tsv(repo_root / "experiments" / "results.tsv")

    dashboard = observe_dashboard_state(
        repo_root,
        now=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
        stale_after_seconds=60,
    )

    assert len(dashboard["ledger"]["rows"]) == 2
    assert "score" not in dashboard["iterations"][0]["metrics"]
    assert "score" not in dashboard["iterations"][1]["metrics"]


def test_observe_dashboard_state_withholds_single_unkeyed_ledger_row(tmp_path):
    repo_root = tmp_path
    iteration_dir = repo_root / "experiments" / "iterations" / "run-single-ledger" / "iteration-0001"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-single-ledger",
            "status": "running",
            "current_iteration": 1,
            "active_iteration": None,
            "updated_at": "2026-04-19T11:59:30+00:00",
        },
    )
    _write_json(
        iteration_dir / "iteration_record.json",
        {
            "run_id": "run-single-ledger",
            "iteration_number": 1,
            "artifact_status": "completed",
            "decision": "keep",
        },
    )
    _write_results_tsv(repo_root / "experiments" / "results.tsv")

    dashboard = observe_dashboard_state(
        repo_root,
        now=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
        stale_after_seconds=60,
    )

    assert len(dashboard["ledger"]["rows"]) == 1
    assert "score" not in dashboard["iterations"][0]["metrics"]


def test_observe_dashboard_state_hides_stale_iterations_without_run_state(tmp_path):
    stale_iteration_dir = tmp_path / "experiments" / "iterations" / "old-run" / "iteration-0001"
    _write_json(
        stale_iteration_dir / "iteration_record.json",
        {
            "run_id": "old-run",
            "iteration_number": 1,
            "artifact_status": "completed",
            "decision": "keep",
        },
    )

    dashboard = observe_dashboard_state(
        tmp_path,
        now=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
        stale_after_seconds=60,
    )

    assert dashboard["run"]["status"] == "Waiting"
    assert dashboard["iterations"] == []
    assert dashboard["sources"]["active_run_root"] is None


def test_observe_dashboard_state_uses_fresh_artifact_heartbeat_over_stale_log(tmp_path):
    now = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
    repo_root = tmp_path
    iteration_dir = repo_root / "experiments" / "iterations" / "run-fresh-artifact" / "iteration-0001"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-fresh-artifact",
            "status": "running",
            "current_iteration": 1,
            "active_iteration": 1,
            "updated_at": "2026-04-19T10:00:00+00:00",
        },
    )
    _write_json(
        iteration_dir / "iteration_record.json",
        {
            "run_id": "run-fresh-artifact",
            "iteration_number": 1,
            "artifact_status": "running",
            "artifact_paths": {
                "context_json": str(iteration_dir / "context.json"),
            },
        },
    )
    _write_json(iteration_dir / "context.json", {"iteration": 1})
    _touch_at(iteration_dir / "context.json", now.timestamp() - 2)
    (iteration_dir / "claude.stdout.log").write_text("stale log\n", encoding="utf-8")
    _touch_at(iteration_dir / "claude.stdout.log", now.timestamp() - 7200)

    dashboard = observe_dashboard_state(repo_root, now=now, stale_after_seconds=60)

    assert dashboard["run"]["status"] == "Busy"
    assert dashboard["run"]["heartbeat"]["source_role"] == "artifact"
    assert dashboard["run"]["heartbeat"]["path"] == str(iteration_dir / "context.json")
    assert dashboard["run"]["heartbeat"]["age_seconds"] == pytest.approx(2)
