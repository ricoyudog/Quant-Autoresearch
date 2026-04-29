from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "004-martinluk-primitive"
    / "run_phase5_bounded_validation.py"
)
MANIFEST_PATH = MODULE_PATH.with_name("phase5-replay-manifest.json")


def load_phase5_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "martinluk_phase5_bounded_validation",
        MODULE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def phase5() -> Any:
    return load_phase5_module()


@pytest.fixture()
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text())


def validate_manifest(phase5: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    return phase5.validate_manifest(copy.deepcopy(manifest))


def report_for(phase5: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    return phase5.build_dry_run_report(copy.deepcopy(manifest), MANIFEST_PATH)


def public_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in manifest["executable_rows"]
        if row["row_kind"] == "public_replay_candidate"
    ]


def control_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in manifest["executable_rows"]
        if row["row_kind"] in {"adjacent_control_window", "null_control_window"}
    ]


def set_reproduced(row: dict[str, Any]) -> None:
    row["expected_status"] = "reproduced"
    row["missing_fields"] = []


def assert_has_error(result: dict[str, Any], *fragments: str) -> None:
    errors = "\n".join(result["errors"])
    for fragment in fragments:
        assert fragment in errors


def test_phase5_manifest_accepts_exact_bounded_25_row_fixture(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    result = validate_manifest(phase5, manifest)
    report = report_for(phase5, manifest)

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["executable_row_count"] == 25
    assert result["public_replay_candidate_count"] == 5
    assert result["adjacent_control_count"] == 10
    assert result["null_control_count"] == 10
    assert report["public_case_status_counts"] == {"insufficient_evidence": 5}
    assert report["bounded_historical_controls_summary"]["control_count"] == 20
    assert "promotion" in report["bounded_historical_controls_summary"]["promotion_count_note"]


def test_phase5_manifest_rejects_six_public_candidates_before_data_access(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    extra = copy.deepcopy(public_rows(manifest)[0])
    extra["row_id"] = "p5-public-extra-sixth"
    extra["case_id"] = "MLUK-EXTRA-UNAPPROVED-006"
    manifest["executable_rows"].append(extra)

    result = validate_manifest(phase5, manifest)
    report = report_for(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, "maximum 5 replayable public candidate cases")
    assert report["market_data_queries"] == []


@pytest.mark.parametrize(
    ("row_kind", "expected_fragment"),
    [
        ("adjacent_control_window", "adjacent_control_window cap"),
        ("null_control_window", "null_control_window cap"),
    ],
)
def test_phase5_manifest_rejects_more_than_two_controls_per_parent(
    phase5: Any,
    manifest: dict[str, Any],
    row_kind: str,
    expected_fragment: str,
) -> None:
    parent = public_rows(manifest)[0]["case_id"]
    source = next(
        row
        for row in manifest["executable_rows"]
        if row["row_kind"] == row_kind and row["parent_case_id"] == parent
    )
    extra = copy.deepcopy(source)
    extra["row_id"] = f"{source['row_id']}-third"
    extra["case_id"] = f"{source['case_id']}-THIRD"
    extra["control_index"] = 3
    manifest["executable_rows"].append(extra)

    result = validate_manifest(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, parent, expected_fragment)


def test_phase5_manifest_rejects_more_than_25_executable_rows(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    extra = copy.deepcopy(control_rows(manifest)[0])
    extra["row_id"] = "p5-control-over-25"
    extra["case_id"] = "MLUK-SOFI-PULLBACK-PDH-001-OVER-25"
    extra["control_index"] = 3
    manifest["executable_rows"].append(extra)

    result = validate_manifest(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, "maximum 25 executable manifest rows")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row, control_case_id: row.update({"parent_case_id": None}),
        lambda row, control_case_id: row.update({"parent_case_id": "MLUK-UNKNOWN"}),
        lambda row, control_case_id: row.update({"parent_case_id": control_case_id}),
        lambda row, control_case_id: row.pop("control_index"),
        lambda row, control_case_id: row.update({"control_index": "1"}),
        lambda row, control_case_id: row.update({"control_role": ""}),
    ],
)
def test_phase5_manifest_rejects_bad_control_parent_linkage(
    phase5: Any,
    manifest: dict[str, Any],
    mutation: Any,
) -> None:
    control = control_rows(manifest)[0]
    mutation(control, control["case_id"])

    result = validate_manifest(phase5, manifest)

    assert result["passed"] is False
    assert any(
        fragment in "\n".join(result["errors"])
        for fragment in [
            "parent_case_id",
            "public_replay_candidate",
            "control_index",
            "control_role",
        ]
    )


def test_phase5_manifest_rejects_research_or_unsupported_rows_inside_executable_manifest(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    first = manifest["executable_rows"][0]
    second = manifest["executable_rows"][1]
    first["evidence_class"] = "research_only_insufficient_evidence"
    second["row_kind"] = "unsupported_case"
    second["evidence_class"] = "unsupported_until_new_primary_evidence"

    result = validate_manifest(phase5, manifest)
    report = report_for(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, "executable evidence_class", "row_kind")
    assert report["market_data_queries"] == []


def test_phase5_audit_ledger_accepts_research_only_and_unsupported_as_insufficient_only(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    report = report_for(phase5, manifest)

    assert validate_manifest(phase5, manifest)["passed"] is True
    audit = {row["case_id"]: row for row in report["audit_results"]}
    assert set(audit) == {
        "MLUK-GLD-SLV-DECLINING9EMA-SHORT-006",
        "MLUK-SNDK-RETRY-COOLDOWN-007",
        "MLUK-NVDA-TSLA-QUANTUM-2025-PULLBACK-008",
    }
    assert {row["final_status"] for row in audit.values()} == {"insufficient_evidence"}
    assert {row["market_data_query_allowed"] for row in audit.values()} == {False}
    assert all("market_granularity" not in row for row in manifest["audit_rows"])


@pytest.mark.parametrize("bad_status", ["reproduced", "not_reproduced", "data_missing"])
def test_phase5_audit_ledger_rejects_positive_or_data_missing_statuses(
    phase5: Any,
    manifest: dict[str, Any],
    bad_status: str,
) -> None:
    manifest["audit_rows"][0]["expected_status"] = bad_status

    result = validate_manifest(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, "audit expected_status must be insufficient_evidence")


def test_phase5_data_gap_classifies_executable_row_as_data_missing_not_not_reproduced(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    row = manifest["executable_rows"][0]
    row["expected_status"] = "not_reproduced"
    row["data_availability"] = {
        "available": False,
        "symbol": row["symbol"],
        "window": row["allowed_window"],
        "missing_reason": "daily bars absent for candidate window",
    }

    report = report_for(phase5, manifest)
    first_result = report["row_results"][0]

    assert first_result["final_status"] == "data_missing"
    assert first_result["final_status"] != "not_reproduced"
    assert "daily bars absent" in first_result["reason"]
    assert row["symbol"] in first_result["reason"]


def test_phase5_minute_granularity_required_for_intraday_replay(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    daily_row = next(row for row in public_rows(manifest) if row["market_granularity"] == "daily")
    minute_row = next(row for row in public_rows(manifest) if row["market_granularity"] == "minute")
    daily_row["expected_status"] = "not_reproduced"
    daily_row["data_availability"] = {"available": True, "source": "daily_fixture"}
    minute_row["expected_status"] = "not_reproduced"
    minute_row["data_availability"] = {
        "available": False,
        "symbol": minute_row["symbol"],
        "window": minute_row["allowed_window"],
        "missing_reason": "minute bars absent for intraday replay",
    }

    report = report_for(phase5, manifest)
    by_case = {row["case_id"]: row for row in report["row_results"]}

    assert by_case[daily_row["case_id"]]["final_status"] == "not_reproduced"
    assert by_case[minute_row["case_id"]]["final_status"] == "data_missing"
    assert "minute bars absent" in by_case[minute_row["case_id"]]["reason"]


def test_phase5_controls_never_count_toward_public_reproduction_or_promotion(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    for row in public_rows(manifest)[:4]:
        set_reproduced(row)
    for row in control_rows(manifest):
        set_reproduced(row)

    report = report_for(phase5, manifest)

    assert report["validation"]["passed"] is True
    assert report["public_case_status_counts"]["reproduced"] == 4
    assert report["bounded_historical_controls_summary"]["status_counts"] == {
        "reproduced": 20
    }
    assert report["overall_run_status"] == "research_only"
    assert report["promoted"] is False


def test_phase5_five_public_reproduced_is_minimum_promotion_gate(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    for row in public_rows(manifest):
        set_reproduced(row)

    report = report_for(phase5, manifest)

    assert report["validation"]["passed"] is True
    assert report["reproduced_public_replay_candidate_count"] == 5
    assert report["overall_run_status"] == "promoted"
    assert report["promoted"] is True


def test_phase5_report_has_no_overclaim_statement_and_na_realized_fields(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    report = report_for(phase5, manifest)
    statement = report["no_overclaim_statement"].lower()

    assert "not profit proof" in statement
    assert "not exact fill" in statement
    assert "not martin luk realized" in statement
    assert "not private account replication" in statement
    for row in [*report["row_results"], *report["audit_results"]]:
        assert row["realized_outcome"] == {
            "realized_entry_price": "N/A",
            "realized_exit_price": "N/A",
            "realized_position_size": "N/A",
            "realized_account_pnl": "N/A",
            "fees": "N/A",
            "slippage": "N/A",
        }


def test_phase5_metric_labels_are_hypothetical_strategy_bar_diagnostics(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    allowed = set(manifest["metric_labels"])
    assert "signal_emitted" in allowed
    assert "direction_match" in allowed
    assert "setup_tag_match" in allowed
    assert "stop_width_pct_hypothetical_strategy_bar_diagnostic" in allowed
    assert "r_multiple_hypothetical_strategy_bar_diagnostic" in allowed
    assert "false_positive_count_in_control_windows" in allowed

    manifest["metric_labels"].extend(
        [
            "profit" + "_proof",
            "replicated" + "_pnl",
            "martin_luk" + "_exact_replication",
            "annualized" + "_return",
            "optimized" + "_threshold",
        ]
    )
    result = validate_manifest(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, "disallowed overclaim labels")


def test_phase5_report_records_source_metadata_and_manifest_identity(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    report = report_for(phase5, manifest)
    source_metadata = report["source_metadata"]

    assert report["run_id"] == "martinluk_phase5_dry_run_v1"
    assert report["manifest_path"].endswith("phase5-replay-manifest.json")
    assert len(report["manifest_sha256"]) == 64
    assert source_metadata["daily_cache_path"] == "data/daily_cache.duckdb"
    assert source_metadata["minute_dataset_root_env"] == "MINUTE_AGGS_DATASET_ROOT"
    assert len(source_metadata["query_date_ranges"]) == 5
    assert source_metadata["missing_symbol_or_window_reasons"] == []


def test_phase5_rejects_broad_backtest_requests_before_loader_calls(
    phase5: Any,
    manifest: dict[str, Any],
) -> None:
    manifest.update(
        {
            "universe": "all",
            "full_history": True,
            "parameter_sweep": {"stop_width": [1, 2, 3]},
            "optimizer_loop": True,
            "walk_forward": True,
            "broad_scoreboard": True,
        }
    )

    result = validate_manifest(phase5, manifest)
    report = report_for(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, "forbidden broad-validation request keys")
    assert report["market_data_queries"] == []


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "optimizer_loop",
        "allow_optimizer_loops",
        "threshold_search",
        "search_loop",
        "allow_search_loops",
    ],
)
def test_phase5_rejects_optimizer_and_search_loop_aliases_before_loader_calls(
    phase5: Any,
    manifest: dict[str, Any],
    forbidden_key: str,
) -> None:
    manifest[forbidden_key] = True

    result = validate_manifest(phase5, manifest)
    report = report_for(phase5, manifest)

    assert result["passed"] is False
    assert_has_error(result, forbidden_key)
    assert report["market_data_queries"] == []
