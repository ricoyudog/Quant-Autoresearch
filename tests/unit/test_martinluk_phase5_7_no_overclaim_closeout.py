from __future__ import annotations

import json
from pathlib import Path


SPEC_DIR = Path(__file__).resolve().parents[2] / "specs" / "004-martinluk-primitive"
CLOSEOUT_PATH = SPEC_DIR / "phase5-7-no-overclaim-closeout.json"


def load_closeout() -> dict:
    return json.loads(CLOSEOUT_PATH.read_text())


def test_phase5_7_closeout_preserves_insufficient_evidence_and_t020_block() -> None:
    closeout = load_closeout()

    assert closeout["overall_decision"] == "preserve_insufficient_evidence_no_overclaim_and_keep_t020_blocked"
    assert closeout["t020_state"].startswith("- [ ] T020 Launch bounded autoresearch")

    status = closeout["replay_status_checks"]
    assert status["overall_run_status"] == "research_only"
    assert status["promoted"] is False
    assert status["public_status_counts"] == {"insufficient_evidence": 5}
    assert status["public_gap_classification_counts"] == {"evidence_not_sufficient": 5}
    assert status["reproduced_public_replay_candidate_count"] == 0
    assert status["controls_counted_toward_promotion"] == 0
    assert status["false_positive_control_row_ids"] == []
    assert status["diagnostic_promotion_veto_active"] is False


def test_phase5_7_closeout_keeps_artifacts_as_mapping_and_proposal_only() -> None:
    closeout = load_closeout()
    checks = closeout["artifact_checks"]

    plan = checks["public_evidence_upgrade_plan"]
    assert plan["broad_autoresearch_allowed"] is False
    assert plan["new_primary_public_evidence_added"] is False

    missing_map = checks["missing_primary_evidence_map"]
    assert missing_map["public_replay_candidate_rows"] == 5
    assert missing_map["phase5_6_gap_rows"] == 20

    proposals = checks["source_date_reconstruction_proposals"]
    assert proposals["direct_source_ledger_updates"] == []
    assert proposals["direct_public_date_reconstruction_updates"] == []
    assert proposals["overall_decision"] == "proposal_only_no_source_ledger_or_public_date_reconstruction_update"

    boundary = closeout["no_overclaim_boundary"].lower()
    assert "evidence-mapping and proposal artifacts only" in boundary
    assert "do not add public sources" in boundary
    assert "update exact dates/fills" in boundary
    assert "patch trace labels" in boundary
    assert "prove profit" in boundary
    assert "private-account outcomes" in boundary
    assert "authorize broad autoresearch/t020" in boundary


def test_phase5_7_closeout_records_worker_ownership_boundaries() -> None:
    closeout = load_closeout()
    ownership = closeout["ownership_coordination"]

    assert "public replay candidate evidence mapping" in ownership["worker_1_scope"]
    assert "source-ledger/public-date-reconstruction proposals" in ownership["worker_1_scope"]
    assert "worker-1 did not edit worker-2-owned Phase 5.6 taxonomy artifacts" in ownership[
        "worker_2_scope_acknowledged"
    ]
    assert "record the gap rather than invent dates" in ownership["shared_boundary"]
    assert "phase5-7-no-overclaim-closeout.*" in ownership["worker_1_owned_outputs"]


def test_phase5_7_closeout_source_artifacts_are_explicit() -> None:
    closeout = load_closeout()
    sources = closeout["source_artifacts"]

    assert set(sources) == {
        "specs/004-martinluk-primitive/phase5-7-public-evidence-upgrade-plan.json",
        "specs/004-martinluk-primitive/phase5-7-missing-primary-evidence-map.json",
        "specs/004-martinluk-primitive/phase5-7-source-date-reconstruction-proposals.json",
        "specs/004-martinluk-primitive/phase5-2-bounded-replay-report.json",
        "specs/004-martinluk-primitive/phase5-6-evidence-gap-classification-packet.json",
        "specs/004-martinluk-primitive/phase5-6-row-contract-gap-comparison.json",
        "specs/004-martinluk-primitive/tasks.md",
    }
    assert all(len(digest) == 64 for digest in sources.values())
