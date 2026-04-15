"""Claude Code autoresearch outer-loop runner scaffold.

This file intentionally starts as a thin, reviewable orchestration surface.
It establishes the operator-facing CLI contract and the internal phase layout
for a Karpathy-style outer loop, while leaving the detailed loop behavior to
subsequent tasks.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.vault import get_vault_paths
from src.memory.idea_keep_revert import decide_keep_revert
from src.memory.experiment_memory import CONTINUATION_MANIFEST_PATH, load_continuation_manifest
from src.memory.iteration_artifacts import render_experiment_note_draft, write_json, write_text


DEFAULT_STATE_PATH = Path("experiments/autoresearch_state.json")
DEFAULT_STRATEGY_PATH = Path("src/strategies/active_strategy.py")
DEFAULT_ITERATION_ROOT = Path("experiments/iterations")
DEFAULT_CONTINUATION_MANIFEST_PATH = CONTINUATION_MANIFEST_PATH
DEFAULT_PROGRAM_PATH = Path("program.md")
DEFAULT_RESULTS_PATH = Path("experiments/results.tsv")
DEFAULT_NOTES_DIR = get_vault_paths().experiments
DEFAULT_CLAUDE_WRAPPER = Path("scripts/run_claude_iteration.sh")
METRIC_PATTERN = re.compile(r"^(?P<name>[A-Z_]+):\s*(?P<value>-?\d+(?:\.\d+)?)\s*$")
RUN_STATE_TEMPLATE = {
    "run_id": None,
    "status": "pending",
    "current_iteration": 0,
    "iteration_budget": None,
    "target_score": None,
    "max_no_improve": None,
    "no_improve_streak": 0,
    "best_score": None,
    "best_iteration": None,
    "best_strategy_reference": None,
    "last_decision": None,
    "updated_at": None,
}


def resolve_state_path(state_file: str | Path) -> Path:
    """Resolve the persisted run-state path."""
    return Path(state_file).expanduser()


def default_run_state() -> dict[str, Any]:
    """Return a fresh copy of the default persisted run-state payload."""
    return dict(RUN_STATE_TEMPLATE)


def load_run_state(state_file: str | Path) -> dict[str, Any]:
    """Load persisted run state, filling any missing keys from the default template."""
    path = resolve_state_path(state_file)
    if not path.exists():
        return default_run_state()

    data = json.loads(path.read_text())
    state = default_run_state()
    state.update(data)
    return state


def save_run_state(state_file: str | Path, state: dict[str, Any]) -> Path:
    """Persist the current run state with an updated timestamp."""
    path = resolve_state_path(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = default_run_state()
    payload.update(state)
    payload["updated_at"] = utc_now()

    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def resolve_strategy_path(strategy_file: str | Path) -> Path:
    """Resolve the strategy-under-iteration path."""
    return Path(strategy_file).expanduser()


def resolve_continuation_manifest_path(manifest_file: str | Path) -> Path:
    """Resolve the continuation manifest path for repo-local research memory."""
    return Path(manifest_file).expanduser()


def resolve_iteration_root(iteration_root: str | Path) -> Path:
    """Resolve the base iteration artifact root."""
    return Path(iteration_root).expanduser()


def resolve_program_path(program_file: str | Path) -> Path:
    """Resolve the program document path."""
    return Path(program_file).expanduser()


def resolve_results_path(results_file: str | Path) -> Path:
    """Resolve the results ledger path."""
    return Path(results_file).expanduser()


def resolve_notes_path(notes_dir: str | Path) -> Path:
    """Resolve the recent-note directory."""
    return Path(notes_dir).expanduser()


def resolve_wrapper_path(wrapper_path: str | Path) -> Path:
    """Resolve the iteration wrapper path."""
    return Path(wrapper_path).expanduser()


def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 form."""
    return datetime.now(timezone.utc).isoformat()


def get_snapshot_root(root: str | Path | None = None) -> Path:
    """Return the directory that stores per-iteration strategy snapshots."""
    snapshot_root = Path(root).expanduser() if root else DEFAULT_ITERATION_ROOT
    return snapshot_root / "snapshots"


def create_strategy_snapshot(
    strategy_file: str | Path,
    iteration_number: int,
    snapshot_root: str | Path | None = None,
) -> dict[str, Any]:
    """Create a reversible snapshot of the current strategy file."""
    strategy_path = resolve_strategy_path(strategy_file)
    if not strategy_path.exists():
        raise FileNotFoundError(f"Strategy file not found: {strategy_path}")

    snapshots_dir = get_snapshot_root(snapshot_root)
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshots_dir / f"iteration-{iteration_number:04d}-active_strategy.py"
    shutil.copy2(strategy_path, snapshot_path)

    return {
        "iteration_number": iteration_number,
        "strategy_path": str(strategy_path),
        "snapshot_path": str(snapshot_path),
        "created_at": utc_now(),
        "restored": False,
    }


def restore_strategy_snapshot(
    snapshot: dict[str, Any] | str | Path,
    strategy_file: str | Path | None = None,
) -> dict[str, Any]:
    """Restore a previously created strategy snapshot."""
    if isinstance(snapshot, dict):
        snapshot_path = Path(snapshot["snapshot_path"]).expanduser()
        target_path = resolve_strategy_path(strategy_file or snapshot["strategy_path"])
        restored_snapshot = dict(snapshot)
    else:
        snapshot_path = Path(snapshot).expanduser()
        if strategy_file is None:
            raise ValueError("strategy_file is required when restoring from a raw snapshot path.")
        target_path = resolve_strategy_path(strategy_file)
        restored_snapshot = {
            "snapshot_path": str(snapshot_path),
            "strategy_path": str(target_path),
        }

    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(snapshot_path, target_path)
    restored_snapshot["restored"] = True
    restored_snapshot["restored_at"] = utc_now()
    return restored_snapshot


def parse_backtest_metrics(output: str, previous_best: float | None = None) -> dict[str, Any]:
    """Parse the deterministic backtest metrics block into normalized values."""
    metrics: dict[str, Any] = {}
    aliases = {
        "SCORE": "score",
        "BASELINE_SHARPE": "baseline_sharpe",
        "NAIVE_SHARPE": "naive_sharpe",
        "NW_SHARPE_BIAS": "nw_sharpe_bias",
        "DEFLATED_SR": "deflated_sr",
    }

    for raw_line in output.splitlines():
        line = raw_line.strip()
        match = METRIC_PATTERN.match(line)
        if not match:
            continue

        key = aliases.get(match.group("name"))
        if key is None:
            continue
        metrics[key] = float(match.group("value"))

    if "score" not in metrics or "baseline_sharpe" not in metrics:
        raise ValueError("Missing required backtest metrics: SCORE and BASELINE_SHARPE are required.")

    metrics["previous_best"] = previous_best
    return metrics


def normalize_backtest_decision(
    output: str,
    previous_best: float | None = None,
    idea_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert raw backtest stdout into the keep/revert decision contract."""
    metrics = parse_backtest_metrics(output, previous_best=previous_best)
    decision = decide_keep_revert(metrics, idea_review=idea_review)

    for advisory_key in ("naive_sharpe", "nw_sharpe_bias", "deflated_sr"):
        if advisory_key in metrics:
            decision[advisory_key] = metrics[advisory_key]

    return decision


def read_text_excerpt(path: Path, max_chars: int = 4000) -> str:
    """Read a file excerpt safely for context assembly."""
    if not path.exists() or not path.is_file():
        return ""

    text = path.read_text(encoding="utf-8", errors="ignore")
    excerpt = text[:max_chars].strip()
    if len(text) > max_chars:
        excerpt += "\n..."
    return excerpt


def read_results_excerpt(results_path: Path, max_lines: int = 5) -> str:
    """Return the tail of the results ledger for context assembly."""
    if not results_path.exists() or not results_path.is_file():
        return ""

    lines = [
        line.rstrip("\n")
        for line in results_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    ]
    if not lines:
        return ""
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join([lines[0], *lines[-(max_lines - 1) :]])


def collect_recent_notes(notes_dir: Path, limit: int) -> list[dict[str, Any]]:
    """Collect the most recent note files for the current iteration context."""
    if limit <= 0 or not notes_dir.exists() or not notes_dir.is_dir():
        return []

    note_files = [
        path
        for path in notes_dir.rglob("*")
        if path.is_file() and path.name != ".gitkeep" and path.suffix.lower() in {".md", ".txt", ".json"}
    ]
    note_files.sort(key=lambda candidate: candidate.stat().st_mtime, reverse=True)

    notes: list[dict[str, Any]] = []
    for note_path in note_files[:limit]:
        notes.append(
            {
                "path": str(note_path),
                "name": note_path.name,
                "excerpt": read_text_excerpt(note_path, max_chars=800),
            }
        )
    return notes


def assemble_iteration_context(
    state: dict[str, Any],
    args: argparse.Namespace,
    iteration_number: int,
) -> dict[str, Any]:
    """Assemble the repository context bundle passed into an iteration."""
    strategy_path = resolve_strategy_path(args.strategy)
    program_path = resolve_program_path(args.program)
    results_path = resolve_results_path(args.results_file)
    notes_dir = resolve_notes_path(args.notes_dir)

    return {
        "run": {
            "run_id": state.get("run_id"),
            "iteration_number": iteration_number,
            "iteration_budget": state.get("iteration_budget"),
            "best_score": state.get("best_score"),
            "best_iteration": state.get("best_iteration"),
            "no_improve_streak": state.get("no_improve_streak"),
            "target_score": state.get("target_score"),
            "max_no_improve": state.get("max_no_improve"),
            "last_decision": state.get("last_decision"),
        },
        "sources": {
            "program": str(program_path),
            "strategy": str(strategy_path),
            "results_file": str(results_path),
            "notes_dir": str(notes_dir),
        },
        "program_excerpt": read_text_excerpt(program_path),
        "strategy_excerpt": read_text_excerpt(strategy_path, max_chars=2000),
        "results_excerpt": read_results_excerpt(results_path),
        "recent_notes": collect_recent_notes(notes_dir, args.recent_notes_limit),
    }


def render_context_markdown(context: dict[str, Any]) -> str:
    """Render the iteration context bundle as human-readable markdown."""
    lines = [
        "# Claude Code Iteration Context",
        "",
        "## Run State",
        f"- Run ID: {context['run']['run_id']}",
        f"- Iteration: {context['run']['iteration_number']} / {context['run']['iteration_budget']}",
        f"- Best score: {context['run']['best_score']}",
        f"- Best iteration: {context['run']['best_iteration']}",
        f"- No-improve streak: {context['run']['no_improve_streak']}",
        f"- Last decision: {context['run']['last_decision']}",
        "",
        "## Sources",
        f"- Program: {context['sources']['program']}",
        f"- Strategy: {context['sources']['strategy']}",
        f"- Results ledger: {context['sources']['results_file']}",
        f"- Notes dir: {context['sources']['notes_dir']}",
        "",
        "## Program Excerpt",
        "```markdown",
        context["program_excerpt"] or "(missing)",
        "```",
        "",
        "## Strategy Excerpt",
        "```python",
        context["strategy_excerpt"] or "(missing)",
        "```",
        "",
        "## Recent Results",
        "```text",
        context["results_excerpt"] or "(missing)",
        "```",
        "",
        "## Recent Notes",
    ]

    if context["recent_notes"]:
        for note in context["recent_notes"]:
            lines.extend(
                [
                    f"### {note['name']}",
                    f"- Path: {note['path']}",
                    "```text",
                    note["excerpt"] or "(empty)",
                    "```",
                    "",
                ]
            )
    else:
        lines.append("- No recent notes found.")

    return "\n".join(lines).strip() + "\n"


def write_context_bundle(iteration_dir: Path, context: dict[str, Any]) -> tuple[Path, Path]:
    """Write structured and markdown context artifacts for one iteration."""
    context_json_path = write_json(iteration_dir / "context.json", context)
    context_md_path = write_text(iteration_dir / "context.md", render_context_markdown(context))
    return context_json_path, context_md_path


def build_round_summary(execution_mode: str) -> dict[str, Any]:
    """Build a conservative round summary when no live agent output exists yet."""
    if execution_mode == "dry_run":
        return {
            "hypothesis": "Dry-run artifact generation only; no live hypothesis was proposed.",
            "strategy_change_summary": "No strategy changes were attempted because this run only generated audit artifacts.",
            "files_touched": [],
        }
    return {
        "hypothesis": "No hypothesis reported.",
        "strategy_change_summary": "No strategy change summary reported.",
        "files_touched": [],
    }


def build_placeholder_decision(execution_mode: str) -> dict[str, Any]:
    """Build a conservative non-evaluation decision payload."""
    return {
        "decision": "pending_evaluation",
        "reasons": ["no_live_evaluator_output"],
        "validation_status": "candidate",
        "artifact_status": "simulated" if execution_mode == "dry_run" else "placeholder",
        "execution_mode": execution_mode,
        "bounded_result": {},
        "unrestricted_result": {},
        "turnover_fee_lesson": "TODO: evaluate fee / turnover impact after a real run.",
    }


def generate_run_id() -> str:
    """Return a stable run identifier for a new autoresearch session."""
    return datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%S%fZ")


def get_run_root(iteration_root: str | Path, run_id: str) -> Path:
    """Return the artifact root for the active run."""
    return resolve_iteration_root(iteration_root) / run_id


def load_or_initialize_run(args: argparse.Namespace) -> dict[str, Any]:
    """Load an existing run state or initialize a new one from CLI args."""
    state = load_run_state(args.state_file)
    if state.get("run_id") is None:
        state["run_id"] = generate_run_id()
        state["current_iteration"] = 0
        state["best_score"] = None
        state["best_iteration"] = None
        state["best_strategy_reference"] = None
        state["last_decision"] = None
        state["no_improve_streak"] = 0

    state["status"] = "pending" if args.dry_run else "running"
    state["iteration_budget"] = args.iterations
    state["target_score"] = args.target_score
    state["max_no_improve"] = args.max_no_improve
    state["strategy_path"] = str(resolve_strategy_path(args.strategy))
    state["iteration_root"] = str(get_run_root(args.iteration_root, state["run_id"]))
    return state


def write_placeholder(path: Path, content: str) -> Path:
    """Write a placeholder text artifact."""
    return write_text(path, content.rstrip() + "\n")


def run_wrapper(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Execute the iteration wrapper."""
    return subprocess.run(command, check=False, capture_output=True, text=True)


def build_parser() -> argparse.ArgumentParser:
    """Build the minimal CLI parser for the outer-loop runner."""
    parser = argparse.ArgumentParser(
        description="Run a bounded Claude Code-driven autoresearch loop.",
    )
    parser.add_argument("--iterations", type=int, required=True, help="Maximum number of autoresearch rounds.")
    parser.add_argument(
        "--strategy",
        default=str(DEFAULT_STRATEGY_PATH),
        help="Path to the strategy-under-iteration file.",
    )
    parser.add_argument(
        "--state-file",
        default=str(DEFAULT_STATE_PATH),
        help="Path to the persisted autoresearch state file.",
    )
    parser.add_argument(
        "--iteration-root",
        default=str(DEFAULT_ITERATION_ROOT),
        help="Directory used for per-iteration artifacts and strategy snapshots.",
    )
    parser.add_argument(
        "--program",
        default=str(DEFAULT_PROGRAM_PATH),
        help="Path to program.md or an equivalent runner program file.",
    )
    parser.add_argument(
        "--results-file",
        default=str(DEFAULT_RESULTS_PATH),
        help="Path to the results.tsv ledger used for context assembly.",
    )
    parser.add_argument(
        "--notes-dir",
        default=str(DEFAULT_NOTES_DIR),
        help="Directory containing recent raw experiment notes for context assembly.",
    )
    parser.add_argument(
        "--recent-notes-limit",
        type=int,
        default=3,
        help="Maximum number of recent note files to include in the iteration context bundle.",
    )
    parser.add_argument(
        "--claude-wrapper",
        default=str(DEFAULT_CLAUDE_WRAPPER),
        help="Shell wrapper used to invoke one Claude Code iteration.",
    )
    parser.add_argument(
        "--target-score",
        type=float,
        default=None,
        help="Optional score threshold that can stop the run early.",
    )
    parser.add_argument(
        "--max-no-improve",
        type=int,
        default=None,
        help="Optional consecutive non-improving round limit.",
    )
    parser.add_argument(
        "--continuation-manifest",
        default=str(DEFAULT_CONTINUATION_MANIFEST_PATH),
        help="Path to the canonical continuation manifest for current research memory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the planned runner contract without executing rounds.",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate the minimum argument contract before deeper implementation exists."""
    if args.iterations <= 0:
        raise SystemExit("--iterations must be greater than 0.")
    if args.max_no_improve is not None and args.max_no_improve < 0:
        raise SystemExit("--max-no-improve must be 0 or greater.")
    if args.recent_notes_limit < 0:
        raise SystemExit("--recent-notes-limit must be 0 or greater.")

    strategy_path = resolve_strategy_path(args.strategy)
    if not strategy_path.exists():
        raise SystemExit(f"Strategy file not found: {strategy_path}")

    program_path = resolve_program_path(args.program)
    if not program_path.exists():
        raise SystemExit(f"Program file not found: {program_path}")

    wrapper_path = resolve_wrapper_path(args.claude_wrapper)
    if not wrapper_path.exists():
        raise SystemExit(f"Claude wrapper not found: {wrapper_path}")


def summarize_contract(args: argparse.Namespace) -> str:
    """Return a human-readable summary of the planned run contract."""
    current_state = load_run_state(args.state_file)
    continuation_manifest_path = resolve_continuation_manifest_path(args.continuation_manifest)
    continuation_manifest = load_continuation_manifest(continuation_manifest_path)
    continuation_baseline = continuation_manifest.get("current_baseline") if continuation_manifest else None
    next_experiment = continuation_manifest.get("next_recommended_experiment") if continuation_manifest else None
    failed_count = len(continuation_manifest.get("failed_branches", [])) if continuation_manifest else 0
    return "\n".join(
        [
            "Claude Code autoresearch runner scaffold",
            f"iterations={args.iterations}",
            f"strategy={args.strategy}",
            f"state_file={args.state_file}",
            f"iteration_root={args.iteration_root}",
            f"program={args.program}",
            f"results_file={args.results_file}",
            f"notes_dir={args.notes_dir}",
            f"recent_notes_limit={args.recent_notes_limit}",
            f"claude_wrapper={args.claude_wrapper}",
            f"target_score={args.target_score}",
            f"max_no_improve={args.max_no_improve}",
            f"continuation_manifest={continuation_manifest_path}",
            f"continuation_manifest_exists={continuation_manifest is not None}",
            (
                f"continuation_current_baseline={continuation_baseline['title']}"
                if continuation_baseline
                else "continuation_current_baseline=None"
            ),
            f"continuation_failed_branches={failed_count}",
            f"continuation_next_experiment={next_experiment}",
            f"dry_run={args.dry_run}",
            f"state_status={current_state['status']}",
            f"state_current_iteration={current_state['current_iteration']}",
        ]
    )


def execute_dry_run(args: argparse.Namespace) -> int:
    """Write a real machine-first artifact bundle for one dry-run iteration."""
    state = load_or_initialize_run(args)
    save_run_state(args.state_file, state)

    continuation_manifest_path = resolve_continuation_manifest_path(args.continuation_manifest)
    continuation_manifest = load_continuation_manifest(continuation_manifest_path) or {}
    run_root = get_run_root(args.iteration_root, state["run_id"])
    run_root.mkdir(parents=True, exist_ok=True)

    iteration_number = state["current_iteration"] + 1
    iteration_dir = run_root / f"iteration-{iteration_number:04d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)

    context = assemble_iteration_context(state, args, iteration_number)
    context_json_path, context_md_path = write_context_bundle(iteration_dir, context)
    snapshot = create_strategy_snapshot(args.strategy, iteration_number, run_root)

    wrapper_command = [
        str(resolve_wrapper_path(args.claude_wrapper)),
        str(iteration_number),
        "--program",
        str(resolve_program_path(args.program)),
        "--strategy",
        str(resolve_strategy_path(args.strategy)),
        "--state-file",
        str(resolve_state_path(args.state_file)),
        "--output-dir",
        str(run_root),
        "--dry-run",
    ]
    wrapper_result = run_wrapper(wrapper_command)
    claude_stdout_path = write_placeholder(
        iteration_dir / "claude.stdout.log",
        wrapper_result.stdout or "dry-run wrapper produced no stdout",
    )
    claude_stderr_path = write_placeholder(
        iteration_dir / "claude.stderr.log",
        wrapper_result.stderr or "dry-run wrapper produced no stderr",
    )
    backtest_stdout_path = write_placeholder(
        iteration_dir / "backtest.stdout.log",
        "dry-run placeholder: no evaluator executed",
    )
    backtest_stderr_path = write_placeholder(
        iteration_dir / "backtest.stderr.log",
        "dry-run placeholder: no evaluator stderr",
    )

    decision = build_placeholder_decision("dry_run")
    decision_path = write_json(iteration_dir / "decision.json", decision)
    summary = build_round_summary("dry_run")
    artifact_paths = {
        "context_json": str(context_json_path),
        "context_md": str(context_md_path),
        "claude_prompt": str(iteration_dir / "claude_prompt.md"),
        "claude_stdout": str(claude_stdout_path),
        "claude_stderr": str(claude_stderr_path),
        "backtest_stdout": str(backtest_stdout_path),
        "backtest_stderr": str(backtest_stderr_path),
        "decision": str(decision_path),
        "snapshot": snapshot["snapshot_path"],
    }
    iteration_record = {
        "run_id": state["run_id"],
        "iteration_number": iteration_number,
        "artifact_status": "simulated",
        "execution_mode": "dry_run",
        "summary": summary,
        "decision": decision,
        "snapshot": snapshot,
        "continuation_context": {
            "manifest_path": str(continuation_manifest_path),
            "current_baseline": continuation_manifest.get("current_baseline"),
            "next_recommended_experiment": continuation_manifest.get("next_recommended_experiment"),
        },
        "sources": context["sources"],
        "artifact_paths": artifact_paths,
    }
    iteration_record_path = write_json(iteration_dir / "iteration_record.json", iteration_record)
    artifact_paths["iteration_record"] = str(iteration_record_path)
    note_draft_path = write_text(
        iteration_dir / "experiment_note_draft.md",
        render_experiment_note_draft(iteration_record),
    )
    artifact_paths["experiment_note_draft"] = str(note_draft_path)
    write_json(iteration_record_path, iteration_record)

    print(summarize_contract(args))
    print(f"artifact_run_root={run_root}")
    print(f"artifact_iteration_dir={iteration_dir}")
    print(f"artifact_iteration_record={iteration_record_path}")
    print(f"artifact_note_draft={note_draft_path}")
    return 0


def main() -> int:
    """Parse arguments and expose the scaffold contract."""
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args)

    if args.dry_run:
        return execute_dry_run(args)

    raise SystemExit(
        "Autoresearch runner scaffold created. Detailed loop behavior will be implemented in follow-up tasks."
    )


if __name__ == "__main__":
    raise SystemExit(main())
