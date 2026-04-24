"""Thin launcher for selecting the repo or OMX autoresearch lane."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_RUNNER = REPO_ROOT / "scripts" / "autoresearch_runner.py"


def run_command(command: Sequence[str], cwd: str | Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command and capture text output."""
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd is not None else None,
        check=False,
        capture_output=True,
        text=True,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the lane-selection CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Route autoresearch to the OMX runtime lane or the repo Claude runner "
            "under the shared mandatory two-hook strategy contract."
        ),
    )
    parser.add_argument(
        "--lane",
        choices=("omx", "claude"),
        default="omx",
        help="Which executor lane to launch. Both lanes share the mandatory select_universe/generate_signals contract.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected command without executing it.",
    )
    return parser


def build_command(lane: str, passthrough: Sequence[str]) -> list[str]:
    """Build the concrete process command for the selected lane."""
    if lane == "claude":
        return [sys.executable, str(REPO_RUNNER), *passthrough]
    return ["omx", "autoresearch", *passthrough]


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, select a lane, and execute or print the command."""
    parser = build_parser()
    args, passthrough = parser.parse_known_args(argv)

    command = build_command(args.lane, passthrough)

    if args.dry_run:
        print(f"lane={args.lane}")
        print("strategy_contract=select_universe(daily_data),generate_signals(minute_data)")
        print(f"command={shlex.join(command)}")
        return 0

    result = run_command(command, cwd=REPO_ROOT)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
