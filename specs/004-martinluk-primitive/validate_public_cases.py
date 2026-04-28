#!/usr/bin/env python3
"""Validate MartinLuk public-operation case ledger.

This phase validates evidence structure only. Future versions may accept
--signals-path to compare generated strategy signals against dated cases.
"""

from __future__ import annotations

import argparse
import json
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def validate(root: Path) -> dict[str, Any]:
    source_ledger = load_json(root / "source-ledger.json")
    cases_doc = load_json(root / "public-operation-cases.json")
    errors: list[str] = []
    source_ids = {source.get("id") for source in source_ledger.get("sources", [])}

    if cases_doc.get("replication_target") != "public_operation_reproducibility":
        errors.append("replication_target must be public_operation_reproducibility")
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

    return {
        "status": "passed" if not errors else "failed",
        "passed": not errors,
        "case_count": len(cases),
        "source_count": len(source_ids),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--signals-path", type=Path, default=None)
    args = parser.parse_args()
    result = validate(args.root)
    if args.signals_path is not None:
        result["signals_path"] = str(args.signals_path)
        result["signal_validation"] = "not_implemented_in_phase_1"
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
