#!/usr/bin/env python3
"""Validate and dry-run report MartinLuk Phase 5 bounded validation manifests.

This module intentionally does not query market data.  Phase 5 starts with a
manifest/report gate so public-case replay and limited controls stay bounded
before any later real-data execution is approved.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "martinluk_phase5_bounded_validation_v1"
DEFAULT_MANIFEST_PATH = Path(__file__).resolve().with_name(
    "phase5-replay-manifest.json"
)

EXECUTABLE_ROW_KINDS = {
    "public_replay_candidate",
    "adjacent_control_window",
    "null_control_window",
}
PUBLIC_ROW_KIND = "public_replay_candidate"
CONTROL_ROW_KINDS = {"adjacent_control_window", "null_control_window"}
AUDIT_ROW_KINDS = {"research_only_case", "unsupported_case"}
EXECUTABLE_EVIDENCE_CLASS = "replayable_window_candidate"
AUDIT_EVIDENCE_CLASSES = {
    "research_only_insufficient_evidence",
    "unsupported_until_new_primary_evidence",
}

ALLOWED_REPLAY_STATUSES = {
    "reproduced",
    "not_reproduced",
    "data_missing",
    "insufficient_evidence",
}
AUDIT_ONLY_STATUS = "insufficient_evidence"
RESEARCH_ONLY_RUN_STATUS = "research_only"
PROMOTED_RUN_STATUS = "promoted"
FAILED_RUN_STATUS = "failed"

ALLOWED_MARKET_GRANULARITIES = {"daily", "minute"}
ALLOWED_PUBLIC_CASE_IDS = {
    "MLUK-SOFI-PULLBACK-PDH-001",
    "MLUK-AMC-ORH-REENTRY-002",
    "MLUK-COIN-BTC-INSIDEDAY-003",
    "MLUK-LMND-HIGHTIGHTFLAG-004",
    "MLUK-SMCI-WEEKLYBASE-005",
}

REQUIRED_EXECUTABLE_ROW_FIELDS = {
    "row_id",
    "row_kind",
    "case_id",
    "parent_case_id",
    "control_index",
    "control_role",
    "symbol",
    "direction",
    "allowed_window",
    "market_granularity",
    "evidence_class",
    "expected_status",
    "missing_fields",
}
REQUIRED_AUDIT_ROW_FIELDS = {
    "row_id",
    "row_kind",
    "case_id",
    "symbol",
    "direction",
    "evidence_class",
    "expected_status",
    "market_data_query_allowed",
    "missing_fields",
}
REQUIRED_CAPS = {
    "max_public_replay_candidates": 5,
    "max_adjacent_controls_per_case": 2,
    "max_null_controls_per_case": 2,
    "max_executable_rows": 25,
    "allow_dynamic_universe": False,
    "allow_full_history": False,
    "allow_parameter_sweeps": False,
    "allow_optimizer_loops": False,
    "allow_walk_forward": False,
    "allow_broad_scoreboard": False,
}
REQUIRED_RUN_LEVEL_GATE = {
    "required_public_reproduced": 5,
    "counted_row_kind": PUBLIC_ROW_KIND,
    "controls_count_toward_promotion": False,
    "below_threshold_status": RESEARCH_ONLY_RUN_STATUS,
}
REQUIRED_DATA_SOURCE_FIELDS = {
    "daily",
    "daily_cache_path",
    "minute",
    "minute_dataset_root_env",
    "query_date_ranges",
    "missing_symbol_or_window_reasons",
}
REQUIRED_METRIC_WORDING_CONTRACT = {
    "diagnostic_values_are": "hypothetical_strategy_bar_diagnostics_only",
    "realized_outcome_fields": "N/A_without_new_primary_fill_evidence",
}
REALIZED_OUTCOME_FIELDS = (
    "realized_entry_price",
    "realized_exit_price",
    "realized_position_size",
    "realized_account_pnl",
    "fees",
    "slippage",
)
DISALLOWED_REPORT_LABELS = {
    "profit" + "_proof",
    "replicated" + "_pnl",
    "martin_luk" + "_exact_replication",
    "exact_fill" + "_replication",
    "private_usic" + "_account_replication",
    "annualized" + "_return",
    "optimized" + "_threshold",
}
NO_OVERCLAIM_STATEMENT = (
    "Phase 5 is a bounded public candidate-window dry-run report. It records "
    "evidence class, validation status, data availability, and hypothetical "
    "strategy-bar diagnostics only. It is not profit proof, not Martin Luk "
    "realized P&L, not private account replication, and not exact fill "
    "replication; "
    "realized entry, exit, size, fees, slippage, and account P&L remain N/A "
    "unless new primary fill evidence is separately approved."
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _is_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 10:
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _append_required_field_errors(
    errors: list[str],
    payload: dict[str, Any],
    required_fields: set[str],
    prefix: str,
) -> None:
    missing = sorted(required_fields - set(payload))
    if missing:
        errors.append(f"{prefix} missing fields: {', '.join(missing)}")


def _validate_caps(manifest: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    caps = manifest.get("caps")
    if not isinstance(caps, dict):
        errors.append("caps must be an object")
        return {}

    for key, expected in REQUIRED_CAPS.items():
        if key not in caps:
            errors.append(f"caps.{key} is required")
            continue
        actual = caps[key]
        if isinstance(expected, bool):
            if actual is not expected:
                errors.append(f"caps.{key} must be {expected}")
        elif not isinstance(actual, int) or isinstance(actual, bool) or actual > expected:
            errors.append(f"caps.{key} must be an integer <= {expected}")
    return caps


def _validate_window(row: dict[str, Any], errors: list[str], prefix: str) -> None:
    window = row.get("allowed_window")
    if not isinstance(window, dict):
        errors.append(f"{prefix} allowed_window must be an object")
        return
    if window.get("full_history") is True:
        errors.append(f"{prefix} allowed_window must not request full history")
    start = window.get("start")
    end = window.get("end")
    if not _is_iso_date(start) or not _is_iso_date(end):
        errors.append(f"{prefix} allowed_window.start/end must be ISO dates")
        return
    if _parse_date(str(start)) > _parse_date(str(end)):
        errors.append(f"{prefix} allowed_window.start must be <= end")
    if any("T" in str(window.get(key, "")) for key in ("start", "end")):
        errors.append(f"{prefix} allowed_window must use dates, not timestamps")


def _validate_run_level_gate(manifest: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    gate = manifest.get("run_level_gate")
    if not isinstance(gate, dict):
        errors.append("run_level_gate must be an object")
        return {}
    for key, expected in REQUIRED_RUN_LEVEL_GATE.items():
        if gate.get(key) != expected:
            errors.append(f"run_level_gate.{key} must be {expected!r}")
    return gate


def _validate_source_metadata(manifest: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    data_sources = manifest.get("data_sources")
    if not isinstance(data_sources, dict):
        errors.append("data_sources must be an object")
        return {}
    missing = sorted(REQUIRED_DATA_SOURCE_FIELDS - set(data_sources))
    if missing:
        errors.append(f"data_sources missing fields: {', '.join(missing)}")
    if not isinstance(data_sources.get("query_date_ranges"), list):
        errors.append("data_sources.query_date_ranges must be a list")
    if not isinstance(data_sources.get("missing_symbol_or_window_reasons"), list):
        errors.append("data_sources.missing_symbol_or_window_reasons must be a list")
    for key in sorted(REQUIRED_DATA_SOURCE_FIELDS - {"query_date_ranges", "missing_symbol_or_window_reasons"}):
        if key in data_sources and (not isinstance(data_sources[key], str) or not data_sources[key].strip()):
            errors.append(f"data_sources.{key} must be a non-empty string")
    return data_sources


def _validate_metric_wording_contract(manifest: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    contract = manifest.get("metric_wording_contract")
    if not isinstance(contract, dict):
        errors.append("metric_wording_contract must be an object")
        return {}
    for key, expected in REQUIRED_METRIC_WORDING_CONTRACT.items():
        if contract.get(key) != expected:
            errors.append(f"metric_wording_contract.{key} must be {expected!r}")
    not_claiming = contract.get("not_claiming")
    if not isinstance(not_claiming, list) or not not_claiming:
        errors.append("metric_wording_contract.not_claiming must be a non-empty list")
    return contract


def _validate_executable_rows(
    rows: list[Any],
    caps: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        errors.append("executable_rows must be a list")
        return []

    row_ids: set[str] = set()
    case_ids: set[str] = set()
    executable_rows: list[dict[str, Any]] = []
    public_rows_by_case_id: dict[str, dict[str, Any]] = {}

    for index, raw_row in enumerate(rows):
        prefix = f"executable_rows[{index}]"
        if not isinstance(raw_row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        row = raw_row
        executable_rows.append(row)
        _append_required_field_errors(
            errors,
            row,
            REQUIRED_EXECUTABLE_ROW_FIELDS,
            prefix,
        )

        row_id = row.get("row_id")
        if not isinstance(row_id, str) or not row_id.strip():
            errors.append(f"{prefix} row_id must be a non-empty string")
        elif row_id in row_ids:
            errors.append(f"duplicate row_id: {row_id}")
        else:
            row_ids.add(row_id)

        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{prefix} case_id must be a non-empty string")
        elif case_id in case_ids:
            errors.append(f"duplicate executable case_id: {case_id}")
        else:
            case_ids.add(case_id)

        row_kind = row.get("row_kind")
        if row_kind not in EXECUTABLE_ROW_KINDS:
            errors.append(f"{prefix} row_kind must be one of {sorted(EXECUTABLE_ROW_KINDS)}")

        if row.get("evidence_class") != EXECUTABLE_EVIDENCE_CLASS:
            errors.append(
                f"{prefix} executable evidence_class must be {EXECUTABLE_EVIDENCE_CLASS}"
            )

        if row.get("expected_status") not in ALLOWED_REPLAY_STATUSES:
            errors.append(
                f"{prefix} expected_status must be one of {sorted(ALLOWED_REPLAY_STATUSES)}"
            )
        if row.get("expected_status") in {"reproduced", "not_reproduced"} and row.get("missing_fields"):
            errors.append(
                f"{prefix} cannot expect {row.get('expected_status')} while missing_fields are present"
            )

        if row.get("market_granularity") not in ALLOWED_MARKET_GRANULARITIES:
            errors.append(
                f"{prefix} market_granularity must be one of "
                f"{sorted(ALLOWED_MARKET_GRANULARITIES)}"
            )

        if not isinstance(row.get("missing_fields"), list):
            errors.append(f"{prefix} missing_fields must be a list")

        _validate_window(row, errors, prefix)

        if row_kind == PUBLIC_ROW_KIND:
            if case_id not in ALLOWED_PUBLIC_CASE_IDS:
                errors.append(f"{prefix} public replay case is not Phase 5-approved")
            if row.get("parent_case_id") is not None:
                errors.append(f"{prefix} public replay parent_case_id must be null")
            if row.get("control_index") is not None:
                errors.append(f"{prefix} public replay control_index must be null")
            if row.get("control_role") is not None:
                errors.append(f"{prefix} public replay control_role must be null")
            if isinstance(case_id, str):
                public_rows_by_case_id[case_id] = row
        elif row_kind in CONTROL_ROW_KINDS:
            parent_case_id = row.get("parent_case_id")
            if not isinstance(parent_case_id, str) or not parent_case_id.strip():
                errors.append(f"{prefix} control row requires parent_case_id")
            control_index = row.get("control_index")
            if (
                not isinstance(control_index, int)
                or isinstance(control_index, bool)
                or control_index < 1
            ):
                errors.append(f"{prefix} control_index must be a positive integer")
            control_role = row.get("control_role")
            if not isinstance(control_role, str) or not control_role.strip():
                errors.append(f"{prefix} control_role must be a non-empty string")

    public_count = sum(1 for row in executable_rows if row.get("row_kind") == PUBLIC_ROW_KIND)
    if public_count > int(caps.get("max_public_replay_candidates", 0)):
        errors.append("executable manifest exceeds maximum 5 replayable public candidate cases")
    if len(executable_rows) > int(caps.get("max_executable_rows", 0)):
        errors.append("executable manifest exceeds maximum 25 executable manifest rows")

    control_counts: Counter[tuple[str, str]] = Counter()
    control_indexes: set[tuple[str, str, int]] = set()
    for index, row in enumerate(executable_rows):
        if row.get("row_kind") not in CONTROL_ROW_KINDS:
            continue
        prefix = f"executable_rows[{index}]"
        parent_case_id = row.get("parent_case_id")
        row_kind = row.get("row_kind")
        if parent_case_id not in public_rows_by_case_id:
            errors.append(
                f"{prefix} parent_case_id must reference a public_replay_candidate"
            )
        if isinstance(parent_case_id, str) and isinstance(row_kind, str):
            control_counts[(parent_case_id, row_kind)] += 1
        control_index = row.get("control_index")
        if (
            isinstance(parent_case_id, str)
            and isinstance(row_kind, str)
            and isinstance(control_index, int)
            and not isinstance(control_index, bool)
        ):
            key = (parent_case_id, row_kind, control_index)
            if key in control_indexes:
                errors.append(
                    f"{prefix} duplicate control_index {control_index} for {parent_case_id} {row_kind}"
                )
            control_indexes.add(key)

    adjacent_cap = int(caps.get("max_adjacent_controls_per_case", 0))
    null_cap = int(caps.get("max_null_controls_per_case", 0))
    for (parent_case_id, row_kind), count in sorted(control_counts.items()):
        cap = adjacent_cap if row_kind == "adjacent_control_window" else null_cap
        if count > cap:
            errors.append(f"{parent_case_id} exceeds {row_kind} cap of {cap}")

    return executable_rows


def _validate_audit_rows(raw_rows: Any, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(raw_rows, list):
        errors.append("audit_rows must be a list")
        return []

    audit_rows: list[dict[str, Any]] = []
    row_ids: set[str] = set()
    for index, raw_row in enumerate(raw_rows):
        prefix = f"audit_rows[{index}]"
        if not isinstance(raw_row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        row = raw_row
        audit_rows.append(row)
        _append_required_field_errors(errors, row, REQUIRED_AUDIT_ROW_FIELDS, prefix)

        row_id = row.get("row_id")
        if not isinstance(row_id, str) or not row_id.strip():
            errors.append(f"{prefix} row_id must be a non-empty string")
        elif row_id in row_ids:
            errors.append(f"duplicate audit row_id: {row_id}")
        else:
            row_ids.add(row_id)

        if row.get("row_kind") not in AUDIT_ROW_KINDS:
            errors.append(f"{prefix} row_kind must be one of {sorted(AUDIT_ROW_KINDS)}")
        if row.get("evidence_class") not in AUDIT_EVIDENCE_CLASSES:
            errors.append(
                f"{prefix} evidence_class must be one of {sorted(AUDIT_EVIDENCE_CLASSES)}"
            )
        if row.get("expected_status") != AUDIT_ONLY_STATUS:
            errors.append(f"{prefix} audit expected_status must be {AUDIT_ONLY_STATUS}")
        if row.get("market_data_query_allowed") is not False:
            errors.append(f"{prefix} audit rows must not query market data")
        if not isinstance(row.get("missing_fields"), list) or not row.get("missing_fields"):
            errors.append(f"{prefix} missing_fields must be a non-empty list")
    return audit_rows


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate manifest boundedness and evidence-class contracts."""

    errors: list[str] = []
    warnings: list[str] = []

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if manifest.get("execution_mode") != "dry_run_fixture_only":
        errors.append("execution_mode must be dry_run_fixture_only")
    if manifest.get("market_data_access") != "disabled_in_dry_run":
        errors.append("market_data_access must be disabled_in_dry_run")

    caps = _validate_caps(manifest, errors)
    _validate_run_level_gate(manifest, errors)
    _validate_source_metadata(manifest, errors)
    _validate_metric_wording_contract(manifest, errors)
    executable_rows = _validate_executable_rows(
        manifest.get("executable_rows"),
        caps,
        errors,
    )
    audit_rows = _validate_audit_rows(manifest.get("audit_rows"), errors)

    top_level_forbidden = [
        key
        for key in (
            "universe",
            "dynamic_universe",
            "full_history",
            "parameter_sweep",
            "threshold_search",
            "threshold_optimization",
            "optimizer",
            "optimizer_loop",
            "allow_optimizer_loops",
            "search_loop",
            "allow_search_loops",
            "walk_forward",
            "broad_scoreboard",
        )
        if key in manifest
    ]
    if top_level_forbidden:
        errors.append(
            "manifest contains forbidden broad-validation request keys: "
            + ", ".join(sorted(top_level_forbidden))
        )

    labels = manifest.get("metric_labels", [])
    if not isinstance(labels, list):
        errors.append("metric_labels must be a list")
    else:
        disallowed = sorted(set(labels) & DISALLOWED_REPORT_LABELS)
        if disallowed:
            errors.append(
                "metric_labels contain disallowed overclaim labels: "
                + ", ".join(disallowed)
            )

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "executable_row_count": len(executable_rows),
        "public_replay_candidate_count": sum(
            1 for row in executable_rows if row.get("row_kind") == PUBLIC_ROW_KIND
        ),
        "adjacent_control_count": sum(
            1
            for row in executable_rows
            if row.get("row_kind") == "adjacent_control_window"
        ),
        "null_control_count": sum(
            1
            for row in executable_rows
            if row.get("row_kind") == "null_control_window"
        ),
        "audit_row_count": len(audit_rows),
    }


def manifest_hash(manifest_path: Path) -> str:
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def realized_outcome_na() -> dict[str, str]:
    return {field: "N/A" for field in REALIZED_OUTCOME_FIELDS}


def _data_gap_reason(row: dict[str, Any]) -> str | None:
    availability = row.get("data_availability")
    if not isinstance(availability, dict):
        return None
    if availability.get("available") is not False:
        return None
    reason = availability.get("missing_reason") or "required market data unavailable"
    symbol = availability.get("symbol") or row.get("symbol")
    window = availability.get("window") or row.get("allowed_window")
    return f"data_missing: {reason}; symbol={symbol}; window={window}"


def _row_final_status_and_reason(row: dict[str, Any]) -> tuple[str, str]:
    data_gap = _data_gap_reason(row)
    if data_gap:
        return "data_missing", data_gap

    expected_status = str(row.get("expected_status"))
    if expected_status == "insufficient_evidence":
        return (
            "insufficient_evidence",
            "public evidence gap remains explicit; no exact fill/timestamp/account data was invented",
        )
    if expected_status == "not_reproduced":
        return (
            "not_reproduced",
            "dry-run fixture marks adequate-evidence/adequate-data no-signal outcome; no market data queried here",
        )
    if expected_status == "reproduced":
        return (
            "reproduced",
            "dry-run fixture marks reproduced signal; exact realized fills still remain N/A unless primary evidence is added",
        )
    return expected_status, "dry-run manifest/report gate only; no market data queried"


def _row_result(row: dict[str, Any]) -> dict[str, Any]:
    final_status, reason = _row_final_status_and_reason(row)
    data_query_status = "data_missing" if final_status == "data_missing" else "not_queried_dry_run"
    return {
        "row_id": row.get("row_id"),
        "row_kind": row.get("row_kind"),
        "case_id": row.get("case_id"),
        "parent_case_id": row.get("parent_case_id"),
        "symbol": row.get("symbol"),
        "direction": row.get("direction"),
        "evidence_class": row.get("evidence_class"),
        "final_status": final_status,
        "market_granularity": row.get("market_granularity"),
        "allowed_window": row.get("allowed_window"),
        "missing_fields": row.get("missing_fields", []),
        "matched_signal_count": 1 if final_status == "reproduced" else 0,
        "data_query_status": data_query_status,
        "data_availability": row.get("data_availability", {"checked": False, "reason": "dry_run_fixture_only"}),
        "realized_outcome": realized_outcome_na(),
        "reason": reason,
    }


def _audit_result(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row.get("row_id"),
        "row_kind": row.get("row_kind"),
        "case_id": row.get("case_id"),
        "symbol": row.get("symbol"),
        "direction": row.get("direction"),
        "evidence_class": row.get("evidence_class"),
        "final_status": AUDIT_ONLY_STATUS,
        "market_data_query_allowed": False,
        "missing_fields": row.get("missing_fields", []),
        "realized_outcome": realized_outcome_na(),
        "reason": row.get(
            "reason",
            "audit-only public evidence row; insufficient evidence until upgraded",
        ),
    }


def build_dry_run_report(
    manifest: dict[str, Any],
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic no-data report from a valid or invalid manifest."""

    validation = validate_manifest(manifest)
    executable_rows = manifest.get("executable_rows", [])
    if not isinstance(executable_rows, list):
        executable_rows = []
    audit_rows = manifest.get("audit_rows", [])
    if not isinstance(audit_rows, list):
        audit_rows = []

    row_results = [
        _row_result(row) for row in executable_rows if isinstance(row, dict)
    ]
    audit_results = [
        _audit_result(row) for row in audit_rows if isinstance(row, dict)
    ]

    public_results = [
        result
        for result in row_results
        if result.get("row_kind") == PUBLIC_ROW_KIND
    ]
    control_results = [
        result
        for result in row_results
        if result.get("row_kind") in CONTROL_ROW_KINDS
    ]
    reproduced_public_count = sum(
        1 for result in public_results if result.get("final_status") == "reproduced"
    )
    promotion_threshold = int(
        manifest.get("run_level_gate", {}).get("required_public_reproduced", 5)
    )
    promoted = validation["passed"] and reproduced_public_count >= promotion_threshold
    overall_status = (
        FAILED_RUN_STATUS
        if not validation["passed"]
        else PROMOTED_RUN_STATUS if promoted else RESEARCH_ONLY_RUN_STATUS
    )

    public_status_counts = Counter(
        str(result.get("final_status")) for result in public_results
    )
    control_status_counts = Counter(
        str(result.get("final_status")) for result in control_results
    )
    data_query_counts = Counter(
        str(result.get("data_query_status")) for result in row_results
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest.get("run_id", "martinluk_phase5_dry_run_v1"),
        "execution_mode": "dry_run_fixture_only",
        "overall_run_status": overall_status,
        "promoted": promoted,
        "promotion_threshold": promotion_threshold,
        "reproduced_public_replay_candidate_count": reproduced_public_count,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "manifest_sha256": manifest_hash(manifest_path) if manifest_path else None,
        "source_metadata": manifest.get("data_sources", {}),
        "market_data_queries": [],
        "data_availability_counts": dict(sorted(data_query_counts.items())),
        "public_case_status_counts": dict(sorted(public_status_counts.items())),
        "bounded_historical_controls_summary": {
            "control_count": len(control_results),
            "status_counts": dict(sorted(control_status_counts.items())),
            "counts_by_kind": dict(
                sorted(Counter(str(row.get("row_kind")) for row in control_results).items())
            ),
            "promotion_count_note": "controls never count toward public-case promotion",
        },
        "trace_diagnostic_errors": [],
        "row_results": row_results,
        "audit_results": audit_results,
        "no_overclaim_statement": NO_OVERCLAIM_STATEMENT,
        "metric_wording_contract": manifest.get("metric_wording_contract", {}),
        "rejected_broad_backtest_requests": validation["errors"],
        "validation": validation,
    }
    return report


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render a concise markdown closeout for the dry-run report."""

    lines = [
        "# MartinLuk Phase 5 Bounded Validation Dry-Run Report",
        "",
        f"Run ID: `{report['run_id']}`",
        f"Overall run status: `{report['overall_run_status']}`",
        f"Promoted: `{str(report['promoted']).lower()}`",
        "",
        "## No-overclaim boundary",
        "",
        report["no_overclaim_statement"],
        "",
        "## Manifest and sources",
        "",
        f"- Manifest: `{report.get('manifest_path')}`",
        f"- Manifest SHA-256: `{report.get('manifest_sha256')}`",
        f"- Daily source: `{report['source_metadata'].get('daily')}`",
        f"- Minute source: `{report['source_metadata'].get('minute')}`",
        "- Market data queries in this dry run: `0`",
        "",
        "## Public replay gate",
        "",
        f"- Required reproduced public replay candidates: `{report['promotion_threshold']}`",
        f"- Reproduced public replay candidates: `{report['reproduced_public_replay_candidate_count']}`",
        "- Controls counted toward promotion: `0`",
        f"- Public status counts: `{json.dumps(report['public_case_status_counts'], sort_keys=True)}`",
        "",
        "## Bounded controls",
        "",
        f"- Control rows: `{report['bounded_historical_controls_summary']['control_count']}`",
        "- Control status counts: "
        f"`{json.dumps(report['bounded_historical_controls_summary']['status_counts'], sort_keys=True)}`",
        "- Note: controls are diagnostic only and never count toward public-case promotion.",
        "",
        "## Audit-only evidence rows",
        "",
    ]

    if report["audit_results"]:
        lines.append("| case_id | evidence_class | status | reason |")
        lines.append("| --- | --- | --- | --- |")
        for row in report["audit_results"]:
            reason = str(row.get("reason", "")).replace("|", "\\|")
            lines.append(
                f"| `{row['case_id']}` | `{row['evidence_class']}` | "
                f"`{row['final_status']}` | {reason} |"
            )
    else:
        lines.append("No audit-only rows supplied.")

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Manifest validation passed: `{str(report['validation']['passed']).lower()}`",
            f"- Executable rows: `{report['validation']['executable_row_count']}`",
            f"- Public replay rows: `{report['validation']['public_replay_candidate_count']}`",
            f"- Adjacent controls: `{report['validation']['adjacent_control_count']}`",
            f"- Null controls: `{report['validation']['null_control_count']}`",
            f"- Audit rows: `{report['validation']['audit_row_count']}`",
            "- Validation errors: "
            f"`{json.dumps(report['validation']['errors'], sort_keys=True)}`",
            "",
            "## Realized outcome fields",
            "",
            "Realized entry, exit, size, fees, slippage, and account P&L are `N/A` "
            "for every row because current public evidence does not contain exact fills.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate the manifest and print validation JSON only",
    )
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    if args.check_only:
        payload = validate_manifest(manifest)
    else:
        payload = build_dry_run_report(manifest, args.manifest)

    if args.output_json is not None:
        args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    if args.output_md is not None:
        report = payload if not args.check_only else build_dry_run_report(manifest, args.manifest)
        args.output_md.write_text(render_markdown_report(report))

    validation = payload if args.check_only else payload["validation"]
    return 0 if validation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
