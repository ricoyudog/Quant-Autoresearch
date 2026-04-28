#!/usr/bin/env python3
"""Validate MartinLuk public-operation case ledger and signal traces."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_CASE_FIELDS = {
    "case_id",
    "symbol",
    "direction",
    "confidence",
    "setup_type",
    "date_window",
    "context_rules",
    "entry_trigger",
    "stop_rule",
    "trim_rule",
    "exit_rule",
    "expected_signal_behavior",
    "source_ids",
    "missing_fields",
}

SIGNAL_TRACE_SCHEMA_VERSION = "martinluk_public_signal_trace_v1"
REPLICATION_TARGET = "public_operation_reproducibility"
SIGNAL_CLASSIFICATIONS = {
    "reproduced",
    "not_reproduced",
    "insufficient_evidence",
    "data_missing",
}
REQUIRED_SIGNAL_FIELDS = {
    "case_id",
    "symbol",
    "direction",
    "date",
    "setup_type",
    "entry_trigger",
    "data_status",
}
REQUIRED_REPRODUCED_DIAGNOSTICS = {
    "r_multiple",
    "mae",
    "mae_unit",
    "mfe",
    "mfe_unit",
    "stop_width_pct",
    "entry_type",
    "trim_type",
    "exit_type",
}
OPEN_EXIT_NULLABLE_DIAGNOSTICS = {"r_multiple", "trim_type"}
DATA_MISSING_STATUSES = {"missing", "unavailable", "not_available"}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def parse_iso_date(value: Any) -> dt.date | None:
    if not isinstance(value, str):
        return None
    candidate = value[:10]
    if not ISO_DATE_RE.match(candidate):
        return None
    try:
        return dt.date.fromisoformat(candidate)
    except ValueError:
        return None


def parse_date_window(value: Any) -> tuple[dt.date, dt.date] | None:
    if isinstance(value, dict):
        start = parse_iso_date(value.get("start") or value.get("from"))
        end = parse_iso_date(value.get("end") or value.get("to"))
        if start and end:
            return (start, end)
        return None

    if isinstance(value, list) and len(value) == 2:
        start = parse_iso_date(value[0])
        end = parse_iso_date(value[1])
        if start and end:
            return (start, end)
        return None

    if not isinstance(value, str):
        return None

    exact = parse_iso_date(value)
    if exact and len(value) == 10:
        return (exact, exact)

    for delimiter in ("..", "/"):
        if delimiter in value:
            start_text, end_text = value.split(delimiter, 1)
            start = parse_iso_date(start_text.strip())
            end = parse_iso_date(end_text.strip())
            if start and end:
                return (start, end)
    return None


def symbol_matches(case_symbol: str, signal_symbol: str) -> bool:
    normalized_case = case_symbol.upper()
    normalized_signal = signal_symbol.upper()
    if normalized_case == normalized_signal:
        return True
    if "_" in normalized_case:
        return normalized_signal in set(normalized_case.split("_"))
    return normalized_case == "MULTI"


def missing_evidence_reasons(case: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if parse_date_window(case.get("date_window")) is None:
        reasons.append(
            f"date_window is not reconstructable: {case.get('date_window')}"
        )
    if case.get("direction") == "long_or_short_unknown":
        reasons.append("direction is unknown")
    return reasons


def signal_data_status(signal: dict[str, Any]) -> str:
    if signal.get("data_available") is False:
        return "missing"
    return str(signal.get("data_status", "")).lower()


def signal_matches_case(case: dict[str, Any], signal: dict[str, Any]) -> bool:
    window = parse_date_window(case.get("date_window"))
    signal_date = parse_iso_date(signal.get("date"))
    if window is None or signal_date is None:
        return False

    start, end = window
    return (
        start <= signal_date <= end
        and symbol_matches(str(case["symbol"]), str(signal["symbol"]))
        and signal.get("direction") == case.get("direction")
        and signal.get("setup_type") == case.get("setup_type")
        and signal.get("entry_trigger") == case.get("entry_trigger")
        and signal_data_status(signal) not in DATA_MISSING_STATUSES
    )


def _field_missing_or_null(payload: dict[str, Any], field: str) -> bool:
    return field not in payload or payload[field] is None


def validate_reproduced_signal_diagnostics(
    signal: dict[str, Any],
    signal_ref: str,
) -> list[str]:
    diagnostic_errors: list[str] = []
    exit_type = signal.get("exit_type")
    is_open_trade = exit_type == "open"
    nullable_fields = OPEN_EXIT_NULLABLE_DIAGNOSTICS if is_open_trade else set()

    if isinstance(signal.get("diagnostics"), dict):
        diagnostic_errors.append(
            f"{signal_ref} diagnostics must live directly on the signal entry; "
            "nested diagnostics objects require a schema_version decision"
        )

    for field in sorted(REQUIRED_REPRODUCED_DIAGNOSTICS):
        if field in nullable_fields:
            if field not in signal:
                diagnostic_errors.append(
                    f"{signal_ref} reproduced signal missing diagnostic field: {field}"
                )
            continue
        if _field_missing_or_null(signal, field):
            diagnostic_errors.append(
                f"{signal_ref} reproduced signal missing diagnostic field: {field}"
            )

    has_holding_period_bars = not _field_missing_or_null(
        signal, "holding_period_bars"
    )
    has_holding_period_minutes = not _field_missing_or_null(
        signal, "holding_period_minutes"
    )
    if not has_holding_period_bars and not has_holding_period_minutes:
        diagnostic_errors.append(
            f"{signal_ref} reproduced signal missing diagnostic field: "
            "holding_period_bars or holding_period_minutes"
        )

    if "mae" in signal and _field_missing_or_null(signal, "mae_unit"):
        diagnostic_errors.append(f"{signal_ref} mae requires mae_unit")
    if "mfe" in signal and _field_missing_or_null(signal, "mfe_unit"):
        diagnostic_errors.append(f"{signal_ref} mfe requires mfe_unit")

    return diagnostic_errors


def validate_signal_trace(
    signals_path: Path,
    cases: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    trace_errors: list[str] = []
    if not signals_path.exists():
        trace_errors.append(f"signals_path does not exist: {signals_path}")
        signals: list[dict[str, Any]] = []
        trace_doc: dict[str, Any] = {}
    else:
        trace_doc = load_json(signals_path)
        raw_signals = trace_doc.get("signals")
        signals = raw_signals if isinstance(raw_signals, list) else []

    if trace_doc.get("schema_version") != SIGNAL_TRACE_SCHEMA_VERSION:
        trace_errors.append(
            "signal trace schema_version must be "
            f"{SIGNAL_TRACE_SCHEMA_VERSION}"
        )
    if trace_doc.get("replication_target") != REPLICATION_TARGET:
        trace_errors.append(
            f"signal trace replication_target must be {REPLICATION_TARGET}"
        )
    if not isinstance(trace_doc.get("signals"), list):
        trace_errors.append("signal trace must include a signals list")

    signals_by_case: dict[str, list[dict[str, Any]]] = {}
    for index, signal in enumerate(signals):
        if not isinstance(signal, dict):
            trace_errors.append(f"signals[{index}] must be an object")
            continue
        missing = sorted(REQUIRED_SIGNAL_FIELDS - set(signal))
        if missing:
            trace_errors.append(
                f"signals[{index}] missing fields: {', '.join(missing)}"
            )
        signal_case_id = str(signal.get("case_id", ""))
        if signal_case_id:
            signals_by_case.setdefault(signal_case_id, []).append(signal)

    case_results: list[dict[str, Any]] = []
    diagnostic_errors: list[str] = []
    for case in cases:
        case_id = str(case.get("case_id", ""))
        candidate_signals = signals_by_case.get(case_id, [])
        evidence_reasons = missing_evidence_reasons(case)
        matched_signals = [
            (idx, signal)
            for idx, signal in enumerate(candidate_signals)
            if signal_matches_case(case, signal)
        ]
        matched_signal_ids = [
            str(signal.get("signal_id", f"{case_id}#{idx}"))
            for idx, signal in matched_signals
        ]

        for idx, signal in matched_signals:
            signal_ref = str(signal.get("signal_id", f"{case_id}#{idx}"))
            diagnostic_errors.extend(
                validate_reproduced_signal_diagnostics(signal, signal_ref)
            )

        if evidence_reasons:
            classification = "insufficient_evidence"
            reason = "; ".join(evidence_reasons)
        elif any(
            signal_data_status(signal) in DATA_MISSING_STATUSES
            for signal in candidate_signals
        ):
            classification = "data_missing"
            reason = "trace reports missing local market data"
        elif matched_signal_ids:
            classification = "reproduced"
            reason = "matched symbol, direction, setup_type, entry_trigger, and date_window"
        else:
            classification = "not_reproduced"
            reason = (
                "no matching signal found"
                if candidate_signals
                else "no signal emitted for this case"
            )

        case_results.append(
            {
                "case_id": case_id,
                "symbol": case.get("symbol"),
                "classification": classification,
                "reason": reason,
                "missing_fields": case.get("missing_fields", []),
                "matched_signal_count": len(matched_signal_ids),
                "matched_signal_ids": matched_signal_ids,
            }
        )

    classification_counts = {
        classification: sum(
            1
            for case_result in case_results
            if case_result["classification"] == classification
        )
        for classification in sorted(SIGNAL_CLASSIFICATIONS)
    }
    reproduced_count = classification_counts["reproduced"]
    required_reproduced_count = 5
    trace_errors.extend(diagnostic_errors)
    passed = not errors and not trace_errors and reproduced_count >= required_reproduced_count
    if trace_errors:
        status = "failed"
    elif passed:
        status = "passed"
    elif (
        classification_counts["insufficient_evidence"] > 0
        and classification_counts["not_reproduced"] == 0
    ):
        status = "insufficient_evidence"
    else:
        status = "failed"

    unsupported_cases = [
        case_result
        for case_result in case_results
        if case_result["classification"] in {"insufficient_evidence", "data_missing"}
    ]

    return {
        "schema_version": SIGNAL_TRACE_SCHEMA_VERSION,
        "signals_path": str(signals_path),
        "status": status,
        "passed": passed,
        "required_reproduced_count": required_reproduced_count,
        "reproduced_count": reproduced_count,
        "classification_counts": classification_counts,
        "case_results": case_results,
        "unsupported_cases": unsupported_cases,
        "diagnostic_errors": diagnostic_errors,
        "errors": trace_errors,
    }


def validate(root: Path, signals_path: Path | None = None) -> dict[str, Any]:
    source_ledger = load_json(root / "source-ledger.json")
    cases_doc = load_json(root / "public-operation-cases.json")
    errors: list[str] = []
    source_ids = {source.get("id") for source in source_ledger.get("sources", [])}

    if cases_doc.get("replication_target") != REPLICATION_TARGET:
        errors.append(f"replication_target must be {REPLICATION_TARGET}")
    if "private" not in str(cases_doc.get("not_target", "")).lower():
        errors.append("not_target must explicitly reject private ledger cloning")

    cases = cases_doc.get("cases", [])
    if len(cases) < 7:
        errors.append(f"expected at least 7 cases, found {len(cases)}")

    seen_case_ids: set[str] = set()
    for idx, case in enumerate(cases):
        prefix = f"case[{idx}]"
        missing = sorted(REQUIRED_CASE_FIELDS - set(case))
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")
            continue
        case_id = case.get("case_id")
        if not case_id:
            errors.append(f"{prefix} empty case_id")
        elif case_id in seen_case_ids:
            errors.append(f"duplicate case_id: {case_id}")
        else:
            seen_case_ids.add(case_id)
        if not case.get("source_ids"):
            errors.append(f"{case_id} has no source_ids")
        for source_id in case.get("source_ids", []):
            if source_id not in source_ids:
                errors.append(f"{case_id} references unknown source_id {source_id}")
        for list_field in ["context_rules", "source_ids", "missing_fields"]:
            if not isinstance(case.get(list_field), list) or not case.get(list_field):
                errors.append(f"{case_id} {list_field} must be a non-empty list")

    result = {
        "status": "passed" if not errors else "failed",
        "passed": not errors,
        "case_count": len(cases),
        "source_count": len(source_ids),
        "errors": errors,
    }
    if signals_path is not None:
        signal_validation = validate_signal_trace(signals_path, cases, errors)
        result["signals_path"] = str(signals_path)
        result["signal_validation"] = signal_validation
        result["status"] = signal_validation["status"] if not errors else "failed"
        result["passed"] = bool(not errors and signal_validation["passed"])
        if signal_validation["errors"]:
            result["errors"] = [*errors, *signal_validation["errors"]]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--signals-path", type=Path, default=None)
    args = parser.parse_args()
    result = validate(args.root, args.signals_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
