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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.memory.idea_keep_revert import decide_keep_revert


DEFAULT_STATE_PATH = Path("experiments/autoresearch_state.json")
DEFAULT_STRATEGY_PATH = Path("src/strategies/active_strategy.py")
DEFAULT_ITERATION_ROOT = Path("experiments/iterations")
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
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def resolve_strategy_path(strategy_file: str | Path) -> Path:
    """Resolve the strategy-under-iteration path."""
    return Path(strategy_file).expanduser()


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
        "created_at": datetime.now(timezone.utc).isoformat(),
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
    restored_snapshot["restored_at"] = datetime.now(timezone.utc).isoformat()
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
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate the minimum argument contract before deeper implementation exists."""
    if args.iterations <= 0:
        raise SystemExit("--iterations must be greater than 0.")
    if args.max_no_improve is not None and args.max_no_improve < 0:
        raise SystemExit("--max-no-improve must be 0 or greater.")


def summarize_contract(args: argparse.Namespace) -> str:
    """Return a human-readable summary of the planned run contract."""
    current_state = load_run_state(args.state_file)
    return "\n".join(
        [
            "Claude Code autoresearch runner scaffold",
            f"iterations={args.iterations}",
            f"strategy={args.strategy}",
            f"state_file={args.state_file}",
            f"iteration_root={args.iteration_root}",
            f"target_score={args.target_score}",
            f"max_no_improve={args.max_no_improve}",
            f"dry_run={args.dry_run}",
            f"state_status={current_state['status']}",
            f"state_current_iteration={current_state['current_iteration']}",
        ]
    )


def main() -> int:
    """Parse arguments and expose the scaffold contract."""
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args)
    print(summarize_contract(args))

    if args.dry_run:
        return 0

    raise SystemExit(
        "Autoresearch runner scaffold created. Detailed loop behavior will be implemented in follow-up tasks."
    )


if __name__ == "__main__":
    raise SystemExit(main())
