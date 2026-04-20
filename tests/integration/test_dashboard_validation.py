from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

from src.dashboard.server import make_dashboard_handler


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _touch_at(path: Path, timestamp: float, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
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
        + "\n".join(
            [
                "\t".join(
                    [
                        "iter-1",
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
                        "iter-2",
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


def _create_representative_dashboard_repo(
    repo_root: Path,
    *,
    now: datetime | None = None,
) -> None:
    now = now or datetime.now(timezone.utc)
    run_root = repo_root / "experiments" / "iterations" / "run-verify"
    first_dir = run_root / "iteration-0001"
    second_dir = run_root / "iteration-0002"

    _write_json(
        repo_root / "experiments" / "autoresearch_state.json",
        {
            "run_id": "run-verify",
            "status": "running",
            "current_iteration": 2,
            "active_iteration": None,
            "last_completed_iteration": 2,
            "best_score": 0.81,
            "best_iteration": 2,
            "updated_at": now.isoformat(),
        },
    )
    _write_json(
        first_dir / "iteration_record.json",
        {
            "run_id": "run-verify",
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
                "decision": str(first_dir / "decision.json"),
                "context_json": str(first_dir / "context.json"),
            },
        },
    )
    _write_json(
        first_dir / "decision.json",
        {
            "decision": "keep",
            "reasons": ["score_above_baseline_and_previous_best"],
            "score": 0.72,
            "baseline_sharpe": 0.5,
            "deflated_sr": 0.61,
        },
    )
    _write_json(first_dir / "context.json", {"iteration": 1})

    _write_json(
        second_dir / "iteration_record.json",
        {
            "run_id": "run-verify",
            "iteration_number": 2,
            "artifact_status": "completed",
            "execution_mode": "live",
            "summary": {
                "hypothesis": "Tighten the no-trade band during low-volatility windows",
                "strategy_change_summary": "Reduced turnover by gating entries on realized volatility",
                "files_touched": ["src/strategies/active_strategy.py", "config/strategy.json"],
            },
            "decision": "keep",
            "decision_reason": ["score_above_previous_iteration", "turnover_reduced"],
            "artifact_paths": {
                "decision": str(second_dir / "decision.json"),
                "context_json": str(second_dir / "context.json"),
                "experiment_note_draft": str(second_dir / "experiment_note_draft.md"),
            },
        },
    )
    _write_json(
        second_dir / "decision.json",
        {
            "decision": "keep",
            "reasons": ["score_above_previous_iteration", "turnover_reduced"],
            "score": 0.81,
            "baseline_sharpe": 0.5,
            "deflated_sr": 0.69,
        },
    )
    _write_json(second_dir / "context.json", {"iteration": 2})
    (second_dir / "experiment_note_draft.md").write_text("# Draft\n", encoding="utf-8")
    _touch_at(first_dir / "claude.stdout.log", now.timestamp() - 60, "round 1 complete\n")
    _touch_at(second_dir / "claude.stdout.log", now.timestamp() - 3, "round 2 complete\n")
    _write_results_tsv(repo_root / "experiments" / "results.tsv")


def test_dashboard_validates_representative_artifact_tree_within_ten_seconds(tmp_path):
    repo_root = tmp_path
    fixture_now = datetime.now(timezone.utc)
    _create_representative_dashboard_repo(repo_root, now=fixture_now)

    handler = make_dashboard_handler(repo_root, refresh_seconds=0.5)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address

        start = time.monotonic()
        with urlopen(f"http://{host}:{port}/", timeout=10) as response:
            home_html = response.read().decode("utf-8")
        home_elapsed = time.monotonic() - start

        start = time.monotonic()
        with urlopen(f"http://{host}:{port}/iterations/2", timeout=10) as response:
            detail_html = response.read().decode("utf-8")
        detail_elapsed = time.monotonic() - start

        with urlopen(f"http://{host}:{port}/api/state", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert home_elapsed < 10, f"home page exceeded 10s: {home_elapsed:.2f}s"
        assert detail_elapsed < 10, f"detail page exceeded 10s: {detail_elapsed:.2f}s"
        assert "Research Monitor" in home_html
        assert "Run Health Strip" in home_html
        assert "Iteration Detail" in detail_html

        assert payload["run"]["run_id"] == "run-verify"
        assert payload["run"]["status"] == "Healthy"
        assert payload["run"]["diagnosis"] is None
        assert payload["run"]["heartbeat"]["source_role"] in {"artifact", "log"}
        assert payload["run"]["heartbeat"]["age_seconds"] < 10
        assert payload["iterations"][-1]["decision"] == "keep"
        assert payload["iterations"][-1]["status"] == "Kept"
        assert payload["iterations"][-1]["analysis"]["hypothesis_diff"].startswith(
            "Previous: Reduce turnover with a no-trade band"
        )
        assert payload["iterations"][-1]["decision_reasons"] == [
            "score_above_previous_iteration",
            "turnover_reduced",
        ]
        assert payload["iterations"][-1]["metric_breakdown"]["comparisons"][1]["label"] == "vs current baseline"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
