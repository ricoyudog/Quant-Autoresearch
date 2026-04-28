from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "004-martinluk-primitive"
    / "validate_public_cases.py"
)


def load_validator_module() -> Any:
    spec = importlib.util.spec_from_file_location("martinluk_public_validator", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_public_case_root(root: Path, cases: list[dict[str, Any]]) -> None:
    root.mkdir(exist_ok=True)
    (root / "source-ledger.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "id": "public_source",
                        "url": "https://example.test/source",
                        "type": "fixture",
                        "use": "unit test public operation evidence",
                        "confidence": "high",
                    }
                ]
            }
        )
    )
    (root / "public-operation-cases.json").write_text(
        json.dumps(
            {
                "replication_target": "public_operation_reproducibility",
                "not_target": "private_USIC_trade_ledger_cloning",
                "cases": cases,
            }
        )
    )


def make_case(index: int, **overrides: Any) -> dict[str, Any]:
    case = {
        "case_id": f"MLUK-TEST-{index:03d}",
        "symbol": f"T{index}",
        "direction": "long",
        "confidence": "medium",
        "setup_type": "leader_pullback_prior_day_high",
        "date_window": f"2025-01-{index:02d}",
        "context_rules": ["leader context"],
        "entry_trigger": "prior_day_high_break_after_pullback",
        "stop_rule": "low_of_day",
        "trim_rule": "partial_after_R_expansion",
        "exit_rule": "close_below_9ema",
        "expected_signal_behavior": "emit long after pullback trigger",
        "source_ids": ["public_source"],
        "missing_fields": ["entry fill"],
    }
    case.update(overrides)
    return case


def write_signal_trace(path: Path, signals: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "martinluk_public_signal_trace_v1",
                "replication_target": "public_operation_reproducibility",
                "signals": signals,
            }
        )
    )


def make_signal(case: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    signal = {
        "signal_id": f"{case['case_id']}-signal",
        "case_id": case["case_id"],
        "symbol": case["symbol"],
        "direction": case["direction"],
        "date": case["date_window"],
        "setup_type": case["setup_type"],
        "entry_trigger": case["entry_trigger"],
        "data_status": "available",
    }
    signal.update(overrides)
    return signal


def test_signals_path_reproduces_five_exact_public_cases(tmp_path: Path) -> None:
    validator = load_validator_module()
    cases = [make_case(index) for index in range(1, 8)]
    write_public_case_root(tmp_path, cases)
    signals_path = tmp_path / "signals.json"
    write_signal_trace(signals_path, [make_signal(case) for case in cases[:5]])

    result = validator.validate(tmp_path, signals_path)

    assert result["status"] == "passed"
    assert result["passed"] is True
    signal_validation = result["signal_validation"]
    assert signal_validation["reproduced_count"] == 5
    assert signal_validation["classification_counts"]["reproduced"] == 5
    assert signal_validation["classification_counts"]["not_reproduced"] == 2


def test_unknown_public_date_classifies_as_insufficient_evidence(
    tmp_path: Path,
) -> None:
    validator = load_validator_module()
    cases = [
        make_case(
            index,
            date_window="unknown_public_interview_example",
            missing_fields=["exact date", "entry fill"],
        )
        for index in range(1, 8)
    ]
    case = cases[0]
    write_public_case_root(tmp_path, cases)
    signals_path = tmp_path / "signals.json"
    write_signal_trace(signals_path, [make_signal(case, date="2025-01-01")])

    result = validator.validate(tmp_path, signals_path)

    assert result["status"] == "insufficient_evidence"
    assert result["passed"] is False
    case_result = result["signal_validation"]["case_results"][0]
    assert case_result["classification"] == "insufficient_evidence"
    assert "date_window is not reconstructable" in case_result["reason"]


def test_trace_data_missing_is_explicit_not_silent_pass(tmp_path: Path) -> None:
    validator = load_validator_module()
    cases = [make_case(index) for index in range(1, 8)]
    case = cases[0]
    write_public_case_root(tmp_path, cases)
    signals_path = tmp_path / "signals.json"
    write_signal_trace(
        signals_path,
        [make_signal(case, data_status="missing")],
    )

    result = validator.validate(tmp_path, signals_path)

    assert result["status"] == "failed"
    assert result["passed"] is False
    case_result = result["signal_validation"]["case_results"][0]
    assert case_result["classification"] == "data_missing"
    assert case_result in result["signal_validation"]["unsupported_cases"]
