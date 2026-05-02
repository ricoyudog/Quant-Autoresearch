import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "specs/004-martinluk-primitive/phase5-6-evidence-gap-classification-packet.json"

EXPECTED_TAXONOMY = {
    "exact date": "exact_date_missing",
    "entry fill": "fill_missing",
    "partial fill": "fill_missing",
    "final exit fill": "exit_missing",
    "account equity": "account_context_missing",
    "exact first attempt timestamp": "exact_date_missing",
    "re-entry timestamp": "exact_date_missing",
    "stop adjustment timestamps": "exit_missing",
    "all exits": "exit_missing",
    "exact BTC context timestamp": "exact_date_missing",
    "entry/exit fills": "fill_missing",
    "position size": "account_context_missing",
    "exact split-adjusted prices": "fill_missing",
    "partial size": "fill_missing",
    "volume climax timestamp": "exact_date_missing",
    "actual premature exit": "exit_missing",
    "would-have-held benchmark": "exit_missing",
}

EXPECTED_SOURCE_LEDGER_TAXONOMY = {
    "exact dates/fills": "exact_date_missing",
    "complete fills": "fill_missing",
    "portfolio sizing": "account_context_missing",
    "exact full execution ledger": "fill_missing",
}

ALLOWED_CATEGORIES = {
    "exact_date_missing",
    "setup_entry_label_missing",
    "fill_missing",
    "exit_missing",
    "account_context_missing",
}


def test_phase5_6_packet_classifies_every_parent_missing_field() -> None:
    packet = json.loads(PACKET.read_text())

    taxonomy = packet["missing_field_taxonomy"]
    assert set(taxonomy["allowed_categories"]) == ALLOWED_CATEGORIES
    assert taxonomy["field_to_category"] == EXPECTED_TAXONOMY

    for row in packet["rows"]:
        evidence = row["parent_public_case_evidence"]
        missing_fields = evidence["missing_fields"]
        classifications = evidence["missing_field_classifications"]

        assert [item["field"] for item in classifications] == missing_fields
        for item in classifications:
            assert item["category"] == EXPECTED_TAXONOMY[item["field"]]
            assert item["category"] in ALLOWED_CATEGORIES
            assert item["evidence_status"] == "public_evidence_missing"

        source_evidence = row["source_ledger_evidence"]
        source_missing_fields = source_evidence["missing_fields"]
        source_classifications = source_evidence["missing_field_classifications"]
        assert [item["field"] for item in source_classifications] == source_missing_fields
        for item in source_classifications:
            assert item["category"] == EXPECTED_SOURCE_LEDGER_TAXONOMY[item["field"]]
            assert item["category"] in ALLOWED_CATEGORIES
            assert item["evidence_status"] == "public_evidence_missing"

        row_gap = row["row_gap_missing_field_classification"]
        assert row_gap["field"] == "required setup_type/entry_trigger trace match"
        assert row_gap["category"] == "setup_entry_label_missing"
        assert row_gap["evidence_status"] == "not_satisfied_by_current_trace_or_series"


def test_phase5_6_missing_field_taxonomy_preserves_no_overclaim_boundary() -> None:
    packet = json.loads(PACKET.read_text())

    assert packet["overall_decision"] == "do_not_patch_trace_labels_and_do_not_launch_t020"
    assert packet["decision_summary"]["safe_trace_label_patches"] == []
    for row in packet["rows"]:
        assert row["patch_decision"] == "do_not_patch_preserve_gap_classification"
        assert "parent_public_case_still_missing_exact_fill_or_intraday_management_fields" in row["decision_reasons"]
