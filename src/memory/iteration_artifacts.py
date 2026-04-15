from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def render_experiment_note_draft(record: dict[str, Any]) -> str:
    summary = record.get("summary") or {}
    decision = record.get("decision") or {}
    continuation = record.get("continuation_context") or {}
    artifact_paths = record.get("artifact_paths") or {}
    current_baseline = continuation.get("current_baseline") or {}

    bounded_result = decision.get("bounded_result") or {}
    unrestricted_result = decision.get("unrestricted_result") or {}
    decision_reasons = decision.get("reasons") or []
    fee_lesson = decision.get("turnover_fee_lesson") or "TODO: capture fee / turnover lesson explicitly after evaluation."

    lines = [
        "---",
        "note_type: experiment_draft",
        "draft_type: derived_iteration_artifact",
        f"run_id: {record.get('run_id')}",
        f"iteration_number: {record.get('iteration_number')}",
        f"validation_status: {decision.get('validation_status', 'candidate')}",
        f"artifact_status: {record.get('artifact_status', 'unknown')}",
        f"execution_mode: {record.get('execution_mode', 'unknown')}",
        f"derived_from_iteration_record: {artifact_paths.get('iteration_record', '')}",
        f"continuation_manifest: {continuation.get('manifest_path', '')}",
        "raw_note_materialization: pending_explicit_finalize",
        "---",
        "",
        "# Experiment Note Draft",
        "",
        "> This is a **derived draft** from the iteration artifact bundle.",
        "> It is not raw evidence, not the canonical continuation manifest, and must not be treated as a finalized experiment note.",
        "",
        "## Objective",
        summary.get("hypothesis") or "No hypothesis reported yet.",
        "",
        "## Proposed Change",
        summary.get("strategy_change_summary") or "No strategy change summary reported yet.",
        "",
        "## Baseline Context",
        f"- Continuation manifest: {continuation.get('manifest_path') or '(missing)'}",
        f"- Current baseline: {current_baseline.get('title') or '(missing)'}",
        f"- Baseline note: {current_baseline.get('raw_note_path') or '(missing)'}",
        f"- Next recommended experiment: {continuation.get('next_recommended_experiment') or '(missing)'}",
        "",
        "## Evaluation Evidence",
    ]

    if record.get("artifact_status") == "simulated":
        lines.extend(
            [
                "- This round was generated in dry-run / simulated mode.",
                "- Placeholder artifacts are present for auditability only; no real evaluator conclusion should be inferred from this draft.",
            ]
        )
    else:
        lines.append("- See decision payload and evaluator logs in the artifact bundle.")

    lines.extend(
        [
            f"- Context bundle: {artifact_paths.get('context_json') or '(missing)'}",
            f"- Prompt artifact: {artifact_paths.get('claude_prompt') or '(missing)'}",
            f"- Decision payload: {artifact_paths.get('decision') or '(missing)'}",
            "",
            "## Bounded Result",
        ]
    )
    if bounded_result:
        for key in ("score", "drawdown", "trades", "baseline_sharpe"):
            if key in bounded_result:
                lines.append(f"- {key.upper()}: `{bounded_result[key]}`")
    else:
        lines.append("- No bounded result recorded yet.")

    lines.extend(["", "## Unrestricted Result"])
    if unrestricted_result:
        for key in ("score", "drawdown", "trades", "baseline_sharpe"):
            if key in unrestricted_result:
                lines.append(f"- {key.upper()}: `{unrestricted_result[key]}`")
    else:
        lines.append("- No unrestricted result recorded yet.")

    lines.extend(["", "## Decision State"])
    lines.append(f"- Decision: `{decision.get('decision', 'pending_evaluation')}`")
    lines.append(f"- Validation status: `{decision.get('validation_status', 'candidate')}`")
    if decision_reasons:
        for reason in decision_reasons:
            lines.append(f"- Reason: {reason}")
    else:
        lines.append("- Reason: awaiting real evaluator output.")

    lines.extend(["", "## Fee / Turnover Lesson", fee_lesson, "", "## Finalization Status"])
    lines.extend(
        [
            "- This file is rebuildable from the machine artifact bundle.",
            "- Final raw note creation or update requires an explicit finalize step.",
            "- Generic intake and summary refresh must ignore this draft by default.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"
