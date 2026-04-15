from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_autoresearch_runner_dry_run_writes_machine_artifacts(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    strategy_path = tmp_path / "active_strategy.py"
    program_path = tmp_path / "program.md"
    results_path = tmp_path / "results.tsv"
    notes_dir = tmp_path / "notes"
    state_path = tmp_path / "state.json"
    iteration_root = tmp_path / "iterations"
    manifest_path = tmp_path / "manifest.json"

    strategy_path.write_text("class Strategy:\n    pass\n")
    program_path.write_text("# Program\n")
    results_path.write_text("commit\tscore\nabc\t1.0\n")
    notes_dir.mkdir()
    (notes_dir / "2026-04-15-note.md").write_text("# Note\n")
    manifest_path.write_text(
        json.dumps(
            {
                "current_baseline": {
                    "title": "Experiment - Minimum Hold Duration v1",
                    "raw_note_path": "vault/experiments/minimum-hold.md",
                },
                "next_recommended_experiment": "Test a no-trade band",
                "failed_branches": [],
            }
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "autoresearch_runner.py"),
            "--iterations",
            "1",
            "--strategy",
            str(strategy_path),
            "--program",
            str(program_path),
            "--results-file",
            str(results_path),
            "--notes-dir",
            str(notes_dir),
            "--state-file",
            str(state_path),
            "--iteration-root",
            str(iteration_root),
            "--continuation-manifest",
            str(manifest_path),
            "--claude-wrapper",
            str(repo_root / "scripts" / "run_claude_iteration.sh"),
            "--dry-run",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    run_dirs = list(iteration_root.glob("run-*/iteration-0001"))
    assert len(run_dirs) == 1
    iteration_dir = run_dirs[0]

    assert "artifact_iteration_dir=" in result.stdout
    assert (iteration_dir / "claude_prompt.md").exists()
    assert (iteration_dir / "claude.stdout.log").exists()
    assert (iteration_dir / "backtest.stdout.log").exists()
    assert (iteration_dir / "experiment_note_draft.md").exists()

    record = json.loads((iteration_dir / "iteration_record.json").read_text())
    assert record["summary"]["hypothesis"].startswith("Dry-run artifact generation only")
    assert record["decision"]["validation_status"] == "candidate"
    assert record["artifact_status"] == "simulated"
