#!/usr/bin/env python3
"""Run MartinLuk Phase 5.1 bounded replay from a frozen Phase 5 manifest.

Phase 5.1 is intentionally not a broad backtest.  It reads the frozen
Phase 5 row ledger, verifies a replay-request hash, derives a query ledger
only from executable manifest rows, executes only approved local loaders, and
writes row-level research evidence.  It does not call select_universe(), does
not route through the public-case validator as orchestration, and does not
produce aggregate profitability or exact-fill claims.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

REQUEST_SCHEMA_VERSION = "martinluk_phase5_1_replay_request_v1"
QUERY_LEDGER_SCHEMA_VERSION = "martinluk_phase5_1_query_ledger_v1"
RUNTIME_SCHEMA_VERSION = "martinluk_phase5_1_runtime_v1"
REPORT_SCHEMA_VERSION = "martinluk_phase5_2_bounded_replay_report_v1"

PHASE5_MANIFEST_REL = "specs/004-martinluk-primitive/phase5-replay-manifest.json"
RUNNER_REL = "specs/004-martinluk-primitive/run_phase5_bounded_replay.py"
REQUEST_REL = "specs/004-martinluk-primitive/phase5-1-replay-request.json"
QUERY_LEDGER_REL = "specs/004-martinluk-primitive/phase5-1-query-ledger.json"
RUNTIME_REL = "specs/004-martinluk-primitive/phase5-1-runtime.json"
REPORT_JSON_REL = "specs/004-martinluk-primitive/phase5-1-bounded-replay-report.json"
REPORT_MD_REL = "specs/004-martinluk-primitive/phase5-1-bounded-replay-report.md"
ALLOWED_OUTPUT_PREFIXES = ("phase5-1-", "phase5-2-")

ALLOWED_LOADER_FILE = "src/data/duckdb_connector.py"
ALLOWED_LOADER_MODULE = "data.duckdb_connector"
ALLOWED_LOADERS = {"load_daily_data", "query_minute_data"}
ALLOWED_EXECUTION_MODE = "bounded_replay"
ALLOWED_STRATEGY_SURFACE = (
    "src/strategies/active_strategy.py::"
    "TradingStrategy.generate_signals/get_signal_trace"
)
FORBIDDEN_STRATEGY_SURFACE = (
    "src/strategies/active_strategy.py::TradingStrategy.select_universe"
)
FORBIDDEN_SURFACES = {
    "src/core/backtester.py",
    "specs/004-martinluk-primitive/validate_public_cases.py as orchestration",
}
PROTECTED_PHASE5_OUTPUTS = {
    "specs/004-martinluk-primitive/phase5-bounded-validation-report.json",
    "specs/004-martinluk-primitive/phase5-bounded-validation-report.md",
    "specs/004-martinluk-primitive/phase5-dry-run-report.json",
}

PUBLIC_ROW_KIND = "public_replay_candidate"
CONTROL_ROW_KINDS = {"adjacent_control_window", "null_control_window"}
EXECUTABLE_ROW_KINDS = {PUBLIC_ROW_KIND, *CONTROL_ROW_KINDS}
AUDIT_ROW_KINDS = {"research_only_case", "unsupported_case"}
RESEARCH_ONLY_RUN_STATUS = "research_only"
PROMOTED_RUN_STATUS = "promoted"
FAILED_RUN_STATUS = "failed"

REALIZED_OUTCOME_FIELDS = (
    "realized_entry_price",
    "realized_exit_price",
    "realized_position_size",
    "realized_account_pnl",
    "fees",
    "slippage",
)
CONTROL_OUTCOME_TO_FINAL_STATUS = {
    "clean_control": "not_reproduced",
    "false_positive_control": "reproduced",
    "data_missing": "data_missing",
    "insufficient_evidence": "insufficient_evidence",
}
FORBIDDEN_BROAD_REQUEST_KEYS = {
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
    "walk_forward_validation",
    "broad_scoreboard",
    "aggregate_scoreboard",
    "profit_metric",
    "sharpe",
    "cagr",
    "win_rate",
}

NO_OVERCLAIM_STATEMENT = (
    "Phase 5.1 is a bounded row-level replay of the frozen Phase 5 public "
    "candidate/control manifest. It is research-only unless all public replay "
    "candidate gates are separately satisfied. It is not a broad backtest, not "
    "profit proof, not Martin Luk realized P&L, not private-account replication, "
    "and not exact-fill replication. Realized entry, exit, size, fees, slippage, "
    "and account P&L remain N/A unless a later primary-fill evidence phase "
    "explicitly upgrades the evidence contract."
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(relative_or_absolute: str | Path) -> Path:
    path = Path(relative_or_absolute)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def repo_rel(path: str | Path) -> str:
    path_obj = Path(path)
    if not path_obj.is_absolute():
        return path_obj.as_posix()
    try:
        return path_obj.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path_obj.as_posix()


def realized_outcome_na() -> dict[str, str]:
    return {field: "N/A" for field in REALIZED_OUTCOME_FIELDS}


def realized_outcome_policy() -> dict[str, Any]:
    return {
        "fields": list(REALIZED_OUTCOME_FIELDS),
        "default": "N/A",
        "applies_to": "all row_results and audit_results",
        "primary_fill_evidence_required": True,
        "reason": "public evidence does not supply primary fills, size, fees, slippage, or account P&L",
    }


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _parse_iso_date(value: Any, *, label: str) -> dt.date:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO date string")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO date string") from exc


def _contains_fragment(values: Iterable[Any], fragment: str) -> bool:
    lowered = fragment.lower()
    return any(lowered in str(value).lower() for value in values)


def _is_allowed_phase5_1_output(path: Path) -> bool:
    rel = repo_rel(path)
    return rel not in PROTECTED_PHASE5_OUTPUTS and Path(rel).name.startswith(ALLOWED_OUTPUT_PREFIXES)


def _protected_output_errors(paths: Iterable[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        rel = repo_rel(path)
        if rel in PROTECTED_PHASE5_OUTPUTS:
            errors.append(f"protected_phase5_output_path: {rel}")
        if rel and not Path(rel).name.startswith(ALLOWED_OUTPUT_PREFIXES):
            # The runner itself is not an output.  Keep this guard focused on
            # artifacts passed to --query-ledger/--runtime/--output-*.
            errors.append(f"non_phase5_bounded_replay_output_path: {rel}")
    return errors


def validate_replay_request(request: dict[str, Any]) -> dict[str, Any]:
    """Validate the Phase 5.1 request before query planning or loaders."""

    errors: list[str] = []
    warnings: list[str] = []

    if request.get("schema_version") != REQUEST_SCHEMA_VERSION:
        errors.append(f"schema_version must be {REQUEST_SCHEMA_VERSION}")
    if not isinstance(request.get("run_id"), str) or not request.get("run_id"):
        errors.append("run_id must be a non-empty string")

    forbidden_keys = sorted(FORBIDDEN_BROAD_REQUEST_KEYS & set(request))
    if forbidden_keys:
        errors.append(
            "forbidden_broad_replay_request_keys: " + ", ".join(forbidden_keys)
        )

    manifest_path_value = request.get("phase5_manifest_path")
    manifest_path: Path | None = None
    actual_manifest_sha256: str | None = None
    if manifest_path_value != PHASE5_MANIFEST_REL:
        errors.append(f"phase5_manifest_path must be {PHASE5_MANIFEST_REL}")
    if isinstance(manifest_path_value, str) and manifest_path_value:
        manifest_path = repo_path(manifest_path_value)
        if not manifest_path.exists():
            errors.append(f"phase5_manifest_missing: {manifest_path_value}")
        else:
            actual_manifest_sha256 = sha256_path(manifest_path)
            if request.get("phase5_manifest_sha256") != actual_manifest_sha256:
                errors.append(
                    "manifest_hash_mismatch: phase5_manifest_sha256 does not match current frozen manifest"
                )
    else:
        errors.append("phase5_manifest_path must be a non-empty string")

    allowed_runner = request.get("allowed_runner")
    if allowed_runner != RUNNER_REL:
        errors.append(f"unknown_runner: allowed_runner must be {RUNNER_REL}")
    if isinstance(allowed_runner, str) and "backtester" in allowed_runner:
        errors.append("backtester_surface_forbidden: allowed_runner must not route through src/core/backtester.py")
    if isinstance(allowed_runner, str) and "validate_public_cases" in allowed_runner:
        errors.append(
            "validate_public_cases_orchestration_forbidden: Phase 5.1 must use the replay runner"
        )

    if request.get("allowed_execution_mode") != ALLOWED_EXECUTION_MODE:
        errors.append(f"allowed_execution_mode must be {ALLOWED_EXECUTION_MODE}")

    allowed_loader_paths = set(_string_list(request.get("allowed_loader_file_paths")))
    if allowed_loader_paths != {ALLOWED_LOADER_FILE}:
        errors.append(f"allowed_loader_file_paths must be [{ALLOWED_LOADER_FILE}]")
    allowed_loader_modules = set(_string_list(request.get("allowed_loader_import_modules")))
    if allowed_loader_modules != {ALLOWED_LOADER_MODULE}:
        errors.append(f"allowed_loader_import_modules must be [{ALLOWED_LOADER_MODULE}]")
    allowed_loaders = set(_string_list(request.get("allowed_loaders")))
    if allowed_loaders != ALLOWED_LOADERS:
        errors.append(f"allowed_loaders must be {sorted(ALLOWED_LOADERS)}")
    if request.get("loader_file_path") != ALLOWED_LOADER_FILE:
        errors.append(f"unapproved_loader_file: loader_file_path must be {ALLOWED_LOADER_FILE}")
    if request.get("loader_import_module") != ALLOWED_LOADER_MODULE:
        errors.append(
            f"unapproved_loader_module: loader_import_module must be {ALLOWED_LOADER_MODULE}"
        )

    if request.get("strategy_surface") != ALLOWED_STRATEGY_SURFACE:
        errors.append("strategy_surface must be generate_signals/get_signal_trace only")
    if request.get("explicitly_forbidden_strategy_surface") != FORBIDDEN_STRATEGY_SURFACE:
        errors.append("explicitly_forbidden_strategy_surface must forbid select_universe")

    forbidden_surfaces = set(_string_list(request.get("forbidden_surfaces")))
    missing_forbidden = sorted(FORBIDDEN_SURFACES - forbidden_surfaces)
    if missing_forbidden:
        errors.append("forbidden_surfaces missing: " + ", ".join(missing_forbidden))
    if any("backtester" in surface for surface in forbidden_surfaces) is False:
        errors.append("backtester_surface_forbidden contract must be explicit")
    if any("validate_public_cases" in surface for surface in forbidden_surfaces) is False:
        errors.append("validate_public_cases_orchestration_forbidden contract must be explicit")

    expected_exact_values = {
        "max_executable_rows": 25,
        "max_public_replay_candidates": 5,
        "max_adjacent_controls_per_case": 2,
        "max_null_controls_per_case": 2,
        "max_daily_warmup_trading_days": 20,
        "max_minute_warmup_session_days": 1,
        "audit_rows_execute": False,
        "controls_count_toward_promotion": False,
    }
    for key, expected in expected_exact_values.items():
        if request.get(key) != expected:
            errors.append(f"{key} must be {expected!r}")

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "phase5_manifest_sha256": actual_manifest_sha256,
    }


def _executable_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in _as_list(manifest.get("executable_rows"))
        if isinstance(row, dict) and row.get("row_kind") in EXECUTABLE_ROW_KINDS
    ]


def _audit_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in _as_list(manifest.get("audit_rows"))
        if isinstance(row, dict) and row.get("row_kind") in AUDIT_ROW_KINDS
    ]


def _date_minus_days(value: str, days: int) -> str:
    return (_parse_iso_date(value, label="allowed_window.start") - dt.timedelta(days=days)).isoformat()


def _query_base_for_row(row: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    row_id = str(row.get("row_id"))
    symbol = str(row.get("symbol"))
    granularity = str(row.get("market_granularity"))
    window = row.get("allowed_window")
    if not isinstance(window, dict):
        raise ValueError(f"row {row_id} allowed_window must be an object")
    if window.get("full_history") is True:
        raise ValueError(f"row {row_id} requested full_history")

    start = _parse_iso_date(window.get("start"), label=f"{row_id}.allowed_window.start")
    end = _parse_iso_date(window.get("end"), label=f"{row_id}.allowed_window.end")
    if start > end:
        raise ValueError(f"row {row_id} allowed_window.start must be <= end")

    if granularity == "daily":
        loader_name = "load_daily_data"
        warmup_days = int(request.get("max_daily_warmup_trading_days", 20))
        warmup_policy = "max_daily_warmup_trading_days"
        raw_loader_scope = "date_only_daily_cache"
    elif granularity == "minute":
        loader_name = "query_minute_data"
        warmup_days = int(request.get("max_minute_warmup_session_days", 1))
        warmup_policy = "max_minute_warmup_session_days"
        raw_loader_scope = "symbol_date_minute_bars"
    else:
        raise ValueError(f"row {row_id} market_granularity must be daily or minute")

    query_start = _date_minus_days(start.isoformat(), warmup_days)
    query_end = end.isoformat()
    return {
        "loader_name": loader_name,
        "loader_module": str(request.get("loader_import_module", ALLOWED_LOADER_MODULE)),
        "symbols": [symbol],
        "effective_symbols": [symbol],
        "raw_loader_scope": raw_loader_scope,
        "date_window_start": query_start,
        "date_window_end": query_end,
        "granularity": granularity,
        "warmup_policy": {
            "name": warmup_policy,
            "max_days": warmup_days,
            "no_forward_expansion": True,
        },
        "warmup_days_used": warmup_days,
        "raw_to_effective_filter_proof": {
            "raw_loader_scope": raw_loader_scope,
            "effective_symbols": [symbol],
            "filter_before_strategy": True,
        },
        "derivation_proof": [
            {
                "row_id": row_id,
                "row_kind": row.get("row_kind"),
                "source_symbol": symbol,
                "source_allowed_window": window,
                "query_start_rule": f"allowed_window.start minus <= {warmup_days} bounded warmup day(s)",
                "query_end_rule": "allowed_window.end with no forward expansion",
            }
        ],
    }


def _query_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("loader_name"),
        record.get("granularity"),
        tuple(record.get("symbols", [])),
        record.get("date_window_start"),
        record.get("date_window_end"),
    )


def build_query_plan(
    manifest: dict[str, Any],
    request: dict[str, Any],
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Build the normalized manifest-derived query union."""

    manifest_path = manifest_path or repo_path(PHASE5_MANIFEST_REL)
    manifest_sha = sha256_path(manifest_path)
    executable_rows = _executable_rows(manifest)
    if len(executable_rows) > int(request.get("max_executable_rows", 25)):
        raise ValueError("max_executable_rows_exceeded")

    by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in executable_rows:
        base = _query_base_for_row(row, request)
        key = _query_key(base)
        if key not in by_key:
            by_key[key] = {
                **base,
                "row_ids": [],
                "derived_from_manifest_path": repo_rel(manifest_path),
                "derived_from_manifest_sha256": manifest_sha,
                "executed": False,
                "loader_status": "skipped_fail_closed",
            }
        by_key[key]["row_ids"].append(str(row.get("row_id")))
        if key in by_key and base["derivation_proof"]:
            known_ids = {item["row_id"] for item in by_key[key]["derivation_proof"]}
            for proof in base["derivation_proof"]:
                if proof["row_id"] not in known_ids:
                    by_key[key]["derivation_proof"].append(proof)

    records = list(by_key.values())
    records.sort(key=lambda item: (item["loader_name"], item["granularity"], item["date_window_start"], item["date_window_end"], item["symbols"]))
    for index, record in enumerate(records, start=1):
        symbol_slug = "-".join(str(symbol).lower() for symbol in record["symbols"])
        record["query_id"] = f"p5-1-q{index:03d}-{record['granularity']}-{symbol_slug}"
        record["row_ids"] = sorted(record["row_ids"])
        record["derivation_proof"] = sorted(record["derivation_proof"], key=lambda item: item["row_id"])

    return {
        "schema_version": QUERY_LEDGER_SCHEMA_VERSION,
        "run_id": request.get("run_id"),
        "derived_from_manifest_path": repo_rel(manifest_path),
        "derived_from_manifest_sha256": manifest_sha,
        "request_execution_mode": request.get("allowed_execution_mode"),
        "query_count": len(records),
        "records": records,
    }


def validate_query_ledger(
    query_ledger: dict[str, Any],
    manifest: dict[str, Any],
    request: dict[str, Any],
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Verify a query ledger equals the normalized executable-row union."""

    errors: list[str] = []
    if query_ledger.get("schema_version") != QUERY_LEDGER_SCHEMA_VERSION:
        errors.append(f"schema_version must be {QUERY_LEDGER_SCHEMA_VERSION}")

    records = query_ledger.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list")
        records = []

    executable_row_ids = {str(row.get("row_id")) for row in _executable_rows(manifest)}
    audit_row_ids = {str(row.get("row_id")) for row in _audit_rows(manifest)}
    manifest_symbols_by_row = {
        str(row.get("row_id")): str(row.get("symbol")) for row in _executable_rows(manifest)
    }

    try:
        expected = build_query_plan(manifest, request, manifest_path)
    except ValueError as exc:
        return {"passed": False, "errors": [f"manifest_query_derivation_failed: {exc}"]}

    expected_map = {
        _query_key(record): set(record.get("row_ids", []))
        for record in expected.get("records", [])
    }
    actual_map = {
        _query_key(record): set(str(row_id) for row_id in record.get("row_ids", []))
        for record in records
        if isinstance(record, dict)
    }
    if actual_map != expected_map:
        errors.append("query_ledger_not_manifest_derived_union")

    for record in records:
        if not isinstance(record, dict):
            errors.append("query record must be an object")
            continue
        row_ids = [str(row_id) for row_id in record.get("row_ids", [])]
        if not row_ids:
            errors.append(f"{record.get('query_id')} row_ids must be non-empty")
        forbidden_audit = sorted(set(row_ids) & audit_row_ids)
        if forbidden_audit:
            errors.append(f"audit_rows_execute_forbidden: {', '.join(forbidden_audit)}")
        unknown_rows = sorted(set(row_ids) - executable_row_ids)
        if unknown_rows:
            errors.append(f"unknown_query_row_ids: {', '.join(unknown_rows)}")

        symbols = [str(symbol) for symbol in record.get("symbols", [])]
        effective_symbols = [str(symbol) for symbol in record.get("effective_symbols", [])]
        expected_symbols = sorted({manifest_symbols_by_row[row_id] for row_id in row_ids if row_id in manifest_symbols_by_row})
        if sorted(symbols) != expected_symbols:
            errors.append(f"extra_or_missing_query_symbols: {record.get('query_id')}")
        if sorted(effective_symbols) != expected_symbols:
            errors.append(f"extra_or_missing_effective_symbols: {record.get('query_id')}")
        if record.get("granularity") == "daily" and record.get("raw_loader_scope") != "date_only_daily_cache":
            errors.append(f"daily_raw_loader_scope_required: {record.get('query_id')}")
        if record.get("granularity") == "minute" and record.get("raw_loader_scope") != "symbol_date_minute_bars":
            errors.append(f"minute_raw_loader_scope_required: {record.get('query_id')}")
        if record.get("date_window_start") is None or record.get("date_window_end") is None:
            errors.append(f"date_window_required: {record.get('query_id')}")
        if record.get("full_history") is True or record.get("dynamic_universe") is True:
            errors.append(f"forbidden_full_history_or_dynamic_universe: {record.get('query_id')}")

    return {"passed": not errors, "errors": errors}


def _import_default_loaders(request: dict[str, Any]) -> Any:
    module_name = str(request.get("loader_import_module", ALLOWED_LOADER_MODULE))
    return importlib.import_module(module_name)


def _import_default_strategy_cls() -> Any:
    module = importlib.import_module("strategies.active_strategy")
    return module.TradingStrategy


def _frame_symbols(frame: Any) -> list[str]:
    if frame is None or getattr(frame, "empty", False):
        return []
    if "ticker" not in getattr(frame, "columns", []):
        return []
    return sorted({str(value) for value in frame["ticker"].dropna().astype(str).tolist()})


def _filter_frame_to_symbols(frame: Any, symbols: list[str]) -> Any:
    if frame is None or getattr(frame, "empty", False):
        return frame
    if "ticker" not in getattr(frame, "columns", []):
        return frame.iloc[0:0].copy()
    return frame.loc[frame["ticker"].astype(str).isin(set(symbols))].copy()


def _frames_by_symbol(frame: Any, symbols: list[str]) -> dict[str, Any]:
    grouped: dict[str, Any] = {}
    if frame is None or getattr(frame, "empty", False) or "ticker" not in getattr(frame, "columns", []):
        return grouped
    for symbol in symbols:
        symbol_frame = frame.loc[frame["ticker"].astype(str) == symbol].copy()
        if not symbol_frame.empty:
            grouped[symbol] = symbol_frame.reset_index(drop=True)
    return grouped


def _series_has_direction(series: Any, direction: str) -> bool:
    if series is None:
        return False
    values: Iterable[Any]
    if hasattr(series, "dropna"):
        values = series.dropna().tolist()
    elif isinstance(series, dict):
        values = series.values()
    else:
        try:
            values = list(series)
        except TypeError:
            values = [series]
    for value in values:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if direction == "long" and numeric > 0:
            return True
        if direction == "short" and numeric < 0:
            return True
    return False


def _signals_by_symbol(signals: Any, symbols: list[str], direction: str) -> dict[str, bool]:
    if isinstance(signals, dict):
        return {symbol: _series_has_direction(signals.get(symbol), direction) for symbol in symbols}
    if len(symbols) == 1:
        return {symbols[0]: _series_has_direction(signals, direction)}
    return {symbol: False for symbol in symbols}


def _trace_signal_by_symbol(trace: Any, symbols: list[str], direction: str) -> dict[str, bool]:
    result = {symbol: False for symbol in symbols}
    if not isinstance(trace, dict):
        return result
    for signal in _as_list(trace.get("signals")):
        if not isinstance(signal, dict):
            continue
        symbol = str(signal.get("symbol"))
        if symbol in result and str(signal.get("direction")) == direction:
            result[symbol] = True
    return result


def _merge_signal_maps(primary: dict[str, bool], secondary: dict[str, bool]) -> dict[str, bool]:
    symbols = set(primary) | set(secondary)
    return {symbol: bool(primary.get(symbol) or secondary.get(symbol)) for symbol in symbols}


def _execute_strategy(strategy_cls: Any, frames: dict[str, Any], direction: str) -> dict[str, bool]:
    strategy = strategy_cls()
    signals = strategy.generate_signals(frames)
    trace = strategy.get_signal_trace() if hasattr(strategy, "get_signal_trace") else {}
    series_map = _signals_by_symbol(signals, list(frames), direction)
    trace_map = _trace_signal_by_symbol(trace, list(frames), direction)
    return _merge_signal_maps(series_map, trace_map)


def execute_query_ledger(
    query_ledger: dict[str, Any],
    manifest: dict[str, Any],
    request: dict[str, Any],
    *,
    loaders: Any | None = None,
    strategy_cls: Any | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str], int]:
    """Execute approved loaders for a valid query ledger.

    Returns updated ledger, row-id query outcomes, fail-closed errors, and loader
    call count.
    """

    loaders = loaders if loaders is not None else _import_default_loaders(request)
    strategy_cls = strategy_cls if strategy_cls is not None else _import_default_strategy_cls()
    row_by_id = {str(row.get("row_id")): row for row in _executable_rows(manifest)}
    row_outcomes: dict[str, dict[str, Any]] = {}
    fail_closed_errors: list[str] = []
    loader_call_count = 0

    for record in query_ledger.get("records", []):
        if not isinstance(record, dict):
            continue
        symbols = [str(symbol) for symbol in record.get("effective_symbols", [])]
        row_ids = [str(row_id) for row_id in record.get("row_ids", [])]
        granularity = str(record.get("granularity"))
        loader_name = str(record.get("loader_name"))
        start = str(record.get("date_window_start"))
        end = str(record.get("date_window_end"))
        direction = str(row_by_id.get(row_ids[0], {}).get("direction", "long")) if row_ids else "long"

        record["executed"] = True
        loader_call_count += 1
        try:
            if loader_name == "load_daily_data" and granularity == "daily":
                raw_frame = loaders.load_daily_data(start_date=start, end_date=end)
                raw_symbols = _frame_symbols(raw_frame)
                filtered = _filter_frame_to_symbols(raw_frame, symbols)
                strategy_input_symbols = _frame_symbols(filtered)
                filtered_out_symbols = sorted(set(raw_symbols) - set(strategy_input_symbols))
                proof = dict(record.get("raw_to_effective_filter_proof", {}))
                proof.update(
                    {
                        "raw_symbol_count": len(raw_symbols),
                        "raw_symbol_sample": raw_symbols[:10],
                        "filtered_out_symbol_count": len(filtered_out_symbols),
                        "filtered_out_symbol_sample": filtered_out_symbols[:10],
                        "strategy_input_symbols": strategy_input_symbols,
                    }
                )
                record["raw_to_effective_filter_proof"] = proof
                if sorted(strategy_input_symbols) != sorted(symbols):
                    record["loader_status"] = "data_missing"
                    record["data_missing_reason"] = "daily loader returned no bars for effective manifest symbols"
                    signal_map = {symbol: False for symbol in symbols}
                else:
                    frames = _frames_by_symbol(filtered, symbols)
                    signal_map = _execute_strategy(strategy_cls, frames, direction)
                    record["loader_status"] = "executed"
                    record["data_missing_reason"] = None
            elif loader_name == "query_minute_data" and granularity == "minute":
                minute_frames = loaders.query_minute_data(symbols, start, end)
                if not isinstance(minute_frames, dict):
                    minute_frames = {}
                returned_symbols = sorted(str(symbol) for symbol in minute_frames)
                extra_symbols = sorted(set(returned_symbols) - set(symbols))
                if extra_symbols:
                    raise ValueError(
                        "minute_loader_returned_extra_symbols: " + ", ".join(extra_symbols)
                    )
                frames = {
                    symbol: frame
                    for symbol, frame in minute_frames.items()
                    if str(symbol) in set(symbols) and not getattr(frame, "empty", False)
                }
                proof = dict(record.get("raw_to_effective_filter_proof", {}))
                proof.update(
                    {
                        "raw_symbol_count": len(returned_symbols),
                        "raw_symbol_sample": returned_symbols[:10],
                        "filtered_out_symbol_count": 0,
                        "filtered_out_symbol_sample": [],
                        "strategy_input_symbols": sorted(str(symbol) for symbol in frames),
                    }
                )
                record["raw_to_effective_filter_proof"] = proof
                missing = sorted(set(symbols) - set(str(symbol) for symbol in frames))
                if missing:
                    record["loader_status"] = "data_missing"
                    record["data_missing_reason"] = "minute loader returned no bars for: " + ", ".join(missing)
                    signal_map = {symbol: False for symbol in symbols}
                else:
                    signal_map = _execute_strategy(strategy_cls, frames, direction)
                    record["loader_status"] = "executed"
                    record["data_missing_reason"] = None
            else:
                raise ValueError(f"unapproved_loader_or_granularity: {loader_name}/{granularity}")
        except Exception as exc:  # noqa: BLE001 - fail closed with explicit reason.
            message = f"{record.get('query_id')} loader_or_strategy_error: {exc}"
            if loader_name in ALLOWED_LOADERS:
                record["loader_status"] = "data_missing"
                record["data_missing_reason"] = message
                signal_map = {symbol: False for symbol in symbols}
            else:
                record["loader_status"] = "skipped_fail_closed"
                record["data_missing_reason"] = message
                fail_closed_errors.append(message)
                signal_map = {symbol: False for symbol in symbols}

        record["signals_by_symbol"] = signal_map
        for row_id in row_ids:
            row = row_by_id.get(row_id, {})
            symbol = str(row.get("symbol"))
            row_outcomes[row_id] = {
                "query_id": record.get("query_id"),
                "loader_status": record.get("loader_status"),
                "data_missing_reason": record.get("data_missing_reason"),
                "signal_present": bool(signal_map.get(symbol)),
            }

    return query_ledger, row_outcomes, fail_closed_errors, loader_call_count


def _control_interpretation_blocked(row: dict[str, Any]) -> bool:
    missing_fields = _as_list(row.get("missing_fields"))
    return bool(row.get("control_interpretation_blocked")) or _contains_fragment(
        missing_fields,
        "cannot interpret",
    )


def _executable_row_result(row: dict[str, Any], query_outcome: dict[str, Any] | None) -> dict[str, Any]:
    query_outcome = query_outcome or {}
    row_kind = str(row.get("row_kind"))
    signal_present = bool(query_outcome.get("signal_present"))
    loader_status = str(query_outcome.get("loader_status") or "skipped_fail_closed")
    data_missing_reason = query_outcome.get("data_missing_reason")

    control_outcome: str | None = None
    if loader_status == "data_missing":
        final_status = "data_missing"
        reason = str(data_missing_reason or "required bounded replay data unavailable")
        if row_kind in CONTROL_ROW_KINDS:
            control_outcome = "data_missing"
    elif row_kind == PUBLIC_ROW_KIND:
        missing_fields = _as_list(row.get("missing_fields"))
        expected_status = str(row.get("expected_status"))
        if missing_fields or expected_status == "insufficient_evidence":
            final_status = "insufficient_evidence"
            reason = "public evidence gap remains explicit; no date/fill/account fields were invented"
        elif signal_present:
            final_status = "reproduced"
            reason = "bounded replay emitted a matching primitive signal; realized outcomes remain N/A"
        else:
            final_status = "not_reproduced"
            reason = "bounded replay data was available but no matching primitive signal appeared"
    elif row_kind in CONTROL_ROW_KINDS:
        if _control_interpretation_blocked(row):
            control_outcome = "insufficient_evidence"
            final_status = CONTROL_OUTCOME_TO_FINAL_STATUS[control_outcome]
            reason = "control row cannot be interpreted without violating public-evidence constraints"
        elif signal_present:
            control_outcome = "false_positive_control"
            final_status = CONTROL_OUTCOME_TO_FINAL_STATUS[control_outcome]
            reason = "matching primitive signal appeared in a diagnostic control window; not promotion evidence"
        else:
            control_outcome = "clean_control"
            final_status = CONTROL_OUTCOME_TO_FINAL_STATUS[control_outcome]
            reason = "no matching primitive signal appeared in the diagnostic control window"
    else:
        final_status = "insufficient_evidence"
        reason = "row kind is not executable for Phase 5.1"

    result = {
        "row_id": row.get("row_id"),
        "row_kind": row.get("row_kind"),
        "case_id": row.get("case_id"),
        "parent_case_id": row.get("parent_case_id"),
        "symbol": row.get("symbol"),
        "direction": row.get("direction"),
        "market_granularity": row.get("market_granularity"),
        "allowed_window": row.get("allowed_window"),
        "evidence_class": row.get("evidence_class"),
        "final_status": final_status,
        "control_outcome": control_outcome,
        "query_id": query_outcome.get("query_id"),
        "loader_status": loader_status,
        "signal_present": signal_present,
        "missing_fields": row.get("missing_fields", []),
        "realized_outcome": realized_outcome_na(),
        "reason": reason,
    }
    if control_outcome is None:
        result.pop("control_outcome")
    return result


def _audit_result(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row.get("row_id"),
        "row_kind": row.get("row_kind"),
        "case_id": row.get("case_id"),
        "symbol": row.get("symbol"),
        "direction": row.get("direction"),
        "evidence_class": row.get("evidence_class"),
        "final_status": "insufficient_evidence",
        "market_data_query_allowed": False,
        "missing_fields": row.get("missing_fields", []),
        "realized_outcome": realized_outcome_na(),
        "reason": row.get(
            "reason",
            "audit-only public evidence row; not eligible for Phase 5.1 loader planning",
        ),
    }


def build_report(
    manifest: dict[str, Any],
    request: dict[str, Any],
    query_ledger: dict[str, Any] | None,
    row_query_outcomes: dict[str, dict[str, Any]],
    *,
    manifest_sha256: str,
    request_path: Path,
    query_ledger_path: Path,
    runtime_path: Path,
    request_sha256: str,
    query_ledger_sha256: str | None,
    runtime_sha256: str | None,
    validation: dict[str, Any],
) -> dict[str, Any]:
    executable_results = [
        _executable_row_result(row, row_query_outcomes.get(str(row.get("row_id"))))
        for row in _executable_rows(manifest)
    ]
    public_results = [row for row in executable_results if row.get("row_kind") == PUBLIC_ROW_KIND]
    control_results = [row for row in executable_results if row.get("row_kind") in CONTROL_ROW_KINDS]
    audit_results = [_audit_result(row) for row in _audit_rows(manifest)]

    public_status_counts = Counter(str(row.get("final_status")) for row in public_results)
    control_status_counts = Counter(str(row.get("final_status")) for row in control_results)
    control_outcome_counts = Counter(str(row.get("control_outcome")) for row in control_results)
    false_positive_control_row_ids = sorted(
        str(row.get("row_id"))
        for row in control_results
        if row.get("control_outcome") == "false_positive_control"
    )
    reproduced_public_count = int(public_status_counts.get("reproduced", 0))
    promotion_threshold = int(manifest.get("run_level_gate", {}).get("required_public_reproduced", 5))
    diagnostic_veto_reasons = (
        ["false_positive_controls_present"] if false_positive_control_row_ids else []
    )
    diagnostic_promotion_veto = {
        "active": bool(diagnostic_veto_reasons),
        "false_positive_control_count": len(false_positive_control_row_ids),
        "false_positive_control_row_ids": false_positive_control_row_ids,
        "controls_counted_toward_promotion": 0,
        "reasons": diagnostic_veto_reasons,
    }
    promoted = (
        bool(validation.get("passed"))
        and reproduced_public_count >= promotion_threshold
        and not diagnostic_promotion_veto["active"]
    )
    overall_status = FAILED_RUN_STATUS if not validation.get("passed") else PROMOTED_RUN_STATUS if promoted else RESEARCH_ONLY_RUN_STATUS

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": request.get("run_id"),
        "execution_mode": ALLOWED_EXECUTION_MODE,
        "overall_run_status": overall_status,
        "promoted": promoted,
        "diagnostic_promotion_veto": diagnostic_promotion_veto,
        "promotion_evaluation": {
            "promoted": promoted,
            "required_public_reproduced": promotion_threshold,
            "reproduced_public_replay_candidate_count": reproduced_public_count,
            "public_replay_candidate_threshold_met": reproduced_public_count >= promotion_threshold,
            "counted_row_kind": PUBLIC_ROW_KIND,
            "controls_counted_toward_promotion": 0,
            "false_positive_control_count": len(false_positive_control_row_ids),
            "false_positive_control_row_ids": false_positive_control_row_ids,
            "diagnostic_veto_reasons": diagnostic_veto_reasons,
            "non_diagnostic_blockers": [
                reason
                for condition, reason in (
                    (
                        reproduced_public_count < promotion_threshold,
                        "public_replay_candidate_reproduction_below_threshold",
                    ),
                    (not validation.get("passed"), "bounded_replay_validation_failed"),
                )
                if condition
            ],
        },
        "promotion_threshold": promotion_threshold,
        "reproduced_public_replay_candidate_count": reproduced_public_count,
        "controls_counted_toward_promotion": 0,
        "phase5_manifest_path": PHASE5_MANIFEST_REL,
        "phase5_manifest_sha256": manifest_sha256,
        "replay_request_path": repo_rel(request_path),
        "replay_request_sha256": request_sha256,
        "query_ledger_path": repo_rel(query_ledger_path),
        "query_ledger_sha256": query_ledger_sha256,
        "runtime_path": repo_rel(runtime_path),
        "runtime_sha256": runtime_sha256,
        "runner_path": RUNNER_REL,
        "data_source_metadata": {
            "loader_file_path": request.get("loader_file_path"),
            "loader_import_module": request.get("loader_import_module"),
            "allowed_loaders": request.get("allowed_loaders"),
            "query_ledger_record_count": len(query_ledger.get("records", [])) if isinstance(query_ledger, dict) else 0,
        },
        "public_replay_candidate_summary": {
            "public_replay_candidate_count": len(public_results),
            "status_counts": dict(sorted(public_status_counts.items())),
        },
        "control_summary": {
            "control_row_count": len(control_results),
            "clean_control_count": int(control_outcome_counts.get("clean_control", 0)),
            "false_positive_control_count": int(control_outcome_counts.get("false_positive_control", 0)),
            "false_positive_control_row_ids": false_positive_control_row_ids,
            "control_data_missing_count": int(control_outcome_counts.get("data_missing", 0)),
            "control_insufficient_evidence_count": int(control_outcome_counts.get("insufficient_evidence", 0)),
            "status_counts": dict(sorted(control_status_counts.items())),
            "controls_counted_toward_promotion": 0,
        },
        "audit_only_summary": {
            "audit_row_count": len(audit_results),
            "status_counts": dict(sorted(Counter(row["final_status"] for row in audit_results).items())),
            "market_data_query_allowed": False,
            "market_data_query_policy": "audit_only_rows_do_not_execute_loaders",
        },
        "row_results": executable_results,
        "audit_results": audit_results,
        "realized_outcome_fields": realized_outcome_na(),
        "realized_outcome_policy": realized_outcome_policy(),
        "phase5_2_artifact_note": (
            "Phase 5.2 report artifacts add diagnostic promotion-veto fields only; "
            "they do not broaden replay scope, query audit rows, or upgrade realized outcomes."
        ),
        "no_overclaim_statement": NO_OVERCLAIM_STATEMENT,
        "diagnostic_promotion_veto": diagnostic_promotion_veto,
        "validation": validation,
    }


def build_runtime(
    request: dict[str, Any],
    *,
    manifest_sha256: str | None,
    request_sha256: str,
    query_ledger_sha256: str | None,
    started_at: str,
    completed_at: str,
    fail_closed: bool,
    fail_closed_reason: str | None,
    loader_call_count: int,
) -> dict[str, Any]:
    runtime = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "run_id": request.get("run_id"),
        "phase5_manifest_sha256": manifest_sha256,
        "replay_request_sha256": request_sha256,
        "query_ledger_sha256": query_ledger_sha256,
        "runner_path": RUNNER_REL,
        "started_at": started_at,
        "completed_at": completed_at,
        "fail_closed": fail_closed,
        "fail_closed_reason": fail_closed_reason,
        "loader_call_count": loader_call_count,
    }
    runtime["runtime_sha256"] = stable_json_sha256(runtime)
    return runtime


def render_markdown_report(report: dict[str, Any]) -> str:
    veto = report.get("diagnostic_promotion_veto", {})
    control_summary = report.get("control_summary", {})
    lines = [
        "# MartinLuk Phase 5.2 Bounded Replay Report",
        "",
        f"Run ID: `{report.get('run_id')}`",
        f"Overall run status: `{report.get('overall_run_status')}`",
        f"Promoted: `{str(report.get('promoted')).lower()}`",
        "",
        "## No-overclaim boundary",
        "",
        str(report.get("no_overclaim_statement")),
        "",
        "## Hash chain",
        "",
        f"- Phase 5 manifest SHA-256: `{report.get('phase5_manifest_sha256')}`",
        f"- Replay request SHA-256: `{report.get('replay_request_sha256')}`",
        f"- Query ledger SHA-256: `{report.get('query_ledger_sha256')}`",
        f"- Runtime SHA-256: `{report.get('runtime_sha256')}`",
        "",
        "## Public replay candidates",
        "",
        f"- Required reproduced public replay candidates: `{report.get('promotion_threshold')}`",
        "- Reproduced public replay candidates: "
        f"`{report.get('reproduced_public_replay_candidate_count')}`",
        "- Public status counts: "
        f"`{json.dumps(report.get('public_replay_candidate_summary', {}).get('status_counts', {}), sort_keys=True)}`",
        "",
        "## Diagnostic controls",
        "",
        f"- Control rows: `{report.get('control_summary', {}).get('control_row_count')}`",
        f"- Clean controls: `{report.get('control_summary', {}).get('clean_control_count')}`",
        f"- False-positive controls: `{report.get('control_summary', {}).get('false_positive_control_count')}`",
        "- False-positive control row IDs: "
        f"`{json.dumps(control_summary.get('false_positive_control_row_ids', []), sort_keys=True)}`",
        f"- Controls counted toward promotion: `{control_summary.get('controls_counted_toward_promotion')}`",
        "",
        "## Diagnostic promotion veto",
        "",
        f"- Active: `{str(veto.get('active')).lower()}`",
        f"- Reasons: `{json.dumps(veto.get('reasons', []), sort_keys=True)}`",
        f"- False-positive control count: `{veto.get('false_positive_control_count')}`",
        "- False-positive control row IDs: "
        f"`{json.dumps(veto.get('false_positive_control_row_ids', []), sort_keys=True)}`",
        "",
        "## Audit-only rows",
        "",
        f"- Audit rows: `{report.get('audit_only_summary', {}).get('audit_row_count')}`",
        "- Audit rows execute loaders: `false`",
        "",
        "## Realized outcomes",
        "",
        "Realized entry, exit, position size, account P&L, fees, and slippage are `N/A` for every row.",
        "",
        "## Phase 5.2 artifact note",
        "",
        str(report.get("phase5_2_artifact_note")),
        "",
    ]
    return "\n".join(lines)


def _fail_closed_result(
    request: dict[str, Any],
    request_path: Path,
    runtime_path: Path,
    output_json_path: Path,
    output_md_path: Path,
    *,
    started_at: str,
    request_sha256: str,
    errors: list[str],
    manifest_sha256: str | None = None,
) -> dict[str, Any]:
    completed_at = utc_now()
    runtime = build_runtime(
        request,
        manifest_sha256=manifest_sha256,
        request_sha256=request_sha256,
        query_ledger_sha256=None,
        started_at=started_at,
        completed_at=completed_at,
        fail_closed=True,
        fail_closed_reason="; ".join(errors),
        loader_call_count=0,
    )
    if _is_allowed_phase5_1_output(runtime_path):
        write_json(runtime_path, runtime)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": request.get("run_id"),
        "execution_mode": ALLOWED_EXECUTION_MODE,
        "overall_run_status": FAILED_RUN_STATUS,
        "promoted": False,
        "diagnostic_promotion_veto": {
            "active": False,
            "reasons": [],
            "false_positive_control_count": 0,
            "false_positive_control_row_ids": [],
        },
        "promotion_evaluation": {
            "promoted": False,
            "required_public_reproduced": None,
            "reproduced_public_replay_candidate_count": 0,
            "public_replay_candidate_threshold_met": False,
            "counted_row_kind": PUBLIC_ROW_KIND,
            "controls_counted_toward_promotion": 0,
            "false_positive_control_count": 0,
            "false_positive_control_row_ids": [],
            "diagnostic_veto_reasons": [],
            "non_diagnostic_blockers": ["bounded_replay_validation_failed"],
        },
        "control_summary": {
            "control_row_count": 0,
            "clean_control_count": 0,
            "false_positive_control_count": 0,
            "false_positive_control_row_ids": [],
            "control_data_missing_count": 0,
            "control_insufficient_evidence_count": 0,
            "status_counts": {},
            "controls_counted_toward_promotion": 0,
        },
        "audit_only_summary": {
            "audit_row_count": 0,
            "status_counts": {},
            "market_data_query_allowed": False,
            "market_data_query_policy": "audit_only_rows_do_not_execute_loaders",
        },
        "phase5_manifest_path": request.get("phase5_manifest_path"),
        "phase5_manifest_sha256": manifest_sha256,
        "replay_request_path": repo_rel(request_path),
        "replay_request_sha256": request_sha256,
        "query_ledger_path": None,
        "query_ledger_sha256": None,
        "runtime_path": repo_rel(runtime_path),
        "runtime_sha256": runtime["runtime_sha256"],
        "runner_path": RUNNER_REL,
        "row_results": [],
        "audit_results": [],
        "realized_outcome_fields": realized_outcome_na(),
        "realized_outcome_policy": realized_outcome_policy(),
        "phase5_2_artifact_note": (
            "Phase 5.2 report artifacts add diagnostic promotion-veto fields only; "
            "they do not broaden replay scope, query audit rows, or upgrade realized outcomes."
        ),
        "no_overclaim_statement": NO_OVERCLAIM_STATEMENT,
        "validation": {"passed": False, "errors": errors},
    }
    if _is_allowed_phase5_1_output(output_json_path):
        write_json(output_json_path, report)
    if _is_allowed_phase5_1_output(output_md_path):
        output_md_path.write_text(render_markdown_report(report))
    return {"ok": False, "errors": errors, "runtime": runtime, "report": report}


def run_bounded_replay(
    *,
    request_path: Path,
    query_ledger_path: Path,
    runtime_path: Path,
    output_json_path: Path,
    output_md_path: Path,
    loaders: Any | None = None,
    strategy_cls: Any | None = None,
) -> dict[str, Any]:
    started_at = utc_now()
    request_path = repo_path(request_path)
    query_ledger_path = repo_path(query_ledger_path)
    runtime_path = repo_path(runtime_path)
    output_json_path = repo_path(output_json_path)
    output_md_path = repo_path(output_md_path)

    request = load_json(request_path)
    request_sha256 = sha256_path(request_path)
    output_errors = _protected_output_errors(
        [query_ledger_path, runtime_path, output_json_path, output_md_path]
    )
    if output_errors:
        return _fail_closed_result(
            request,
            request_path,
            runtime_path,
            output_json_path,
            output_md_path,
            started_at=started_at,
            request_sha256=request_sha256,
            errors=output_errors,
        )

    request_validation = validate_replay_request(request)
    if not request_validation["passed"]:
        return _fail_closed_result(
            request,
            request_path,
            runtime_path,
            output_json_path,
            output_md_path,
            started_at=started_at,
            request_sha256=request_sha256,
            errors=request_validation["errors"],
            manifest_sha256=request_validation.get("phase5_manifest_sha256"),
        )

    manifest_path = repo_path(str(request["phase5_manifest_path"]))
    manifest_sha256 = sha256_path(manifest_path)
    manifest = load_json(manifest_path)

    try:
        query_ledger = build_query_plan(manifest, request, manifest_path)
    except ValueError as exc:
        return _fail_closed_result(
            request,
            request_path,
            runtime_path,
            output_json_path,
            output_md_path,
            started_at=started_at,
            request_sha256=request_sha256,
            errors=[f"query_planning_failed: {exc}"],
            manifest_sha256=manifest_sha256,
        )

    query_validation = validate_query_ledger(query_ledger, manifest, request, manifest_path)
    if not query_validation["passed"]:
        return _fail_closed_result(
            request,
            request_path,
            runtime_path,
            output_json_path,
            output_md_path,
            started_at=started_at,
            request_sha256=request_sha256,
            errors=query_validation["errors"],
            manifest_sha256=manifest_sha256,
        )

    query_ledger, row_query_outcomes, execution_errors, loader_call_count = execute_query_ledger(
        query_ledger,
        manifest,
        request,
        loaders=loaders,
        strategy_cls=strategy_cls,
    )
    validation = {
        "passed": not execution_errors,
        "request": request_validation,
        "query_ledger": query_validation,
        "errors": execution_errors,
    }
    write_json(query_ledger_path, query_ledger)
    query_ledger_sha256 = sha256_path(query_ledger_path)

    completed_at = utc_now()
    runtime = build_runtime(
        request,
        manifest_sha256=manifest_sha256,
        request_sha256=request_sha256,
        query_ledger_sha256=query_ledger_sha256,
        started_at=started_at,
        completed_at=completed_at,
        fail_closed=bool(execution_errors),
        fail_closed_reason="; ".join(execution_errors) if execution_errors else None,
        loader_call_count=loader_call_count,
    )
    write_json(runtime_path, runtime)

    report = build_report(
        manifest,
        request,
        query_ledger,
        row_query_outcomes,
        manifest_sha256=manifest_sha256,
        request_path=request_path,
        query_ledger_path=query_ledger_path,
        runtime_path=runtime_path,
        request_sha256=request_sha256,
        query_ledger_sha256=query_ledger_sha256,
        runtime_sha256=runtime["runtime_sha256"],
        validation=validation,
    )
    write_json(output_json_path, report)
    output_md_path.write_text(render_markdown_report(report))
    return {
        "ok": validation["passed"],
        "errors": execution_errors,
        "query_ledger": query_ledger,
        "runtime": runtime,
        "report": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=repo_path(REQUEST_REL))
    parser.add_argument("--query-ledger", type=Path, default=repo_path(QUERY_LEDGER_REL))
    parser.add_argument("--runtime", type=Path, default=repo_path(RUNTIME_REL))
    parser.add_argument("--output-json", type=Path, default=repo_path(REPORT_JSON_REL))
    parser.add_argument("--output-md", type=Path, default=repo_path(REPORT_MD_REL))
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate the request contract without query planning or loader calls",
    )
    args = parser.parse_args()

    if args.check_only:
        request = load_json(repo_path(args.request))
        payload = validate_replay_request(request)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["passed"] else 1

    result = run_bounded_replay(
        request_path=args.request,
        query_ledger_path=args.query_ledger,
        runtime_path=args.runtime,
        output_json_path=args.output_json,
        output_md_path=args.output_md,
    )
    print(json.dumps({"ok": result["ok"], "errors": result["errors"]}, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
