"""Claude Code autoresearch outer-loop runner.

This script keeps Claude Code outside the repository runtime while the runner
owns iteration control, deterministic evaluation, keep/revert behavior, and
resume state.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.vault import get_vault_paths
from src.memory.idea_keep_revert import decide_keep_revert
from src.memory.experiment_memory import CONTINUATION_MANIFEST_PATH, load_continuation_manifest
from src.memory.iteration_artifacts import render_experiment_note_draft, write_text


DEFAULT_STATE_PATH = Path("experiments/autoresearch_state.json")
DEFAULT_STRATEGY_PATH = Path("src/strategies/active_strategy.py")
DEFAULT_ITERATION_ROOT = Path("experiments/iterations")
DEFAULT_CONTINUATION_MANIFEST_PATH = CONTINUATION_MANIFEST_PATH
DEFAULT_PROGRAM_PATH = Path("program.md")
DEFAULT_RESULTS_PATH = Path("experiments/results.tsv")
DEFAULT_NOTES_DIR = get_vault_paths().experiments
DEFAULT_CLAUDE_WRAPPER = Path("scripts/run_claude_iteration.sh")
CLAUDE_RATE_LIMIT_EXIT_CODE = 75
CLAUDE_MAX_RETRY_ATTEMPTS = 3
CLAUDE_RETRY_BASE_DELAY_SECONDS = 5
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

CommandRunner = Callable[
    [list[str], str | Path | None, dict[str, str] | None],
    subprocess.CompletedProcess[str],
]


def resolve_state_path(state_file: str | Path) -> Path:
    """Resolve the persisted run-state path."""
    return Path(state_file).expanduser()


def resolve_strategy_path(strategy_file: str | Path) -> Path:
    """Resolve the strategy-under-iteration path."""
    return Path(strategy_file).expanduser()


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
    """Resolve the recent-notes directory."""
    return Path(notes_dir).expanduser()


def resolve_wrapper_path(wrapper_path: str | Path) -> Path:
    """Resolve the Claude wrapper path for validation only."""
    return Path(wrapper_path).expanduser()


def resolve_continuation_manifest_path(manifest_file: str | Path) -> Path:
    """Resolve the continuation manifest path for repo-local research memory."""
    return Path(manifest_file).expanduser()


def build_continuation_context(manifest_file: str | Path) -> dict[str, Any]:
    """Load the current continuation-manifest context for iteration artifacts."""
    manifest_path = resolve_continuation_manifest_path(manifest_file)
    manifest = load_continuation_manifest(manifest_path) or {}
    return {
        "manifest_path": str(manifest_path),
        "current_baseline": manifest.get("current_baseline"),
        "next_recommended_experiment": manifest.get("next_recommended_experiment"),
        "failed_branches": manifest.get("failed_branches") or [],
    }


def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 form."""
    return datetime.now(timezone.utc).isoformat()


def default_run_state() -> dict[str, Any]:
    """Return a fresh copy of the default persisted run-state payload."""
    return dict(RUN_STATE_TEMPLATE)


def load_run_state(state_file: str | Path) -> dict[str, Any]:
    """Load persisted run state, filling missing keys from the default template."""
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


def run_command(
    command: list[str],
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command with captured text output."""
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def resolve_command_runner(runner: CommandRunner | None = None) -> CommandRunner:
    """Return the injected command runner or the live shell runner."""
    return runner or run_command


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
    """Read a file excerpt safely for prompt assembly."""
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

    lines = [line.rstrip("\n") for line in results_path.read_text(encoding="utf-8", errors="ignore").splitlines()]
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
    """Assemble the repository context bundle passed into a round."""
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
    """Render the iteration context bundle as operator-readable markdown."""
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
    context_json_path = iteration_dir / "context.json"
    context_md_path = iteration_dir / "context.md"
    context_json_path.write_text(json.dumps(context, indent=2) + "\n")
    context_md_path.write_text(render_context_markdown(context))
    return context_json_path, context_md_path


def parse_iteration_summary(output: str) -> dict[str, Any]:
    """Parse Claude's round summary, preferring JSON when available."""
    cleaned = output.strip()
    if not cleaned:
        return {
            "hypothesis": "No hypothesis reported.",
            "strategy_change_summary": "No strategy change summary reported.",
            "files_touched": [],
        }

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        hypothesis = lines[0] if lines else "No hypothesis reported."
        summary = lines[1] if len(lines) > 1 else hypothesis
        return {
            "hypothesis": hypothesis,
            "strategy_change_summary": summary,
            "files_touched": [],
        }

    if not isinstance(payload, dict):
        return {
            "hypothesis": str(payload),
            "strategy_change_summary": str(payload),
            "files_touched": [],
        }

    return {
        "hypothesis": str(payload.get("hypothesis") or "No hypothesis reported."),
        "strategy_change_summary": str(
            payload.get("strategy_change_summary")
            or payload.get("change_summary")
            or "No strategy change summary reported."
        ),
        "files_touched": payload.get("files_touched") or [],
        "notes": payload.get("notes"),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the outer-loop runner."""
    parser = argparse.ArgumentParser(
        description="Run a bounded Claude Code-driven autoresearch loop.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Maximum number of autoresearch rounds. Required unless --status-only is used.",
    )
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
        help="Directory used for per-run artifacts and strategy snapshots.",
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
        help="Directory containing recent experiment notes for context assembly.",
    )
    parser.add_argument(
        "--recent-notes-limit",
        type=int,
        default=3,
        help="Maximum number of recent note files to include in a round context bundle.",
    )
    parser.add_argument(
        "--claude-wrapper",
        default=str(DEFAULT_CLAUDE_WRAPPER),
        help="Shell wrapper used to invoke one Claude Code iteration.",
    )
    parser.add_argument(
        "--continuation-manifest",
        default=str(DEFAULT_CONTINUATION_MANIFEST_PATH),
        help="Path to the canonical continuation manifest for current research memory.",
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
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the planned runner contract without executing rounds.",
    )
    parser.add_argument(
        "--status-only",
        action="store_true",
        help="Print the current run-state summary without executing additional rounds.",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate the runner argument contract."""
    if args.status_only:
        return

    if args.iterations is None:
        raise SystemExit("--iterations is required unless --status-only is used.")
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
    continuation_manifest_path = resolve_continuation_manifest_path(getattr(args, "continuation_manifest", DEFAULT_CONTINUATION_MANIFEST_PATH))
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
            f"continuation_manifest={continuation_manifest_path}",
            f"continuation_manifest_exists={continuation_manifest is not None}",
            (
                f"continuation_current_baseline={continuation_baseline['title']}"
                if continuation_baseline
                else "continuation_current_baseline=None"
            ),
            f"continuation_failed_branches={failed_count}",
            f"continuation_next_experiment={next_experiment}",
            f"target_score={args.target_score}",
            f"max_no_improve={args.max_no_improve}",
            f"dry_run={args.dry_run}",
            f"state_status={current_state['status']}",
            f"state_current_iteration={current_state['current_iteration']}",
        ]
    )


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

    state["status"] = "running"
    state["stop_reason"] = None
    state["iteration_budget"] = args.iterations
    if args.target_score is not None or state.get("target_score") is None:
        state["target_score"] = args.target_score
    if args.max_no_improve is not None or state.get("max_no_improve") is None:
        state["max_no_improve"] = args.max_no_improve
    state["strategy_path"] = str(resolve_strategy_path(args.strategy))
    state["iteration_root"] = str(get_run_root(args.iteration_root, state["run_id"]))
    return state


def restore_best_strategy_reference(state: dict[str, Any], strategy_file: str | Path) -> None:
    """Restore the retained best strategy before resuming additional rounds."""
    best_reference = state.get("best_strategy_reference")
    if not best_reference:
        return

    best_reference_path = Path(best_reference).expanduser()
    if not best_reference_path.exists():
        return

    strategy_path = resolve_strategy_path(strategy_file)
    target_parent = strategy_path.parent
    target_parent.mkdir(parents=True, exist_ok=True)
    if not strategy_path.exists() or strategy_path.read_text() != best_reference_path.read_text():
        shutil.copy2(best_reference_path, strategy_path)


def should_stop(state: dict[str, Any]) -> tuple[bool, str | None]:
    """Return whether the run should stop and the reason if it should."""
    best_score = state.get("best_score")
    target_score = state.get("target_score")
    max_no_improve = state.get("max_no_improve")
    no_improve_streak = int(state.get("no_improve_streak") or 0)

    if target_score is not None and best_score is not None and best_score >= target_score:
        return True, "target_score_reached"
    if max_no_improve is not None and no_improve_streak > 0 and no_improve_streak >= max_no_improve:
        return True, "max_no_improve_reached"
    if state.get("current_iteration", 0) >= state.get("iteration_budget", 0):
        return True, "iteration_budget_reached"
    return False, None


def invoke_claude_iteration(
    iteration_number: int,
    args: argparse.Namespace,
    run_root: Path,
    context_file: Path,
    runner: CommandRunner | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the shell wrapper for one Claude Code iteration."""
    command_runner = resolve_command_runner(runner)
    command = [
        "bash",
        Path(args.claude_wrapper).name,
        str(iteration_number),
        "--program",
        str(resolve_program_path(args.program)),
        "--strategy",
        str(resolve_strategy_path(args.strategy)),
        "--state-file",
        str(resolve_state_path(args.state_file)),
        "--output-dir",
        str(run_root),
        "--context-file",
        str(context_file),
    ]
    return command_runner(command, cwd=resolve_wrapper_path(args.claude_wrapper).parent)


def get_process_output(result: subprocess.CompletedProcess[str]) -> str:
    """Combine stdout/stderr into one searchable error string."""
    return "\n".join(part for part in [result.stdout, result.stderr] if part).strip()


def is_retryable_claude_failure(message: str, returncode: int | None = None) -> bool:
    """Detect transient Claude invocation failures that should be retried."""
    if returncode == CLAUDE_RATE_LIMIT_EXIT_CODE:
        return True
    normalized = (message or "").lower()
    return (
        "api error: 429" in normalized
        or "rate limit reached" in normalized
        or '"code":"1302"' in normalized
        or '"code": "1302"' in normalized
    )


def invoke_claude_iteration_with_retries(
    iteration_number: int,
    args: argparse.Namespace,
    run_root: Path,
    context_file: Path,
    runner: CommandRunner | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> tuple[subprocess.CompletedProcess[str], int, list[int], bool]:
    """Invoke Claude, retrying transient rate-limit failures with linear backoff."""
    delays: list[int] = []
    command_sleep = sleep_fn or time.sleep
    retryable_failure = False

    for attempt in range(1, CLAUDE_MAX_RETRY_ATTEMPTS + 1):
        result = invoke_claude_iteration(
            iteration_number,
            args,
            run_root,
            context_file,
            runner=runner,
        )
        if result.returncode == 0:
            return result, attempt, delays, False

        message = get_process_output(result)
        retryable_failure = is_retryable_claude_failure(message, returncode=result.returncode)
        if not retryable_failure or attempt == CLAUDE_MAX_RETRY_ATTEMPTS:
            return result, attempt, delays, retryable_failure

        delay_seconds = CLAUDE_RETRY_BASE_DELAY_SECONDS * attempt
        delays.append(delay_seconds)
        command_sleep(delay_seconds)

    return result, CLAUDE_MAX_RETRY_ATTEMPTS, delays, retryable_failure


def run_backtest(
    strategy_file: str | Path,
    runner: CommandRunner | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the deterministic repository backtest for the active strategy."""
    command_runner = resolve_command_runner(runner)
    command = [
        "uv",
        "run",
        "python",
        "cli.py",
        "backtest",
        "--strategy",
        str(resolve_strategy_path(strategy_file)),
    ]
    return command_runner(command, cwd=REPO_ROOT)


def build_failed_decision(
    reason: str,
    previous_best: float | None,
    message: str | None = None,
) -> dict[str, Any]:
    """Build a normalized failed decision payload."""
    reasons = [reason]
    if message:
        reasons.append(message)
    return {
        "decision": "failed",
        "reasons": reasons,
        "score": None,
        "baseline_sharpe": None,
        "previous_best": previous_best,
    }


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    """Write JSON with a stable trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def execute_dry_run(args: argparse.Namespace) -> int:
    """Write a real machine-first artifact bundle for one dry-run iteration."""
    state = load_or_initialize_run(args)
    state["status"] = "pending"
    save_run_state(args.state_file, state)

    continuation_context = build_continuation_context(getattr(args, "continuation_manifest", DEFAULT_CONTINUATION_MANIFEST_PATH))
    run_root = get_run_root(args.iteration_root, state["run_id"])
    run_root.mkdir(parents=True, exist_ok=True)

    iteration_number = int(state["current_iteration"]) + 1
    iteration_dir = run_root / f"iteration-{iteration_number:04d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)

    context = assemble_iteration_context(state, args, iteration_number)
    context_json_path, context_md_path = write_context_bundle(iteration_dir, context)
    snapshot = create_strategy_snapshot(args.strategy, iteration_number, run_root)

    wrapper_command = [
        "bash",
        Path(args.claude_wrapper).name,
        str(iteration_number),
        "--program",
        str(resolve_program_path(args.program)),
        "--strategy",
        str(resolve_strategy_path(args.strategy)),
        "--state-file",
        str(resolve_state_path(args.state_file)),
        "--output-dir",
        str(run_root),
        "--context-file",
        str(context_md_path),
        "--dry-run",
    ]
    wrapper_result = run_command(wrapper_command, cwd=resolve_wrapper_path(args.claude_wrapper).parent)

    claude_stdout_path = iteration_dir / "claude.stdout.log"
    claude_stderr_path = iteration_dir / "claude.stderr.log"
    backtest_stdout_path = iteration_dir / "backtest.stdout.log"
    backtest_stderr_path = iteration_dir / "backtest.stderr.log"
    claude_stdout_path.write_text(wrapper_result.stdout or "")
    claude_stderr_path.write_text(wrapper_result.stderr or "")
    backtest_stdout_path.write_text("dry-run placeholder: no evaluator executed\n")
    backtest_stderr_path.write_text("dry-run placeholder: no evaluator stderr\n")

    summary = {
        "hypothesis": "Dry-run artifact generation only; no live hypothesis was proposed.",
        "strategy_change_summary": "No strategy changes were attempted because this run only generated audit artifacts.",
        "files_touched": [],
    }
    decision = {
        "decision": "pending_evaluation",
        "reasons": ["no_live_evaluator_output"],
        "score": None,
        "baseline_sharpe": None,
        "previous_best": state.get("best_score"),
        "validation_status": "candidate",
        "artifact_status": "simulated",
        "execution_mode": "dry_run",
        "bounded_result": {},
        "unrestricted_result": {},
        "turnover_fee_lesson": "TODO: evaluate fee / turnover impact after a real run.",
    }
    decision_path = write_json(iteration_dir / "decision.json", decision)
    iteration_record = {
        "run_id": state["run_id"],
        "iteration_number": iteration_number,
        "artifact_status": "simulated",
        "execution_mode": "dry_run",
        "summary": summary,
        "hypothesis": summary["hypothesis"],
        "strategy_change_summary": summary["strategy_change_summary"],
        "files_touched": [],
        "decision": decision,
        "decision_outcome": decision["decision"],
        "decision_reason": decision["reasons"],
        "decision_payload": decision,
        "snapshot": snapshot,
        "continuation_context": continuation_context,
        "sources": context["sources"],
        "artifact_paths": {
            "context_json": str(context_json_path),
            "context_markdown": str(context_md_path),
            "claude_prompt": str(iteration_dir / "claude_prompt.md"),
            "claude_stdout": str(claude_stdout_path),
            "claude_stderr": str(claude_stderr_path),
            "backtest_stdout": str(backtest_stdout_path),
            "backtest_stderr": str(backtest_stderr_path),
            "decision": str(decision_path),
            "snapshot": snapshot["snapshot_path"],
        },
    }
    iteration_record_path = write_iteration_record(iteration_dir, iteration_record)
    iteration_record["artifact_paths"]["iteration_record"] = str(iteration_record_path)
    note_draft_path = write_text(iteration_dir / "experiment_note_draft.md", render_experiment_note_draft({
        "run_id": state["run_id"],
        "iteration_number": iteration_number,
        "artifact_status": "simulated",
        "execution_mode": "dry_run",
        "summary": summary,
        "decision": decision,
        "continuation_context": continuation_context,
        "artifact_paths": {**iteration_record["artifact_paths"], "iteration_record": str(iteration_record_path)},
    }))
    iteration_record["artifact_paths"]["experiment_note_draft"] = str(note_draft_path)
    write_json(iteration_record_path, iteration_record)

    print(summarize_contract(args))
    print(f"artifact_run_root={run_root}")
    print(f"artifact_iteration_dir={iteration_dir}")
    print(f"artifact_iteration_record={iteration_record_path}")
    print(f"artifact_note_draft={note_draft_path}")
    return 0


def apply_decision(
    decision: dict[str, Any],
    state: dict[str, Any],
    snapshot: dict[str, Any],
    strategy_file: str | Path,
    run_root: Path,
    iteration_number: int,
) -> dict[str, Any]:
    """Apply keep/revert behavior and update the persisted run state."""
    updated_snapshot = dict(snapshot)
    decision_type = decision["decision"]

    if decision_type == "keep":
        retained_dir = run_root / "retained"
        retained_dir.mkdir(parents=True, exist_ok=True)
        retained_path = retained_dir / f"iteration-{iteration_number:04d}-{Path(strategy_file).name}"
        shutil.copy2(resolve_strategy_path(strategy_file), retained_path)
        state["best_score"] = decision.get("score")
        state["best_iteration"] = iteration_number
        state["best_strategy_reference"] = str(retained_path)
        state["no_improve_streak"] = 0
        state["last_error"] = None
        updated_snapshot["retained_path"] = str(retained_path)
        return updated_snapshot

    updated_snapshot = restore_strategy_snapshot(snapshot, strategy_file)
    state["no_improve_streak"] = int(state.get("no_improve_streak") or 0) + 1
    if decision_type == "failed":
        state["last_error"] = "; ".join(str(reason) for reason in decision.get("reasons", []))
    else:
        state["last_error"] = None
    return updated_snapshot


def write_iteration_record(iteration_dir: Path, record: dict[str, Any]) -> Path:
    """Persist the normalized audit record for a completed iteration."""
    return write_json(iteration_dir / "iteration_record.json", record)


def summarize_run(state: dict[str, Any]) -> str:
    """Render a concise operator-facing summary of the current run."""
    return "\n".join(
        [
            f"run_id={state.get('run_id')}",
            f"status={state.get('status')}",
            f"current_iteration={state.get('current_iteration')}",
            f"iteration_budget={state.get('iteration_budget')}",
            f"best_score={state.get('best_score')}",
            f"best_iteration={state.get('best_iteration')}",
            f"no_improve_streak={state.get('no_improve_streak')}",
            f"stop_reason={state.get('stop_reason')}",
            f"last_decision={state.get('last_decision')}",
        ]
    )


def run_autoresearch(args: argparse.Namespace, runner: CommandRunner | None = None) -> int:
    """Execute the bounded multi-round autoresearch loop."""
    command_runner = resolve_command_runner(runner)
    state = load_or_initialize_run(args)
    continuation_context = build_continuation_context(getattr(args, "continuation_manifest", DEFAULT_CONTINUATION_MANIFEST_PATH))
    run_root = get_run_root(args.iteration_root, state["run_id"])
    run_root.mkdir(parents=True, exist_ok=True)

    restore_best_strategy_reference(state, args.strategy)
    save_run_state(args.state_file, state)

    should_end, stop_reason = should_stop(state)
    while not should_end:
        iteration_number = int(state["current_iteration"]) + 1
        iteration_dir = run_root / f"iteration-{iteration_number:04d}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        context = assemble_iteration_context(state, args, iteration_number)
        context_json_path, context_md_path = write_context_bundle(iteration_dir, context)
        snapshot = create_strategy_snapshot(args.strategy, iteration_number, run_root)

        state["active_iteration"] = iteration_number
        save_run_state(args.state_file, state)

        claude_result, claude_attempts, claude_retry_delays, claude_retry_exhausted = invoke_claude_iteration_with_retries(
            iteration_number,
            args,
            run_root,
            context_md_path,
            runner=command_runner,
        )
        claude_stdout_path = iteration_dir / "claude.stdout.log"
        claude_stderr_path = iteration_dir / "claude.stderr.log"
        claude_stdout_path.write_text(claude_result.stdout or "")
        claude_stderr_path.write_text(claude_result.stderr or "")
        iteration_summary = parse_iteration_summary(claude_result.stdout)

        backtest_stdout_path = iteration_dir / "backtest.stdout.log"
        backtest_stderr_path = iteration_dir / "backtest.stderr.log"
        if claude_result.returncode != 0:
            backtest_stdout_path.write_text("")
            backtest_stderr_path.write_text("")
            failure_reason = "claude_iteration_rate_limited" if claude_retry_exhausted else "claude_iteration_failed"
            decision = build_failed_decision(
                failure_reason,
                previous_best=state.get("best_score"),
                message=get_process_output(claude_result) or None,
            )
            evaluation_summary = {
                "status": "failed",
                "error": get_process_output(claude_result) or "Claude iteration failed.",
            }
            decision["validation_status"] = "candidate"
        else:
            backtest_result = run_backtest(args.strategy, runner=command_runner)
            backtest_stdout_path.write_text(backtest_result.stdout or "")
            backtest_stderr_path.write_text(backtest_result.stderr or "")

            if backtest_result.returncode != 0:
                decision = build_failed_decision(
                    "backtest_failed",
                    previous_best=state.get("best_score"),
                    message=(backtest_result.stderr or backtest_result.stdout).strip() or None,
                )
                evaluation_summary = {
                    "status": "failed",
                    "error": (backtest_result.stderr or backtest_result.stdout).strip() or "Backtest command failed.",
                }
                decision["validation_status"] = "candidate"
            else:
                try:
                    evaluation_summary = parse_backtest_metrics(
                        backtest_result.stdout,
                        previous_best=state.get("best_score"),
                    )
                    decision = normalize_backtest_decision(
                        backtest_result.stdout,
                        previous_best=state.get("best_score"),
                    )
                    decision["validation_status"] = "follow_up_required" if decision["decision"] == "keep" else "candidate"
                    decision["bounded_result"] = {k: v for k, v in evaluation_summary.items() if k in {"score", "baseline_sharpe", "naive_sharpe", "nw_sharpe_bias", "deflated_sr"}}
                    decision["unrestricted_result"] = {}
                except ValueError as exc:
                    decision = build_failed_decision(
                        "backtest_output_invalid",
                        previous_best=state.get("best_score"),
                        message=str(exc),
                    )
                    evaluation_summary = {
                        "status": "failed",
                        "error": str(exc),
                    }
                    decision["validation_status"] = "candidate"

        iteration_record = {
            "run_id": state["run_id"],
            "iteration_number": iteration_number,
            "artifact_status": "completed" if claude_result.returncode == 0 else "failed",
            "execution_mode": "live",
            "summary": {
                "hypothesis": iteration_summary["hypothesis"],
                "strategy_change_summary": iteration_summary["strategy_change_summary"],
                "files_touched": iteration_summary.get("files_touched") or [],
            },
            "hypothesis": iteration_summary["hypothesis"],
            "strategy_change_summary": iteration_summary["strategy_change_summary"],
            "files_touched": iteration_summary.get("files_touched") or [],
            "claude_attempts": claude_attempts,
            "claude_retry_delays": claude_retry_delays,
            "evaluation_summary": evaluation_summary,
            "decision": decision["decision"],
            "decision_reason": decision.get("reasons", []),
            "continuation_context": continuation_context,
            "artifact_paths": {
                "context_json": str(context_json_path),
                "context_markdown": str(context_md_path),
                "claude_prompt": str(iteration_dir / "claude_prompt.md"),
                "claude_stdout": str(claude_stdout_path),
                "claude_stderr": str(claude_stderr_path),
                "backtest_stdout": str(backtest_stdout_path),
                "backtest_stderr": str(backtest_stderr_path),
            },
        }

        if claude_retry_exhausted:
            updated_snapshot = restore_strategy_snapshot(snapshot, args.strategy)
            state["active_iteration"] = None
            state["last_decision"] = decision
            state["last_error"] = "; ".join(str(reason) for reason in decision.get("reasons", []))
            state["status"] = "blocked"
            state["stop_reason"] = "claude_rate_limited"
            decision_path = write_json(iteration_dir / "decision.json", decision)
            iteration_record["snapshot"] = updated_snapshot
            iteration_record["artifact_paths"]["decision"] = str(decision_path)
            iteration_record_path = write_iteration_record(iteration_dir, iteration_record)
            iteration_record["artifact_paths"]["iteration_record"] = str(iteration_record_path)
            note_draft_path = write_text(iteration_dir / "experiment_note_draft.md", render_experiment_note_draft({
                "run_id": state["run_id"],
                "iteration_number": iteration_number,
                "artifact_status": iteration_record["artifact_status"],
                "execution_mode": iteration_record["execution_mode"],
                "summary": iteration_record["summary"],
                "decision": decision,
                "continuation_context": continuation_context,
                "artifact_paths": {**iteration_record["artifact_paths"], "iteration_record": str(iteration_record_path)},
            }))
            iteration_record["artifact_paths"]["experiment_note_draft"] = str(note_draft_path)
            write_json(iteration_record_path, iteration_record)
            save_run_state(args.state_file, state)
            return 1

        updated_snapshot = apply_decision(
            decision,
            state,
            snapshot,
            args.strategy,
            run_root,
            iteration_number,
        )
        state["current_iteration"] = iteration_number
        state["last_completed_iteration"] = iteration_number
        state["active_iteration"] = None
        state["last_decision"] = decision
        save_run_state(args.state_file, state)

        decision_path = write_json(iteration_dir / "decision.json", decision)
        iteration_record["snapshot"] = updated_snapshot
        iteration_record["artifact_paths"]["decision"] = str(decision_path)
        iteration_record_path = write_iteration_record(iteration_dir, iteration_record)
        iteration_record["artifact_paths"]["iteration_record"] = str(iteration_record_path)
        note_draft_path = write_text(iteration_dir / "experiment_note_draft.md", render_experiment_note_draft({
            "run_id": state["run_id"],
            "iteration_number": iteration_number,
            "artifact_status": iteration_record["artifact_status"],
            "execution_mode": iteration_record["execution_mode"],
            "summary": iteration_record["summary"],
            "decision": decision,
            "continuation_context": continuation_context,
            "artifact_paths": {**iteration_record["artifact_paths"], "iteration_record": str(iteration_record_path)},
        }))
        iteration_record["artifact_paths"]["experiment_note_draft"] = str(note_draft_path)
        write_json(iteration_record_path, iteration_record)

        should_end, stop_reason = should_stop(state)

    state["status"] = "completed"
    state["stop_reason"] = stop_reason
    state["active_iteration"] = None
    save_run_state(args.state_file, state)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the bounded autoresearch loop."""
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args)

    if args.status_only:
        print(summarize_run(load_run_state(args.state_file)))
        return 0

    if args.dry_run:
        return execute_dry_run(args)

    print(summarize_contract(args))
    result = run_autoresearch(args)
    print(summarize_run(load_run_state(args.state_file)))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
