from __future__ import annotations

import json
from pathlib import Path


SPEC_DIR = Path(__file__).resolve().parents[2] / "specs" / "004-martinluk-primitive"


def load_report(name: str) -> dict:
    return json.loads((SPEC_DIR / name).read_text())


def normalize_statement(statement: str) -> str:
    return statement.lower().replace("-", " ")


def test_phase5_reports_preserve_no_overclaim_statement() -> None:
    reports = [
        load_report("phase5-bounded-validation-report.json"),
        load_report("phase5-1-bounded-replay-report.json"),
        load_report("phase5-2-bounded-replay-report.json"),
    ]

    for report in reports:
        statement = normalize_statement(report["no_overclaim_statement"])
        assert "not profit proof" in statement
        assert "not martin luk realized" in statement
        assert "not private account replication" in statement
        assert "not exact fill replication" in statement
        assert "account p&l remain n/a" in statement


def test_phase5_reports_keep_realized_outcomes_unclaimed() -> None:
    reports = [
        load_report("phase5-bounded-validation-report.json"),
        load_report("phase5-1-bounded-replay-report.json"),
        load_report("phase5-2-bounded-replay-report.json"),
    ]

    realized_fields = {
        "realized_entry_price",
        "realized_exit_price",
        "realized_position_size",
        "realized_account_pnl",
        "fees",
        "slippage",
    }
    for report in reports:
        for row in [*report["row_results"], *report["audit_results"]]:
            assert set(row["realized_outcome"]) == realized_fields
            assert set(row["realized_outcome"].values()) == {"N/A"}
