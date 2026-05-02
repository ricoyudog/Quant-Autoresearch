from __future__ import annotations

import json
from pathlib import Path


SPEC_DIR = Path(__file__).resolve().parents[2] / "specs" / "004-martinluk-primitive"
MAP_PATH = SPEC_DIR / "phase5-7-missing-primary-evidence-map.json"


def load_map() -> dict:
    return json.loads(MAP_PATH.read_text())


def categories(row: dict) -> set[str]:
    return {item["category"] for item in row["missing_primary_evidence"]}


def test_phase5_7_missing_evidence_map_preserves_no_overclaim_and_t020_block() -> None:
    evidence_map = load_map()

    assert (
        evidence_map["overall_decision"]
        == "record_missing_primary_evidence_without_upgrading_replay_or_launching_t020"
    )
    assert evidence_map["t020_state"].startswith("- [ ] T020 Launch bounded autoresearch")
    boundary = evidence_map["no_overclaim_boundary"].lower()
    assert "identifies missing primary public evidence only" in boundary
    assert "does not add sources" in boundary
    assert "update exact dates/fills" in boundary
    assert "patch trace labels" in boundary
    assert "prove profit" in boundary
    assert "replicate private-account outcomes" in boundary
    assert "authorize t020/broad autoresearch" in boundary

    status = evidence_map["current_replay_status"]
    assert status["overall_run_status"] == "research_only"
    assert status["promoted"] is False
    assert status["reproduced_public_replay_candidate_count"] == 0
    assert status["public_status_counts"] == {"insufficient_evidence": 5}


def test_phase5_7_missing_evidence_map_covers_public_candidates() -> None:
    evidence_map = load_map()
    rows = evidence_map["public_candidate_missing_evidence"]

    assert evidence_map["summary"]["public_replay_candidate_rows"] == 5
    assert {row["row_id"] for row in rows} == {
        "p5-public-sofi",
        "p5-public-amc",
        "p5-public-coin",
        "p5-public-lmnd",
        "p5-public-smci",
    }

    for row in rows:
        assert row["current_status"] == "insufficient_evidence"
        assert row["current_gap_classification"] == "evidence_not_sufficient"
        assert row["source_refs_exist"]
        assert row["missing_primary_evidence"]
        assert row["evidence_status"] == "insufficient_evidence_until_each_missing_primary_field_is_cited"
        for requirement in row["missing_primary_evidence"]:
            assert "primary" in requirement["category"]
            assert "market-bar inference alone is not sufficient" in requirement["required_primary_evidence"]


def test_phase5_7_missing_evidence_map_covers_all_phase5_6_gap_rows() -> None:
    evidence_map = load_map()
    rows = evidence_map["phase5_6_gap_row_missing_evidence"]
    by_id = {row["row_id"]: row for row in rows}

    assert evidence_map["summary"]["phase5_6_gap_rows"] == 20
    assert evidence_map["summary"]["gap_rows_by_classification"] == {
        "primitive_not_emitted": 17,
        "trace_label_missing": 3,
    }
    assert len(by_id) == 20

    for row in rows:
        assert row["patch_decision"] == "do_not_patch_preserve_gap_classification"
        assert row["evidence_status"] == (
            "control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist"
        )
        assert "control_identity_primary_evidence_missing" in categories(row)
        assert "setup_entry_label_primary_evidence_missing" in categories(row)

    trace_label_rows = {
        "p5-control-amc-adjacent-1",
        "p5-control-amc-null-1",
        "p5-control-amc-null-2",
    }
    assert {
        row_id for row_id, row in by_id.items() if row["gap_classification"] == "trace_label_missing"
    } == trace_label_rows
    for row_id in trace_label_rows:
        assert "diagnostic_control_relabel_primary_evidence_missing" in categories(by_id[row_id])

    primitive_rows = [row for row in rows if row["gap_classification"] == "primitive_not_emitted"]
    assert len(primitive_rows) == 17
    assert all("primitive_trace_support_missing" in categories(row) for row in primitive_rows)


def test_phase5_7_missing_evidence_map_source_artifact_chain_is_explicit() -> None:
    evidence_map = load_map()
    sources = evidence_map["source_artifacts"]

    assert set(sources) >= {
        "specs/004-martinluk-primitive/phase5-7-public-evidence-upgrade-plan.json",
        "specs/004-martinluk-primitive/phase5-6-evidence-gap-classification-packet.json",
        "specs/004-martinluk-primitive/phase5-6-row-contract-gap-comparison.json",
        "specs/004-martinluk-primitive/phase5-2-bounded-replay-report.json",
        "specs/004-martinluk-primitive/public-operation-cases.json",
        "specs/004-martinluk-primitive/public-date-reconstruction.md",
        "specs/004-martinluk-primitive/source-ledger.json",
    }
    assert all(len(digest) == 64 for digest in sources.values())
