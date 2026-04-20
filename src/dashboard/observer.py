from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_PATH = Path("experiments/autoresearch_state.json")
ITERATION_ROOT = Path("experiments/iterations")
RESULTS_PATH = Path("experiments/results.tsv")
ITERATION_DIR_PATTERN = re.compile(r"^iteration-(?P<number>\d+)$")


def observe_dashboard_state(
    repo_root: str | Path,
    *,
    now: datetime | None = None,
    stale_after_seconds: int = 600,
) -> dict[str, Any]:
    """Read repo-local autoresearch artifacts into a normalized dashboard state."""
    root = Path(repo_root).expanduser().resolve()
    observed_at = _normalize_datetime(now or datetime.now(timezone.utc))
    state_path = root / STATE_PATH
    iteration_root = root / ITERATION_ROOT
    results_path = root / RESULTS_PATH

    raw_state = _read_json(state_path)
    has_run_state = isinstance(raw_state, dict)
    state = raw_state
    if not has_run_state:
        state = {}

    run_root = _resolve_run_root(iteration_root, state.get("run_id"), allow_latest=has_run_state)
    ledger = _read_results_ledger(results_path)
    iterations = _collect_iterations(root, run_root, ledger["rows"])
    heartbeat = _latest_heartbeat(run_root, state_path, state, observed_at)
    run = _normalize_run(state, heartbeat, observed_at, stale_after_seconds)

    return {
        "observed_at": observed_at.isoformat(),
        "run": run,
        "iterations": iterations,
        "ledger": ledger,
        "sources": {
            "state": _source_status(state_path),
            "iteration_root": _source_status(iteration_root),
            "active_run_root": _source_status(run_root) if run_root is not None else None,
            "results": _source_status(results_path),
        },
    }


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _read_json(path: Path) -> Any:
    if not path.exists() or not path.is_file():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _source_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
    }


def _resolve_run_root(iteration_root: Path, run_id: Any, *, allow_latest: bool = True) -> Path | None:
    if isinstance(run_id, str) and run_id:
        return iteration_root / run_id

    if not allow_latest or not iteration_root.exists():
        return None

    run_dirs = [path for path in iteration_root.iterdir() if path.is_dir()]
    if not run_dirs:
        return None

    return max(run_dirs, key=lambda path: path.stat().st_mtime)


def _read_results_ledger(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "path": str(path),
            "columns": [],
            "rows": [],
        }

    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = reader.fieldnames or []
        for row in reader:
            rows.append({key: _coerce_scalar(value) for key, value in row.items()})

    return {
        "path": str(path),
        "columns": columns,
        "rows": rows,
    }


def _coerce_scalar(value: Any) -> Any:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        return value

    try:
        numeric = float(value)
    except ValueError:
        return value

    if numeric.is_integer() and "." not in value:
        return int(numeric)
    return numeric


def _collect_iterations(
    repo_root: Path,
    run_root: Path | None,
    ledger_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if run_root is None or not run_root.exists():
        return []

    iteration_dirs = [path for path in run_root.iterdir() if path.is_dir() and _iteration_number(path) is not None]
    iteration_dirs.sort(key=lambda path: _iteration_number(path) or 0)
    ledger_by_iteration = _ledger_rows_by_iteration(iteration_dirs, ledger_rows)

    iterations: list[dict[str, Any]] = []
    for iteration_dir in iteration_dirs:
        iteration_number = _iteration_number(iteration_dir)
        ledger_row = ledger_by_iteration.get(iteration_number, {}) if iteration_number is not None else {}
        iterations.append(_normalize_iteration(repo_root, iteration_dir, ledger_row))

    best_iteration = _best_iteration(iterations)
    for index, iteration in enumerate(iterations):
        previous = iterations[index - 1] if index > 0 else None
        iteration["analysis"] = _iteration_analysis(iteration, previous)
        iteration["metric_breakdown"] = _metric_breakdown(iteration, previous, best_iteration)
    return iterations


def _iteration_number(path: Path) -> int | None:
    match = ITERATION_DIR_PATTERN.match(path.name)
    if not match:
        return None
    return int(match.group("number"))


def _ledger_rows_by_iteration(
    iteration_dirs: list[Path],
    ledger_rows: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    if not ledger_rows:
        return {}

    correlated: dict[int, dict[str, Any]] = {}
    ambiguous: set[int] = set()
    for row in ledger_rows:
        iteration_number = _ledger_iteration_number(row)
        if iteration_number is None:
            continue
        if iteration_number in correlated:
            ambiguous.add(iteration_number)
            continue
        correlated[iteration_number] = row

    for iteration_number in ambiguous:
        correlated.pop(iteration_number, None)
    return correlated


def _ledger_iteration_number(row: dict[str, Any]) -> int | None:
    for key in ("iteration", "iteration_number", "iteration_index", "round", "round_number"):
        iteration_number = _integer_identifier(row.get(key))
        if iteration_number is not None:
            return iteration_number

    for key in ("iteration_dir", "iteration_path", "artifact_iteration_dir", "artifact_path"):
        value = row.get(key)
        if isinstance(value, str):
            match = ITERATION_DIR_PATTERN.search(Path(value).name)
            if match:
                return int(match.group("number"))
    return None


def _integer_identifier(value: Any) -> int | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if stripped.isdigit():
        return int(stripped)
    match = ITERATION_DIR_PATTERN.match(stripped)
    if match:
        return int(match.group("number"))
    return None


def _normalize_iteration(repo_root: Path, iteration_dir: Path, ledger_row: dict[str, Any]) -> dict[str, Any]:
    record_path = iteration_dir / "iteration_record.json"
    decision_path = iteration_dir / "decision.json"
    record = _read_json(record_path)
    if not isinstance(record, dict):
        record = {}
    decision_payload = _read_json(decision_path)
    if not isinstance(decision_payload, dict):
        decision_payload = {}

    decision_value = _decision_value(record, decision_payload)
    decision_reasons = _decision_reasons(record, decision_payload)
    metrics = _iteration_metrics(record, decision_payload, ledger_row)
    logs = _iteration_logs(iteration_dir)

    summary = record.get("summary") if isinstance(record.get("summary"), dict) else {}
    artifact_status = record.get("artifact_status")
    artifact_paths = record.get("artifact_paths") if isinstance(record.get("artifact_paths"), dict) else {}
    artifact_references = _artifact_references(repo_root, iteration_dir, artifact_paths, record_path, decision_path)
    status = _iteration_status(record, decision_value, artifact_status, logs)

    return {
        "iteration": _iteration_number(iteration_dir),
        "path": str(iteration_dir),
        "status": status,
        "artifact_status": artifact_status,
        "execution_mode": record.get("execution_mode"),
        "hypothesis": record.get("hypothesis") or summary.get("hypothesis"),
        "strategy_change_summary": record.get("strategy_change_summary") or summary.get("strategy_change_summary"),
        "files_touched": record.get("files_touched") or summary.get("files_touched") or [],
        "decision": decision_value,
        "decision_reasons": decision_reasons,
        "metrics": metrics,
        "logs": logs,
        "artifacts": {item["name"]: item["exists"] for item in artifact_references},
        "artifact_references": artifact_references,
        "diagnosis": _iteration_diagnosis(
            status=status,
            artifact_references=artifact_references,
            decision_reasons=decision_reasons,
            record=record,
            metrics=metrics,
        ),
    }


def _artifact_references(
    repo_root: Path,
    iteration_dir: Path,
    artifact_paths: dict[str, Any],
    record_path: Path,
    decision_path: Path,
) -> list[dict[str, Any]]:
    known_paths = {
        "context_json": iteration_dir / "context.json",
        "context_markdown": iteration_dir / "context.md",
        "decision": decision_path,
        "iteration_record": record_path,
        "experiment_note_draft": iteration_dir / "experiment_note_draft.md",
    }
    references: list[dict[str, Any]] = []
    seen: set[str] = set()

    for name, default_path in known_paths.items():
        path = _artifact_path(repo_root, artifact_paths.get(name), default_path)
        references.append({"name": name, "path": str(path), "exists": path.exists()})
        seen.add(name)

    for name, value in sorted(artifact_paths.items()):
        if name in seen:
            continue
        path = _artifact_path(repo_root, value, iteration_dir / str(value))
        references.append({"name": str(name), "path": str(path), "exists": path.exists()})

    return references


def _artifact_path(repo_root: Path, value: Any, default_path: Path) -> Path:
    if not isinstance(value, str) or not value:
        return default_path
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return repo_root / path


def _best_iteration(iterations: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [
        iteration
        for iteration in iterations
        if _as_float((iteration.get("metrics") or {}).get("score")) is not None
    ]
    if not scored:
        return None
    return max(scored, key=lambda iteration: _as_float((iteration.get("metrics") or {}).get("score")) or float("-inf"))


def _iteration_analysis(
    iteration: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, str]:
    hypothesis = _display_text(iteration.get("hypothesis"), "No hypothesis reported.")
    previous_hypothesis = _display_text(previous.get("hypothesis"), "No previous hypothesis.") if previous else None
    strategy = _display_text(iteration.get("strategy_change_summary"), "No strategy change summary reported.")
    previous_strategy = (
        _display_text(previous.get("strategy_change_summary"), "No previous strategy summary.") if previous else None
    )
    files_touched = [str(path) for path in iteration.get("files_touched") or []]

    strategy_lines = []
    if previous_strategy is not None:
        strategy_lines.append(f"Previous: {previous_strategy}")
    else:
        strategy_lines.append("Previous: No previous iteration.")
    strategy_lines.append(f"Current: {strategy}")
    if files_touched:
        strategy_lines.append("Files touched:")
        strategy_lines.extend(f"- {path}" for path in files_touched)

    return {
        "hypothesis_diff": "\n".join(
            [
                (
                    f"Previous: {previous_hypothesis}"
                    if previous_hypothesis is not None
                    else "Previous: No previous iteration."
                ),
                f"Current: {hypothesis}",
            ]
        ),
        "strategy_diff": "\n".join(strategy_lines),
    }


def _display_text(value: Any, fallback: str) -> str:
    if value in (None, ""):
        return fallback
    return str(value)


def _metric_breakdown(
    iteration: dict[str, Any],
    previous: dict[str, Any] | None,
    best_iteration: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "current": iteration.get("metrics") or {},
        "comparisons": _metric_comparisons(iteration, previous, best_iteration),
    }


def _metric_comparisons(
    iteration: dict[str, Any],
    previous: dict[str, Any] | None,
    best_iteration: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return [
        _iteration_comparison("vs previous iteration", iteration, previous),
        _baseline_comparison(iteration),
        _iteration_comparison("vs best iteration in current run", iteration, best_iteration),
    ]


def _iteration_comparison(
    label: str,
    iteration: dict[str, Any],
    reference: dict[str, Any] | None,
) -> dict[str, Any]:
    if reference is None:
        return {
            "label": label,
            "reference_iteration": None,
            "deltas": {},
            "summary": "No comparison iteration available.",
        }

    deltas = _metric_deltas(iteration.get("metrics") or {}, reference.get("metrics") or {})
    return {
        "label": label,
        "reference_iteration": reference.get("iteration"),
        "deltas": deltas,
        "summary": _comparison_summary(deltas),
    }


def _baseline_comparison(iteration: dict[str, Any]) -> dict[str, Any]:
    metrics = iteration.get("metrics") or {}
    score = _as_float(metrics.get("score"))
    baseline = _as_float(metrics.get("baseline_sharpe"))
    if score is None or baseline is None:
        return {
            "label": "vs current baseline",
            "reference_iteration": None,
            "deltas": {},
            "summary": "No baseline metric available.",
        }

    deltas = {"score": score - baseline}
    return {
        "label": "vs current baseline",
        "reference_iteration": None,
        "reference_metric": "baseline_sharpe",
        "reference_value": baseline,
        "deltas": deltas,
        "summary": _comparison_summary(deltas),
    }


def _metric_deltas(current: dict[str, Any], reference: dict[str, Any]) -> dict[str, float]:
    deltas: dict[str, float] = {}
    for key in ("score", "deflated_sr", "drawdown", "turnover", "trades", "baseline_delta"):
        current_value = _as_float(current.get(key))
        reference_value = _as_float(reference.get(key))
        if current_value is not None and reference_value is not None:
            deltas[key] = current_value - reference_value
    return deltas


def _comparison_summary(deltas: dict[str, float]) -> str:
    if not deltas:
        return "No comparable metrics available."
    return "; ".join(f"{key}: {value:+.6g}" for key, value in deltas.items())


def _decision_value(record: dict[str, Any], decision_payload: dict[str, Any]) -> str | None:
    record_decision = record.get("decision")
    if isinstance(record_decision, dict):
        return _string_or_none(record_decision.get("decision"))
    if isinstance(record_decision, str):
        return record_decision
    return _string_or_none(decision_payload.get("decision"))


def _decision_reasons(record: dict[str, Any], decision_payload: dict[str, Any]) -> list[str]:
    for candidate in (
        record.get("decision_reason"),
        record.get("decision_reasons"),
        decision_payload.get("reasons"),
        record.get("decision", {}).get("reasons") if isinstance(record.get("decision"), dict) else None,
    ):
        if isinstance(candidate, list):
            return [str(item) for item in candidate]
        if isinstance(candidate, str):
            return [candidate]
    return []


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _iteration_metrics(
    record: dict[str, Any],
    decision_payload: dict[str, Any],
    ledger_row: dict[str, Any],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}

    evaluation_summary = record.get("evaluation_summary")
    if isinstance(evaluation_summary, dict):
        metrics.update(evaluation_summary)

    record_decision = record.get("decision")
    if isinstance(record_decision, dict):
        metrics.update(record_decision)

    metrics.update(decision_payload)
    metrics.update(ledger_row)

    score = _as_float(metrics.get("score"))
    baseline = _as_float(metrics.get("baseline_sharpe"))
    if score is not None and baseline is not None:
        metrics["baseline_delta"] = score - baseline

    return metrics


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iteration_logs(iteration_dir: Path) -> list[dict[str, Any]]:
    logs = []
    for path in sorted(iteration_dir.glob("*.log")):
        logs.append(
            {
                "path": str(path),
                "updated_at": _datetime_from_mtime(path).isoformat(),
                "excerpt": _read_text_excerpt(path),
            }
        )
    return logs


def _read_text_excerpt(path: Path, max_chars: int = 1000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _iteration_status(
    record: dict[str, Any],
    decision_value: str | None,
    artifact_status: Any,
    logs: list[dict[str, Any]],
) -> str:
    normalized_decision = (decision_value or "").lower().replace("_", "-")
    normalized_artifact_status = str(artifact_status or "").lower()

    if normalized_artifact_status == "failed" or normalized_decision == "failed":
        return "Failed"
    if normalized_decision == "keep":
        return "Kept"
    if normalized_decision == "revert":
        return "Reverted"
    if normalized_decision in {"follow-up", "followup"}:
        return "Follow-up"
    if normalized_decision == "pending-evaluation":
        return "Decision Pending"
    if normalized_artifact_status in {"completed", "simulated"} and not normalized_decision:
        return "Decision Pending"
    if normalized_artifact_status in {"running", "in-progress", "in_progress", "started"}:
        return "In Progress"
    if normalized_artifact_status in {"queued", "pending", "created"}:
        return "Queued"
    if record:
        return "Evaluated"
    if logs:
        return "In Progress"
    return "Queued"


def _iteration_diagnosis(
    *,
    status: str,
    artifact_references: list[dict[str, Any]],
    decision_reasons: list[str],
    record: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any] | None:
    available_artifacts = [item["name"] for item in artifact_references if item.get("exists")]
    missing_artifacts = [item["name"] for item in artifact_references if not item.get("exists")]

    if status == "Failed":
        details = decision_reasons or _iteration_failure_details(record, metrics)
        return {
            "reason": "failed_iteration",
            "details": details or ["Iteration failed before producing a successful decision."],
            "available_artifacts": available_artifacts,
            "missing_artifacts": missing_artifacts,
        }
    if status == "Decision Pending":
        return {
            "reason": "decision_pending",
            "details": ["Awaiting decision artifact or final keep/revert outcome."],
            "available_artifacts": available_artifacts,
            "missing_artifacts": [name for name in ("decision",) if name in missing_artifacts],
        }
    if status == "In Progress":
        return {
            "reason": "artifacts_pending",
            "details": ["Iteration is still active and has not produced all expected artifacts yet."],
            "available_artifacts": available_artifacts,
            "missing_artifacts": [name for name in ("iteration_record", "decision") if name in missing_artifacts],
        }
    if status == "Queued":
        return {
            "reason": "queued",
            "details": ["No iteration logs or decision artifacts detected yet."],
            "available_artifacts": available_artifacts,
            "missing_artifacts": [name for name in ("iteration_record", "decision") if name in missing_artifacts],
        }
    if decision_reasons:
        return {
            "reason": "decision_recorded",
            "details": decision_reasons,
            "available_artifacts": available_artifacts,
            "missing_artifacts": [],
        }
    return None


def _iteration_failure_details(record: dict[str, Any], metrics: dict[str, Any]) -> list[str]:
    evaluation_summary = record.get("evaluation_summary")
    if isinstance(evaluation_summary, dict):
        error = evaluation_summary.get("error")
        if error:
            return [str(error)]
    error = metrics.get("error")
    if error:
        return [str(error)]
    return []


def _latest_heartbeat(
    run_root: Path | None,
    state_path: Path,
    state: dict[str, Any],
    observed_at: datetime,
) -> dict[str, Any]:
    log_candidates: list[tuple[datetime, str, Path | None]] = []
    artifact_candidates: list[tuple[datetime, str, Path | None]] = []
    state_candidates: list[tuple[datetime, str, Path | None]] = []

    if run_root is not None and run_root.exists():
        for path in run_root.rglob("*.log"):
            log_candidates.append((_datetime_from_mtime(path), "log", path))
        for pattern in ("iteration_record.json", "decision.json", "context.json"):
            for path in run_root.rglob(pattern):
                artifact_candidates.append((_datetime_from_mtime(path), "artifact", path))

    state_updated_at = _parse_datetime(state.get("updated_at"))
    if state_updated_at is not None:
        state_candidates.append((state_updated_at, "state", state_path))
    elif state_path.exists():
        state_candidates.append((_datetime_from_mtime(state_path), "state", state_path))

    candidates = log_candidates + artifact_candidates + state_candidates
    if not candidates:
        return {
            "source_role": None,
            "path": None,
            "updated_at": None,
            "age_seconds": None,
        }

    viable_candidates = [candidate for candidate in candidates if candidate[0] <= observed_at]
    if viable_candidates:
        candidates = viable_candidates

    updated_at, source_role, path = max(candidates, key=lambda candidate: candidate[0])
    return {
        "source_role": source_role,
        "path": str(path) if path is not None else None,
        "updated_at": updated_at.isoformat(),
        "age_seconds": max(0.0, (observed_at - updated_at).total_seconds()),
    }


def _datetime_from_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _normalize_datetime(parsed)


def _normalize_run(
    state: dict[str, Any],
    heartbeat: dict[str, Any],
    observed_at: datetime,
    stale_after_seconds: int,
) -> dict[str, Any]:
    del observed_at
    heartbeat_age = heartbeat.get("age_seconds")
    raw_status = str(state.get("status") or "missing").lower()
    active_iteration = state.get("active_iteration")
    status = _run_status(raw_status, active_iteration, heartbeat_age, stale_after_seconds, bool(state))
    diagnosis = _run_diagnosis(state, status, heartbeat)

    return {
        "run_id": state.get("run_id"),
        "status": status,
        "raw_status": state.get("status"),
        "active_iteration": active_iteration,
        "current_iteration": state.get("current_iteration"),
        "iteration_budget": state.get("iteration_budget"),
        "latest_update": heartbeat.get("updated_at") or state.get("updated_at"),
        "best_score": state.get("best_score"),
        "best_iteration": state.get("best_iteration"),
        "stop_reason": state.get("stop_reason"),
        "heartbeat": heartbeat,
        "diagnosis": diagnosis,
    }


def _run_status(
    raw_status: str,
    active_iteration: Any,
    heartbeat_age: Any,
    stale_after_seconds: int,
    has_state: bool,
) -> str:
    if raw_status == "blocked":
        return "Blocked"
    if raw_status == "failed":
        return "Failed"
    if raw_status == "completed":
        return "Completed"
    if not has_state:
        return "Waiting"
    if heartbeat_age is not None and heartbeat_age > stale_after_seconds:
        return "Stalled"
    if active_iteration not in (None, "", 0):
        return "Busy"
    if raw_status == "running":
        return "Healthy"
    return "Waiting"


def _run_diagnosis(
    state: dict[str, Any],
    status: str,
    heartbeat: dict[str, Any],
) -> dict[str, Any] | None:
    if status == "Waiting":
        if not state:
            return {
                "reason": "awaiting_state",
                "details": ["No active run state file detected yet."],
            }
        return {
            "reason": "awaiting_activity",
            "details": ["Run state exists but there is no active iteration or fresh heartbeat yet."],
        }
    if status == "Stalled":
        return {
            "reason": "heartbeat_stale",
            "affected_iteration": state.get("active_iteration") or state.get("current_iteration"),
            "time_since_heartbeat_seconds": heartbeat.get("age_seconds"),
            "stale_signal": heartbeat.get("source_role"),
            "path": heartbeat.get("path"),
        }
    if status in {"Blocked", "Failed"}:
        return {
            "reason": state.get("stop_reason") or state.get("last_error") or status.lower(),
            "details": _state_failure_details(state),
        }
    if status == "Completed" and state.get("stop_reason"):
        details: list[str] = []
        last_completed_iteration = state.get("last_completed_iteration")
        if last_completed_iteration not in (None, ""):
            details.append(f"last_completed_iteration={last_completed_iteration}")
        return {
            "reason": state.get("stop_reason"),
            "details": details,
        }
    return None


def _state_failure_details(state: dict[str, Any]) -> list[str]:
    last_decision = state.get("last_decision")
    if isinstance(last_decision, dict):
        reasons = last_decision.get("reasons")
        if isinstance(reasons, list):
            return [str(reason) for reason in reasons]
        if isinstance(reasons, str):
            return [reasons]

    last_error = state.get("last_error")
    if isinstance(last_error, str) and last_error:
        return [part.strip() for part in last_error.split(";") if part.strip()]
    return []
