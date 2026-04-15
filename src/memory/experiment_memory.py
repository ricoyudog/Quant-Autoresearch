from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from config.vault import get_vault_paths

try:
    from core.research import read_frontmatter
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from src.core.research import read_frontmatter

CONTINUATION_MANIFEST_PATH = Path("experiments/continuation/current_research_base.json")
GENERIC_EXPERIMENT_TAGS = {
    "experiment",
    "experiments",
    "minute-level",
    "momentum",
    "research",
    "knowledge",
    "index",
    "progress",
    "completed",
}
METRIC_ALIASES = {
    "score": "score",
    "baseline_sharpe": "baseline_sharpe",
    "naive_sharpe": "naive_sharpe",
    "nw_sharpe_bias": "nw_sharpe_bias",
    "deflated_sr": "deflated_sr",
    "sortino": "sortino",
    "calmar": "calmar",
    "drawdown": "drawdown",
    "max_dd_days": "max_dd_days",
    "trades": "trades",
    "win_rate": "win_rate",
    "profit_factor": "profit_factor",
    "avg_win": "avg_win",
    "avg_loss": "avg_loss",
}
METRIC_LINE_PATTERN = re.compile(
    r"^-\s*(?P<label>[A-Z_ ]+):\s*`?(?P<value>-?\d+(?:\.\d+)?)`?\s*$"
)
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
DATE_PATTERN = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "experiment"


def _note_text(note_path: Path) -> str:
    return note_path.read_text(encoding="utf-8")


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2].lstrip("\n")


def _read_title(note_path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return note_path.stem


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_title: str | None = None
    current_lines: list[str] = []

    for raw_line in body.splitlines():
        match = re.match(r"^(#{2,3})\s+(.*)$", raw_line)
        if match:
            if current_title is not None:
                sections[current_title] = current_lines[:]
            current_title = match.group(2).strip().lower()
            current_lines = []
            continue
        if current_title is not None:
            current_lines.append(raw_line)

    if current_title is not None:
        sections[current_title] = current_lines

    return {title: "\n".join(lines).strip() for title, lines in sections.items()}


def _metric_block_from_text(body: str, labels: tuple[str, ...]) -> dict[str, float]:
    lines = body.splitlines()
    for index, raw_line in enumerate(lines):
        normalized = raw_line.strip().lower().rstrip(":")
        if not any(label in normalized for label in labels):
            continue

        block: list[str] = []
        for follow in lines[index + 1 :]:
            stripped = follow.strip()
            if not stripped:
                if block:
                    break
                continue
            if re.match(r"^#{2,3}\s+", stripped):
                break
            if block and not stripped.startswith("-"):
                break
            block.append(stripped)

        metrics = _parse_metric_lines(block)
        if metrics:
            return metrics

    return {}


def _parse_metric_lines(lines: list[str]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in lines:
        match = METRIC_LINE_PATTERN.match(line)
        if not match:
            continue
        raw_label = match.group("label").strip().lower().replace(" ", "_")
        metric_key = METRIC_ALIASES.get(raw_label)
        if metric_key is None:
            continue
        metrics[metric_key] = float(match.group("value"))
    return metrics


def _extract_wiki_links(text: str) -> list[str]:
    return WIKI_LINK_PATTERN.findall(text)


def _derive_reference(frontmatter: dict[str, Any], key: str, fallback_text: str, matchers: tuple[str, ...]) -> str | None:
    explicit_value = frontmatter.get(key)
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()

    for link in _extract_wiki_links(fallback_text):
        normalized = link.lower()
        if any(matcher in normalized for matcher in matchers):
            return link
    return None


def _derive_baseline_reference(frontmatter: dict[str, Any], sections: dict[str, str], body: str) -> str | None:
    explicit_value = frontmatter.get("baseline_reference")
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()

    baseline_section = sections.get("baseline before this experiment", "")
    for link in _extract_wiki_links(baseline_section):
        return link

    for link in _extract_wiki_links(body):
        if "experiment-index" in link.lower():
            continue
        if DATE_PATTERN.search(link):
            return link
    return None


def _derive_branch_id(frontmatter: dict[str, Any], note_path: Path) -> str:
    explicit_value = frontmatter.get("branch_id")
    if isinstance(explicit_value, str) and explicit_value.strip():
        return _slugify(explicit_value)

    tags = frontmatter.get("tags") or []
    for raw_tag in tags:
        tag = _slugify(str(raw_tag))
        if tag not in GENERIC_EXPERIMENT_TAGS:
            return tag

    experiment_slug = frontmatter.get("experiment_slug")
    if isinstance(experiment_slug, str) and experiment_slug.strip():
        return _slugify(experiment_slug)

    return _slugify(note_path.stem)


def _derive_parent_experiment(frontmatter: dict[str, Any], sections: dict[str, str], body: str) -> str | None:
    explicit_value = frontmatter.get("parent_experiment")
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()

    baseline_reference = _derive_baseline_reference(frontmatter, sections, body)
    if baseline_reference:
        return baseline_reference
    return None


def _derive_decision(frontmatter: dict[str, Any], sections: dict[str, str], body: str) -> str:
    explicit_value = frontmatter.get("decision")
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip().lower()

    decision_text = "\n".join(
        filter(
            None,
            [sections.get("decision", ""), sections.get("interpretation", ""), body],
        )
    ).lower()
    if re.search(r"\b(revert|discard)\b", decision_text):
        return "revert"
    if re.search(r"\bkeep\b", decision_text):
        return "keep"
    return "unknown"


def _derive_decision_reasons(sections: dict[str, str]) -> list[str]:
    decision_section = sections.get("decision", "")
    if not decision_section:
        return []

    reasons: list[str] = []
    for raw_line in decision_section.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("reason:"):
            reason_text = line.split(":", 1)[1].strip()
            if reason_text:
                reasons.append(reason_text)
            continue
        if line.startswith("-"):
            reasons.append(line.lstrip("-").strip())
    return reasons


def _derive_turnover_fee_lesson(frontmatter: dict[str, Any], body: str) -> str | None:
    explicit_value = frontmatter.get("turnover_fee_lesson")
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()

    keywords = ("turnover", "fee", "transaction-cost", "transaction cost", "overtrading", "churn")
    matches = [
        line.strip()
        for line in body.splitlines()
        if any(keyword in line.lower() for keyword in keywords)
    ]
    if matches:
        return " ".join(matches[:3])
    return None


def _derive_next_experiment(frontmatter: dict[str, Any], sections: dict[str, str]) -> str | None:
    explicit_value = frontmatter.get("next_experiment")
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()

    next_section = sections.get("next experiment", "")
    if not next_section:
        return None

    cleaned_lines = [line.strip().lstrip("-").strip() for line in next_section.splitlines() if line.strip()]
    if not cleaned_lines:
        return None
    return " ".join(cleaned_lines)


def _derive_validation_status(frontmatter: dict[str, Any], decision: str) -> str:
    explicit_value = frontmatter.get("validation_status")
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()
    if decision == "keep":
        return "follow_up_required"
    if decision == "revert":
        return "rejected"
    return "candidate"


def _coerce_date(frontmatter: dict[str, Any], note_path: Path) -> str | None:
    raw_date = frontmatter.get("date")
    if isinstance(raw_date, str) and raw_date.strip():
        return raw_date.strip().strip("'")

    match = DATE_PATTERN.search(note_path.stem)
    if match:
        return match.group("date")
    return None


def _parse_experiment_note(note_path: Path) -> dict[str, Any]:
    text = _note_text(note_path)
    frontmatter = read_frontmatter(note_path)
    body = _strip_frontmatter(text)
    sections = _parse_sections(body)
    title = _read_title(note_path, text)
    decision = _derive_decision(frontmatter, sections, body)

    record = {
        "title": title,
        "note_date": _coerce_date(frontmatter, note_path),
        "raw_note_path": str(note_path),
        "experiment_slug": frontmatter.get("experiment_slug") or _slugify(title),
        "branch_id": _derive_branch_id(frontmatter, note_path),
        "parent_experiment": _derive_parent_experiment(frontmatter, sections, body),
        "baseline_reference": _derive_baseline_reference(frontmatter, sections, body),
        "status": frontmatter.get("status") or "completed",
        "decision": decision,
        "decision_reasons": _derive_decision_reasons(sections),
        "validation_status": _derive_validation_status(frontmatter, decision),
        "turnover_fee_lesson": _derive_turnover_fee_lesson(frontmatter, body),
        "next_experiment": _derive_next_experiment(frontmatter, sections),
        "bounded_result": _metric_block_from_text(body, ("bounded result", "post-change bounded result")),
        "unrestricted_result": _metric_block_from_text(body, ("unrestricted result",)),
        "idea_trace": _derive_reference(frontmatter, "idea_trace", body, ("/research/", "intraday-", "query")),
        "analysis_context": _derive_reference(
            frontmatter,
            "analysis_context",
            body,
            ("daily-research-kickoff", "analysis", "spy-analysis", "kickoff"),
        ),
        "results_tsv_path": "experiments/results.tsv",
        "related_links": _extract_wiki_links(body),
    }
    return record


def collect_experiment_memory(vault_root: str | Path | None = None) -> list[dict[str, Any]]:
    paths = get_vault_paths(vault_root)
    records: list[dict[str, Any]] = []
    for note_path in sorted(paths.experiments.glob("*.md")):
        if note_path.name == "experiment-index.md":
            continue
        records.append(_parse_experiment_note(note_path))
    records.sort(key=lambda item: (item.get("note_date") or "", item["raw_note_path"]))
    return records


def build_continuation_context(records: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_records = sorted(records, key=lambda item: (item.get("note_date") or "", item["raw_note_path"]))
    keep_records = [record for record in sorted_records if record["decision"] == "keep"]
    keep_references = {
        record["parent_experiment"]
        for record in keep_records
        if isinstance(record.get("parent_experiment"), str) and record["parent_experiment"]
    }
    terminal_keeps = [
        record
        for record in keep_records
        if Path(record["raw_note_path"]).stem not in keep_references
        and record.get("experiment_slug") not in keep_references
    ]
    baseline_pool = terminal_keeps or keep_records
    current_baseline = baseline_pool[-1] if baseline_pool else None
    failed_branches = [record for record in reversed(sorted_records) if record["decision"] == "revert"]
    next_experiment = None
    if current_baseline is not None:
        next_experiment = current_baseline.get("next_experiment")
    if not next_experiment and sorted_records:
        next_experiment = sorted_records[-1].get("next_experiment")

    return {
        "current_baseline": current_baseline,
        "recent_winning_branch": current_baseline,
        "failed_branches": failed_branches,
        "next_recommended_experiment": next_experiment,
        "experiments": sorted_records,
    }


def _render_metrics(metrics: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for metric_key in ("score", "drawdown", "trades", "baseline_sharpe"):
        if metric_key not in metrics:
            continue
        label = metric_key.upper()
        lines.append(f"- {label}: `{metrics[metric_key]}`")
    return lines


def render_experiment_index(manifest: dict[str, Any]) -> str:
    current_baseline = manifest.get("current_baseline") or {}
    failed_branches = manifest.get("failed_branches") or []
    recent_progress = manifest.get("experiments") or []
    branch_summary_paths = manifest.get("branch_summary_paths") or []

    lines = [
        "---",
        "note_type: index",
        "topic: experiment-index",
        "tags:",
        "  - experiments",
        "  - index",
        "  - progress",
        "---",
        "",
        "# Experiment Index",
        "",
        "This note is the quick-entry map for the current strategy knowledge loop.",
        "",
        "## Artifact Ownership",
        "- Raw evidence: Obsidian experiment notes remain the source evidence.",
        "- `experiments/continuation/current_research_base.json` is the automation manifest.",
        "- This index and any branch summaries are derived, rebuildable views.",
        "",
        "## Current Baseline To Continue From",
    ]

    if current_baseline:
        lines.extend(
            [
                f"- Source note: [[{Path(current_baseline['raw_note_path']).stem}]]",
                f"- Branch: `{current_baseline['branch_id']}`",
                f"- Validation status: `{current_baseline['validation_status']}`",
            ]
        )
        lines.extend(_render_metrics(current_baseline.get("bounded_result") or {}))
        if current_baseline.get("unrestricted_result"):
            lines.append("- Unrestricted follow-up captured in raw note")
        if current_baseline.get("turnover_fee_lesson"):
            lines.append(f"- Fee / turnover lesson: {current_baseline['turnover_fee_lesson']}")
    else:
        lines.append("- No keep baseline found yet.")

    lines.extend(["", "## Recent Progress Trail"])
    if recent_progress:
        for record in recent_progress:
            decision = record.get("decision", "unknown")
            validation_status = record.get("validation_status", "candidate")
            lines.extend(
                [
                    f"- [[{Path(record['raw_note_path']).stem}]]",
                    f"  - decision: `{decision}`",
                    f"  - validation_status: `{validation_status}`",
                ]
            )
            if record.get("next_experiment"):
                lines.append(f"  - next: {record['next_experiment']}")
    else:
        lines.append("- No experiment notes found yet.")

    lines.extend(["", "## Failed / Rejected Branches"])
    if failed_branches:
        for record in failed_branches:
            lines.append(f"- [[{Path(record['raw_note_path']).stem}]]")
            if record.get("decision_reasons"):
                lines.append(f"  - reasons: {'; '.join(record['decision_reasons'])}")
            if record.get("turnover_fee_lesson"):
                lines.append(f"  - lesson: {record['turnover_fee_lesson']}")
    else:
        lines.append("- No rejected branches recorded yet.")

    lines.extend(["", "## Next Recommended Experiment"])
    next_experiment = manifest.get("next_recommended_experiment")
    if next_experiment:
        lines.append(f"- {next_experiment}")
    else:
        lines.append("- No next experiment recorded yet.")

    lines.extend(["", "## Branch Summaries"])
    if branch_summary_paths:
        for path in branch_summary_paths:
            lines.append(f"- [[{Path(path).stem}]]")
    else:
        lines.append("- No branch summaries generated yet.")

    return "\n".join(lines).rstrip() + "\n"


def render_branch_summary(branch_id: str, records: list[dict[str, Any]]) -> str:
    sorted_records = sorted(records, key=lambda item: (item.get("note_date") or "", item["raw_note_path"]))
    latest_keep = next((record for record in reversed(sorted_records) if record["decision"] == "keep"), None)
    latest_revert = next((record for record in reversed(sorted_records) if record["decision"] == "revert"), None)

    lines = [
        "---",
        "note_type: summary",
        f"branch_id: {branch_id}",
        "tags:",
        "  - experiments",
        "  - summary",
        f"  - {branch_id}",
        "---",
        "",
        f"# Branch Summary - {branch_id}",
        "",
        "This summary is derived from raw experiment notes. Rebuild it instead of editing raw evidence.",
        "",
        "## Included Raw Notes",
    ]
    for record in sorted_records:
        lines.append(f"- [[{Path(record['raw_note_path']).stem}]]")

    lines.extend(["", "## Leading Candidate"])
    if latest_keep is not None:
        lines.append(f"- [[{Path(latest_keep['raw_note_path']).stem}]]")
        lines.append(f"- validation_status: `{latest_keep['validation_status']}`")
        lines.extend(_render_metrics(latest_keep.get("bounded_result") or {}))
    else:
        lines.append("- No keep candidate recorded yet.")

    lines.extend(["", "## Latest Rejection / Cautionary Lesson"])
    if latest_revert is not None:
        lines.append(f"- [[{Path(latest_revert['raw_note_path']).stem}]]")
        if latest_revert.get("decision_reasons"):
            lines.append(f"- reasons: {'; '.join(latest_revert['decision_reasons'])}")
        if latest_revert.get("turnover_fee_lesson"):
            lines.append(f"- fee lesson: {latest_revert['turnover_fee_lesson']}")
    else:
        lines.append("- No rejected branch recorded yet.")

    lines.extend(["", "## Next Step"])
    if latest_keep is not None and latest_keep.get("next_experiment"):
        lines.append(f"- {latest_keep['next_experiment']}")
    else:
        lines.append("- No next step recorded yet.")

    return "\n".join(lines).rstrip() + "\n"


def write_branch_summaries(vault_root: str | Path | None, records: list[dict[str, Any]]) -> list[str]:
    paths = get_vault_paths(vault_root)
    summaries_dir = paths.experiments / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["branch_id"]].append(record)

    summary_paths: list[str] = []
    for branch_id, branch_records in sorted(grouped.items()):
        if not branch_records:
            continue
        summary_path = summaries_dir / f"branch-summary-{branch_id}.md"
        summary_path.write_text(render_branch_summary(branch_id, branch_records), encoding="utf-8")
        summary_paths.append(str(summary_path))
    return summary_paths


def load_continuation_manifest(manifest_path: str | Path = CONTINUATION_MANIFEST_PATH) -> dict[str, Any] | None:
    resolved_path = Path(manifest_path).expanduser()
    if not resolved_path.exists():
        return None
    return json.loads(resolved_path.read_text(encoding="utf-8"))


def refresh_research_base(
    vault_root: str | Path | None = None,
    manifest_path: str | Path = CONTINUATION_MANIFEST_PATH,
) -> dict[str, Any]:
    records = collect_experiment_memory(vault_root)
    continuation = build_continuation_context(records)
    paths = get_vault_paths(vault_root)
    summary_paths = write_branch_summaries(vault_root, records)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "raw_note_directory": str(paths.experiments),
        "results_tsv_path": "experiments/results.tsv",
        "current_baseline": continuation["current_baseline"],
        "recent_winning_branch": continuation["recent_winning_branch"],
        "failed_branches": continuation["failed_branches"],
        "next_recommended_experiment": continuation["next_recommended_experiment"],
        "experiments": continuation["experiments"],
        "branch_summary_paths": summary_paths,
    }

    index_path = paths.experiments / "experiment-index.md"
    index_path.write_text(render_experiment_index(manifest), encoding="utf-8")

    manifest["index_note_path"] = str(index_path)
    resolved_manifest_path = Path(manifest_path).expanduser()
    resolved_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(resolved_manifest_path)
    return manifest
