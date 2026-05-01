from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "004-martinluk-primitive"
    / "run_phase5_bounded_replay.py"
)
REQUEST_PATH = MODULE_PATH.with_name("phase5-1-replay-request.json")
MANIFEST_PATH = MODULE_PATH.with_name("phase5-replay-manifest.json")


def load_phase5_1_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "martinluk_phase5_bounded_replay",
        MODULE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def phase5_1() -> Any:
    return load_phase5_1_module()


@pytest.fixture()
def request_payload() -> dict[str, Any]:
    return json.loads(REQUEST_PATH.read_text())


@pytest.fixture()
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text())


def test_phase5_1_request_accepts_current_manifest_hash(
    phase5_1: Any,
    request_payload: dict[str, Any],
) -> None:
    result = phase5_1.validate_replay_request(copy.deepcopy(request_payload))

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["phase5_manifest_sha256"] == request_payload["phase5_manifest_sha256"]


def test_phase5_1_request_rejects_manifest_hash_mismatch_before_query_planning(
    phase5_1: Any,
    request_payload: dict[str, Any],
    tmp_path: Path,
) -> None:
    request_payload["phase5_manifest_sha256"] = "0" * 64
    request_path = tmp_path / "phase5-1-replay-request.json"
    request_path.write_text(json.dumps(request_payload))

    class ExplodingLoaders:
        def load_daily_data(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - must not be called
            raise AssertionError("loader should not be called")

        def query_minute_data(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - must not be called
            raise AssertionError("loader should not be called")

    result = phase5_1.run_bounded_replay(
        request_path=request_path,
        query_ledger_path=tmp_path / "phase5-1-query-ledger.json",
        runtime_path=tmp_path / "phase5-1-runtime.json",
        output_json_path=tmp_path / "phase5-1-bounded-replay-report.json",
        output_md_path=tmp_path / "phase5-1-bounded-replay-report.md",
        loaders=ExplodingLoaders(),
    )

    assert result["ok"] is False
    assert any("manifest_hash_mismatch" in error for error in result["errors"])
    runtime = json.loads((tmp_path / "phase5-1-runtime.json").read_text())
    assert runtime["loader_call_count"] == 0
    assert runtime["fail_closed"] is True


@pytest.mark.parametrize(
    ("mutation", "fragment"),
    [
        (lambda req: req.update({"allowed_runner": "src/core/backtester.py"}), "unknown_runner"),
        (
            lambda req: req.update(
                {"allowed_runner": "specs/004-martinluk-primitive/validate_public_cases.py"}
            ),
            "validate_public_cases",
        ),
        (lambda req: req.update({"loader_import_module": "data.unapproved"}), "unapproved_loader_module"),
        (lambda req: req.update({"optimizer_loop": True}), "forbidden_broad_replay_request_keys"),
    ],
)
def test_phase5_1_request_rejects_forbidden_surfaces_and_broad_keys(
    phase5_1: Any,
    request_payload: dict[str, Any],
    mutation: Any,
    fragment: str,
) -> None:
    mutation(request_payload)

    result = phase5_1.validate_replay_request(request_payload)

    assert result["passed"] is False
    assert fragment in "\n".join(result["errors"])


def test_phase5_1_query_plan_matches_manifest_derived_union_and_excludes_audit_rows(
    phase5_1: Any,
    manifest: dict[str, Any],
    request_payload: dict[str, Any],
) -> None:
    ledger = phase5_1.build_query_plan(copy.deepcopy(manifest), copy.deepcopy(request_payload), MANIFEST_PATH)
    validation = phase5_1.validate_query_ledger(ledger, manifest, request_payload, MANIFEST_PATH)
    executable_row_ids = {row["row_id"] for row in manifest["executable_rows"]}
    audit_row_ids = {row["row_id"] for row in manifest["audit_rows"]}
    ledger_row_ids = {row_id for record in ledger["records"] for row_id in record["row_ids"]}

    assert validation["passed"] is True
    assert ledger["query_count"] == len(ledger["records"])
    assert ledger_row_ids == executable_row_ids
    assert ledger_row_ids.isdisjoint(audit_row_ids)
    assert all(record["effective_symbols"] == record["symbols"] for record in ledger["records"])
    assert all(record["warmup_policy"].get("no_forward_expansion") is True for record in ledger["records"])
    assert all(
        record["raw_loader_scope"] == "date_only_daily_cache"
        for record in ledger["records"]
        if record["granularity"] == "daily"
    )


def test_phase5_1_query_ledger_rejects_audit_row_and_extra_symbol(
    phase5_1: Any,
    manifest: dict[str, Any],
    request_payload: dict[str, Any],
) -> None:
    ledger = phase5_1.build_query_plan(copy.deepcopy(manifest), copy.deepcopy(request_payload), MANIFEST_PATH)
    ledger["records"][0]["row_ids"].append(manifest["audit_rows"][0]["row_id"])
    ledger["records"][0]["effective_symbols"].append("EXTRA")

    result = phase5_1.validate_query_ledger(ledger, manifest, request_payload, MANIFEST_PATH)

    assert result["passed"] is False
    errors = "\n".join(result["errors"])
    assert "audit_rows_execute_forbidden" in errors
    assert "extra_or_missing_effective_symbols" in errors


def test_phase5_1_daily_loader_overfetch_is_filtered_to_effective_manifest_symbols(
    phase5_1: Any,
    manifest: dict[str, Any],
    request_payload: dict[str, Any],
) -> None:
    ledger = phase5_1.build_query_plan(copy.deepcopy(manifest), copy.deepcopy(request_payload), MANIFEST_PATH)
    first_daily = next(record for record in ledger["records"] if record["granularity"] == "daily")
    ledger["records"] = [first_daily]
    target_symbol = first_daily["effective_symbols"][0]

    class FakeLoaders:
        def load_daily_data(self, start_date: str, end_date: str) -> pd.DataFrame:
            return pd.DataFrame(
                {
                    "ticker": [target_symbol, "EXTRA"],
                    "session_date": [start_date, start_date],
                    "open": [10.0, 10.0],
                    "high": [11.0, 11.0],
                    "low": [9.0, 9.0],
                    "close": [10.5, 10.5],
                    "volume": [1000, 1000],
                }
            )

    class RecordingStrategy:
        seen_symbols: list[str] = []
        select_universe_called = False

        def select_universe(self, *_args: Any, **_kwargs: Any) -> list[str]:  # pragma: no cover - must not be called
            type(self).select_universe_called = True
            raise AssertionError("select_universe must not be called")

        def generate_signals(self, frames: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
            type(self).seen_symbols.extend(sorted(frames))
            return {symbol: pd.Series([0.0], index=frame.index) for symbol, frame in frames.items()}

        def get_signal_trace(self) -> dict[str, Any]:
            return {"signals": []}

    updated, outcomes, errors, loader_calls = phase5_1.execute_query_ledger(
        ledger,
        manifest,
        request_payload,
        loaders=FakeLoaders(),
        strategy_cls=RecordingStrategy,
    )

    assert errors == []
    assert loader_calls == 1
    assert RecordingStrategy.select_universe_called is False
    assert RecordingStrategy.seen_symbols == [target_symbol]
    assert "EXTRA" not in updated["records"][0]["raw_to_effective_filter_proof"]["strategy_input_symbols"]
    assert "EXTRA" in updated["records"][0]["raw_to_effective_filter_proof"]["filtered_out_symbol_sample"]
    assert set(outcomes) == set(first_daily["row_ids"])


@pytest.mark.parametrize(
    ("positive_index", "trace_date", "expected_signal_present"),
    [
        (0, "2024-05-08", False),
        (1, "2024-05-09", True),
    ],
)
def test_phase5_2_signal_matching_uses_allowed_window_not_warmup(
    phase5_1: Any,
    manifest: dict[str, Any],
    request_payload: dict[str, Any],
    positive_index: int,
    trace_date: str,
    expected_signal_present: bool,
) -> None:
    target_row = next(
        row
        for row in manifest["executable_rows"]
        if row["row_id"] == "p5-control-amc-adjacent-1"
    )
    manifest["executable_rows"] = [target_row]
    ledger = phase5_1.build_query_plan(copy.deepcopy(manifest), copy.deepcopy(request_payload), MANIFEST_PATH)

    class FakeLoaders:
        def load_daily_data(self, *args: Any, **kwargs: Any) -> pd.DataFrame:  # pragma: no cover - not used
            raise AssertionError("daily loader should not be called")

        def query_minute_data(self, tickers: list[str], start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
            assert tickers == ["AMC"]
            assert start_date == "2024-05-08"
            assert end_date == "2024-05-10"
            return {
                "AMC": pd.DataFrame(
                    {
                        "ticker": ["AMC", "AMC"],
                        "session_date": ["2024-05-08", "2024-05-09"],
                        "open": [3.2, 3.3],
                        "high": [3.3, 3.4],
                        "low": [3.1, 3.2],
                        "close": [3.25, 3.35],
                        "volume": [1000, 1000],
                    }
                )
            }

    class WindowAwareStrategy:
        def generate_signals(self, frames: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
            frame = frames["AMC"]
            values = [0.0, 0.0]
            values[positive_index] = 1.0
            return {"AMC": pd.Series(values, index=frame.index)}

        def get_signal_trace(self) -> dict[str, Any]:
            return {"signals": [{"symbol": "AMC", "direction": "long", "date": trace_date}]}

    updated, outcomes, errors, loader_calls = phase5_1.execute_query_ledger(
        ledger,
        manifest,
        request_payload,
        loaders=FakeLoaders(),
        strategy_cls=WindowAwareStrategy,
    )

    assert errors == []
    assert loader_calls == 1
    assert updated["records"][0]["signals_by_symbol"] == {"AMC": expected_signal_present}
    assert outcomes["p5-control-amc-adjacent-1"]["signal_present"] is expected_signal_present


def test_phase5_1_rejects_existing_phase5_output_paths_without_overwrite(
    phase5_1: Any,
    request_payload: dict[str, Any],
    tmp_path: Path,
) -> None:
    request_path = tmp_path / "phase5-1-replay-request.json"
    request_path.write_text(json.dumps(request_payload))
    protected = MODULE_PATH.with_name("phase5-bounded-validation-report.json")
    before = protected.read_bytes()

    result = phase5_1.run_bounded_replay(
        request_path=request_path,
        query_ledger_path=tmp_path / "phase5-1-query-ledger.json",
        runtime_path=tmp_path / "phase5-1-runtime.json",
        output_json_path=protected,
        output_md_path=tmp_path / "phase5-1-bounded-replay-report.md",
    )

    assert result["ok"] is False
    assert any("protected_phase5_output_path" in error for error in result["errors"])
    assert protected.read_bytes() == before


def test_phase5_1_control_outcome_mapping_and_promotion_excludes_controls(
    phase5_1: Any,
    manifest: dict[str, Any],
    request_payload: dict[str, Any],
) -> None:
    row_outcomes: dict[str, dict[str, Any]] = {}
    for row in manifest["executable_rows"]:
        row_outcomes[row["row_id"]] = {
            "query_id": "fixture-query",
            "loader_status": "executed",
            "signal_present": row["row_kind"] != "public_replay_candidate",
        }

    report = phase5_1.build_report(
        manifest,
        request_payload,
        {"records": []},
        row_outcomes,
        manifest_sha256=request_payload["phase5_manifest_sha256"],
        request_path=REQUEST_PATH,
        query_ledger_path=MODULE_PATH.with_name("phase5-1-query-ledger.json"),
        runtime_path=MODULE_PATH.with_name("phase5-1-runtime.json"),
        request_sha256="request-sha",
        query_ledger_sha256="ledger-sha",
        runtime_sha256="runtime-sha",
        validation={"passed": True, "errors": []},
    )

    assert report["public_replay_candidate_summary"]["status_counts"] == {"insufficient_evidence": 5}
    assert report["control_summary"]["false_positive_control_count"] == 20
    assert report["control_summary"]["controls_counted_toward_promotion"] == 0
    assert report["promoted"] is False


def test_phase5_2_reports_false_positive_control_ids_and_vetoes_promotion(
    phase5_1: Any,
    manifest: dict[str, Any],
    request_payload: dict[str, Any],
) -> None:
    public_rows = [
        row for row in manifest["executable_rows"] if row["row_kind"] == "public_replay_candidate"
    ]
    false_positive_control_ids = [
        "p5-control-amc-adjacent-1",
        "p5-control-amc-null-1",
        "p5-control-amc-null-2",
    ]

    for row in public_rows:
        row["missing_fields"] = []
        row["expected_status"] = "replayable_window_candidate"
    manifest["run_level_gate"]["required_public_reproduced"] = len(public_rows)

    row_outcomes: dict[str, dict[str, Any]] = {}
    for row in manifest["executable_rows"]:
        row_outcomes[row["row_id"]] = {
            "query_id": f"query-{row['row_id']}",
            "loader_status": "executed",
            "signal_present": row["row_kind"] == "public_replay_candidate"
            or row["row_id"] in false_positive_control_ids,
        }

    report = phase5_1.build_report(
        manifest,
        request_payload,
        {"records": []},
        row_outcomes,
        manifest_sha256=request_payload["phase5_manifest_sha256"],
        request_path=REQUEST_PATH,
        query_ledger_path=MODULE_PATH.with_name("phase5-2-query-ledger.json"),
        runtime_path=MODULE_PATH.with_name("phase5-2-runtime.json"),
        request_sha256="request-sha",
        query_ledger_sha256="ledger-sha",
        runtime_sha256="runtime-sha",
        validation={"passed": True, "errors": []},
    )

    assert report["reproduced_public_replay_candidate_count"] == len(public_rows)
    assert report["control_summary"]["false_positive_control_count"] == len(false_positive_control_ids)
    assert report["control_summary"]["false_positive_control_row_ids"] == false_positive_control_ids
    assert report["control_summary"]["controls_counted_toward_promotion"] == 0
    assert report["promoted"] is False
    assert report["overall_run_status"] == "research_only"
    assert report["diagnostic_promotion_veto"] == {
        "active": True,
        "false_positive_control_count": len(false_positive_control_ids),
        "false_positive_control_row_ids": false_positive_control_ids,
        "controls_counted_toward_promotion": 0,
        "reasons": ["false_positive_controls_present"],
    }


def test_phase5_2_audit_and_executable_rows_keep_realized_outcomes_na(
    phase5_1: Any,
    manifest: dict[str, Any],
    request_payload: dict[str, Any],
) -> None:
    row_outcomes: dict[str, dict[str, Any]] = {
        row["row_id"]: {
            "query_id": f"query-{row['row_id']}",
            "loader_status": "executed",
            "signal_present": False,
        }
        for row in manifest["executable_rows"]
    }

    report = phase5_1.build_report(
        manifest,
        request_payload,
        {"records": []},
        row_outcomes,
        manifest_sha256=request_payload["phase5_manifest_sha256"],
        request_path=REQUEST_PATH,
        query_ledger_path=MODULE_PATH.with_name("phase5-2-query-ledger.json"),
        runtime_path=MODULE_PATH.with_name("phase5-2-runtime.json"),
        request_sha256="request-sha",
        query_ledger_sha256="ledger-sha",
        runtime_sha256="runtime-sha",
        validation={"passed": True, "errors": []},
    )

    expected_na = phase5_1.realized_outcome_na()
    assert report["realized_outcome_fields"] == expected_na
    assert all(row["realized_outcome"] == expected_na for row in report["row_results"])
    assert all(row["realized_outcome"] == expected_na for row in report["audit_results"])
    assert all(row["market_data_query_allowed"] is False for row in report["audit_results"])
    assert all("query_id" not in row for row in report["audit_results"])
