from __future__ import annotations

import json
from pathlib import Path


SPEC_DIR = Path(__file__).resolve().parents[2] / "specs" / "004-martinluk-primitive"
PROPOSAL_PATH = SPEC_DIR / "phase5-7-source-date-reconstruction-proposals.json"


def load_proposal() -> dict:
    return json.loads(PROPOSAL_PATH.read_text())


def test_phase5_7_source_date_proposals_make_no_direct_canonical_updates() -> None:
    proposal = load_proposal()

    assert proposal["overall_decision"] == "proposal_only_no_source_ledger_or_public_date_reconstruction_update"
    assert proposal["t020_state"].startswith("- [ ] T020 Launch bounded autoresearch")
    assert proposal["direct_source_ledger_updates"] == []
    assert proposal["direct_public_date_reconstruction_updates"] == []
    assert proposal["proposal_policy"]["current_result"] == "No direct canonical source/date updates are made in this task."

    boundary = proposal["no_overclaim_boundary"].lower()
    assert "no source-ledger or public-date-reconstruction field is upgraded" in boundary
    assert "candidate-window evidence only" in boundary
    assert "insufficient_evidence" in proposal["no_overclaim_boundary"]


def test_phase5_7_source_date_proposals_are_cited_per_public_candidate() -> None:
    proposal = load_proposal()
    rows = proposal["candidate_proposals"]

    assert {row["row_id"] for row in rows} == {
        "p5-public-sofi",
        "p5-public-amc",
        "p5-public-coin",
        "p5-public-lmnd",
        "p5-public-smci",
    }

    for row in rows:
        assert row["current_source_ids"]
        assert row["cited_public_evidence_currently_available"]
        assert row["existing_source_ledger_entries"]
        assert row["missing_primary_evidence_fields"]
        assert (
            row["source_ledger_action"]
            == "no_direct_update_existing_sources_do_not_close_missing_primary_fields"
        )
        assert (
            row["public_date_reconstruction_action"]
            == "no_direct_update_keep_reconstructed_candidate_not_exact_fill"
        )
        assert "Existing cited public evidence supports candidate-window reconstruction only" in row["blocked_reason"]

    coin = next(row for row in rows if row["row_id"] == "p5-public-coin")
    assert set(coin["current_source_ids"]) == {
        "lilys_traderlion_2024_transcript",
        "financialwisdom_martin_luk_strategy",
    }


def test_phase5_7_source_date_proposals_keep_control_gap_rows_out_of_source_updates() -> None:
    proposal = load_proposal()

    assert proposal["control_gap_policy"] == (
        "The 20 Phase 5.6 gap rows are controls; do not add source-ledger/public-date-reconstruction "
        "entries for them unless future cited public evidence proves the row itself is a public operation."
    )
    assert "diagnostic controls" in proposal["proposal_policy"]["not_allowed"]
    assert "uncited assumptions" in proposal["proposal_policy"]["not_allowed"]


def test_phase5_7_source_date_proposals_record_source_artifact_hashes() -> None:
    proposal = load_proposal()
    sources = proposal["source_artifacts"]

    assert set(sources) == {
        "specs/004-martinluk-primitive/phase5-7-missing-primary-evidence-map.json",
        "specs/004-martinluk-primitive/phase5-7-public-evidence-upgrade-plan.json",
        "specs/004-martinluk-primitive/source-ledger.json",
        "specs/004-martinluk-primitive/public-date-reconstruction.md",
        "specs/004-martinluk-primitive/public-operation-cases.json",
    }
    assert all(len(digest) == 64 for digest in sources.values())
