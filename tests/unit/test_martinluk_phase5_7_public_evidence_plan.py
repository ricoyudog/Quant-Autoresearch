from __future__ import annotations

import json
from pathlib import Path


SPEC_DIR = Path(__file__).resolve().parents[2] / "specs" / "004-martinluk-primitive"
PLAN_PATH = SPEC_DIR / "phase5-7-public-evidence-upgrade-plan.json"
TASKS_PATH = SPEC_DIR / "tasks.md"


def load_plan() -> dict:
    return json.loads(PLAN_PATH.read_text())


def normalize(text: str) -> str:
    return text.lower().replace("-", " ")


def test_phase5_7_plan_keeps_t020_blocked_and_disallows_broad_autoresearch() -> None:
    plan = load_plan()
    tasks_text = TASKS_PATH.read_text()

    assert plan["overall_decision"] == "keep_t020_blocked_and_collect_primary_public_evidence_only"
    assert plan["t020_state"] in tasks_text
    assert plan["t020_state"].startswith("- [ ] T020 Launch bounded autoresearch")
    assert plan["broad_autoresearch_allowed"] is False
    assert plan["new_primary_public_evidence_added"] is False
    assert (
        plan["source_ledger_update_policy"]
        == "proposal_only_until_cited_primary_public_evidence_supports_the_specific_missing_field"
    )

    boundary = normalize(plan["no_overclaim_boundary"])
    assert "planning artifact only" in boundary
    assert "preserves insufficient_evidence" in plan["no_overclaim_boundary"]
    assert "research_only" in plan["no_overclaim_boundary"]
    assert "promoted=false" in plan["no_overclaim_boundary"]
    assert "n/a realized outcomes" in boundary
    assert "not profit proof" in boundary
    assert "not martin luk realized" in boundary
    assert "not private account replication" in boundary
    assert "not exact fill replication" in boundary
    assert "not evidence to launch t020" in boundary


def test_phase5_7_plan_preserves_current_research_only_replay_status() -> None:
    plan = load_plan()
    status = plan["current_replay_status"]

    assert status["overall_run_status"] == "research_only"
    assert status["promoted"] is False
    assert status["reproduced_public_replay_candidate_count"] == 0
    assert status["public_replay_candidate_count"] == 5
    assert status["public_status_counts"] == {"insufficient_evidence": 5}
    assert status["public_gap_classification_counts"] == {"evidence_not_sufficient": 5}
    assert status["false_positive_control_row_ids"] == []
    assert status["controls_counted_toward_promotion"] == 0
    assert status["diagnostic_promotion_veto_active"] is False


def test_phase5_7_plan_maps_public_candidates_to_missing_primary_evidence() -> None:
    plan = load_plan()
    rows = plan["public_candidate_upgrade_matrix"]

    assert {row["row_id"] for row in rows} == {
        "p5-public-sofi",
        "p5-public-amc",
        "p5-public-coin",
        "p5-public-lmnd",
        "p5-public-smci",
    }

    for row in rows:
        assert row["current_phase5_2_final_status"] == "insufficient_evidence"
        assert row["current_phase5_2_gap_classification"] == "evidence_not_sufficient"
        assert row["window_status"] == "reconstructed_candidate_not_exact_fill"
        assert row["upgrade_status"] == "blocked_pending_cited_primary_public_evidence"
        assert row["source_refs_exist"]
        assert row["missing_source_refs"] == []
        assert row["missing_primary_public_fields"]
        assert len(row["required_primary_evidence"]) == len(
            row["missing_primary_public_fields"]
        )
        for requirement in row["required_primary_evidence"]:
            assert requirement["missing_field"] in row["missing_primary_public_fields"]
            assert "public primary evidence" in requirement["required_upgrade_evidence"]
            assert (
                requirement["ledger_action"]
                == "do_not_update_source_ledger_or_public_date_reconstruction_until_cited_evidence_exists"
            )


def test_phase5_7_plan_retains_phase5_6_do_not_patch_inputs() -> None:
    plan = load_plan()
    inputs = plan["phase5_6_inputs"]

    assert inputs["overall_decision"] == "do_not_patch_trace_labels_and_do_not_launch_t020"
    assert inputs["safe_trace_label_patches"] == []
    assert inputs["eligible_trace_label_patch_rows"] == []
    assert inputs["patch_active_strategy_trace_labels"] is False
    assert inputs["reviewed_gap_rows"] == 20
    assert inputs["gap_classification_summary"] == {
        "evidence_not_sufficient": 8,
        "primitive_not_emitted": 17,
        "trace_label_missing": 3,
    }
