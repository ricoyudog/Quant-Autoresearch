from __future__ import annotations

import json
from pathlib import Path


SPEC_DIR = Path(__file__).resolve().parents[2] / "specs" / "004-martinluk-primitive"
LAUNCH_PATH = SPEC_DIR / "phase5-t020-bounded-autoresearch-launch.json"
LAUNCH_MD_PATH = SPEC_DIR / "phase5-t020-bounded-autoresearch-launch.md"


def load_launch() -> dict:
    return json.loads(LAUNCH_PATH.read_text())


def test_phase5_t020_launch_records_bounded_evaluation_and_no_overclaim() -> None:
    launch = load_launch()
    md = LAUNCH_MD_PATH.read_text()

    assert launch["overall_decision"] == "bounded_autoresearch_launched_with_no_overclaim_boundary"
    assert launch["launch_status"] == "completed"
    assert launch["launch_attempted"] is True
    assert launch["launch_authorized"] is True
    assert launch["t020_state"] in md
    assert launch["t020_state"].startswith("- [X] T020 Launch bounded autoresearch")

    boundary = launch["no_overclaim_boundary"].lower()
    assert "bounded autoresearch/backtest evaluation only" in boundary
    assert "does not prove profit" in boundary
    assert "private-account outcomes" in boundary
    assert "exact-fill replication" in boundary
    assert "insufficient_evidence" in launch["no_overclaim_boundary"]


def test_phase5_t020_launch_reflects_bounded_eval_and_replay_boundaries() -> None:
    launch = load_launch()
    summary = launch["bounded_evaluation_summary"]
    checks = launch["gate_checks"]

    assert summary["overall_run_status"] == "bounded_evaluation_complete"
    assert summary["promoted"] is False
    assert summary["public_replay_candidates"] == 5
    assert summary["reproduced_public_replay_candidate_count"] == 0
    assert summary["public_status_counts"] == {"insufficient_evidence": 5}
    assert summary["public_gap_classification_counts"] == {"evidence_not_sufficient": 5}
    assert summary["controls_counted_toward_promotion"] == 0
    assert summary["market_data_queries"] == "bounded_backtest_query_only"
    metrics = summary["bounded_backtest_metrics"]
    assert metrics["score_sharpe"] == 1.061
    assert metrics["deflated_sr"] == 0.677
    assert metrics["trades"] == 8

    assert checks["public_operation_replay_gates"]["status"] == "research_only_insufficient_evidence"
    assert "0/5 reproduced" in checks["public_operation_replay_gates"]["evidence"]
    assert checks["validator"]["status"] == "pass"
    assert checks["bounded_backtest_evaluation"]["status"] == "pass"
