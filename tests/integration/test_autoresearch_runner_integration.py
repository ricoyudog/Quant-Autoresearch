from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess


def _load_runner_module():
    spec = importlib.util.spec_from_file_location(
        "autoresearch_runner",
        Path("scripts/autoresearch_runner.py"),
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _build_args(tmp_path: Path) -> argparse.Namespace:
    strategy_path = tmp_path / "active_strategy.py"
    strategy_path.write_text("VALUE = 0\n")

    program_path = tmp_path / "program.md"
    program_path.write_text("# Program\n\nKeep edits bounded.\n")

    results_path = tmp_path / "results.tsv"
    results_path.write_text(
        "commit\tscore\tbaseline_sharpe\tstatus\tdescription\n"
        "working\t0.500000\t0.400000\tpending\tbaseline\n"
    )

    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "idea.md").write_text("# Idea\n\nAudit every round.\n")

    return argparse.Namespace(
        iterations=1,
        strategy=str(strategy_path),
        state_file=str(tmp_path / "autoresearch_state.json"),
        iteration_root=str(tmp_path / "iterations"),
        target_score=None,
        max_no_improve=None,
        dry_run=False,
        program=str(program_path),
        results_file=str(results_path),
        notes_dir=str(notes_dir),
        recent_notes_limit=3,
        claude_wrapper="scripts/run_claude_iteration.sh",
        status_only=False,
    )


def _command_arg(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


def test_run_claude_iteration_dry_run_writes_prompt_and_reports_contract(tmp_path):
    program_path = tmp_path / "program.md"
    strategy_path = tmp_path / "active_strategy.py"
    state_path = tmp_path / "autoresearch_state.json"
    output_root = tmp_path / "iterations"
    context_path = tmp_path / "context.md"

    program_path.write_text("# Program\n")
    strategy_path.write_text("VALUE = 0\n")
    state_path.write_text("{}\n")
    context_path.write_text("# Context\n\nUse prior notes.\n")

    result = subprocess.run(
        [
            "bash",
            "scripts/run_claude_iteration.sh",
            "3",
            "--program",
            str(program_path),
            "--strategy",
            str(strategy_path),
            "--state-file",
            str(state_path),
            "--output-dir",
            str(output_root),
            "--context-file",
            str(context_path),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    prompt_path = output_root / "iteration-0003" / "claude_prompt.md"

    assert result.returncode == 0
    assert "status=dry_run" in result.stdout
    assert f"context_file={context_path}" in result.stdout
    assert prompt_path.exists()
    prompt_text = prompt_path.read_text()
    assert "Context Bundle:" in prompt_text
    assert "Use prior notes." in prompt_text


def test_run_claude_iteration_maps_rate_limit_to_stable_exit_code(tmp_path):
    program_path = tmp_path / "program.md"
    strategy_path = tmp_path / "active_strategy.py"
    state_path = tmp_path / "autoresearch_state.json"
    output_root = tmp_path / "iterations"
    fake_claude = tmp_path / "fake_claude.sh"

    program_path.write_text("# Program\n")
    strategy_path.write_text("VALUE = 0\n")
    state_path.write_text("{}\n")
    fake_claude.write_text(
        "#!/usr/bin/env bash\n"
        "cat >/dev/null\n"
        "echo 'API Error: 429 {\"error\":{\"code\":\"1302\",\"message\":\"Rate limit reached for requests\"}}'\n"
        "exit 1\n"
    )
    fake_claude.chmod(0o755)

    result = subprocess.run(
        [
            "bash",
            "scripts/run_claude_iteration.sh",
            "1",
            "--program",
            str(program_path),
            "--strategy",
            str(strategy_path),
            "--state-file",
            str(state_path),
            "--output-dir",
            str(output_root),
            "--claude-bin",
            str(fake_claude),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 75
    assert "API Error: 429" in result.stdout


def test_run_claude_iteration_success_keeps_stdout_clean_for_runner(tmp_path):
    program_path = tmp_path / "program.md"
    strategy_path = tmp_path / "active_strategy.py"
    state_path = tmp_path / "autoresearch_state.json"
    output_root = tmp_path / "iterations"
    fake_claude = tmp_path / "fake_claude_success.sh"

    program_path.write_text("# Program\n")
    strategy_path.write_text("VALUE = 0\n")
    state_path.write_text("{}\n")
    fake_claude.write_text(
        "#!/usr/bin/env bash\n"
        "cat >/dev/null\n"
        "echo '{\"hypothesis\":\"retry safe\",\"strategy_change_summary\":\"kept clean json\"}'\n"
        "exit 0\n"
    )
    fake_claude.chmod(0o755)

    result = subprocess.run(
        [
            "bash",
            "scripts/run_claude_iteration.sh",
            "1",
            "--program",
            str(program_path),
            "--strategy",
            str(strategy_path),
            "--state-file",
            str(state_path),
            "--output-dir",
            str(output_root),
            "--claude-bin",
            str(fake_claude),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == '{"hypothesis":"retry safe","strategy_change_summary":"kept clean json"}'
    assert "Claude Code iteration wrapper" in result.stderr


def test_run_claude_iteration_resolves_default_relative_paths_from_scripts_dir(tmp_path):
    repo_root = Path.cwd()
    program_path = repo_root / "program.md"
    strategy_path = repo_root / "src" / "strategies" / "active_strategy.py"
    state_path = repo_root / "experiments" / "tmp_wrapper_autoresearch_state.json"
    output_root = repo_root / "experiments" / "tmp_wrapper_iterations"

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{}\n")

    repo_relative_program = Path("program.md")
    repo_relative_strategy = Path("src/strategies/active_strategy.py")
    repo_relative_state = Path("experiments/tmp_wrapper_autoresearch_state.json")
    repo_relative_output = Path("experiments/tmp_wrapper_iterations")

    result = subprocess.run(
        [
            "bash",
            "run_claude_iteration.sh",
            "1",
            "--program",
            str(repo_relative_program),
            "--strategy",
            str(repo_relative_strategy),
            "--state-file",
            str(repo_relative_state),
            "--output-dir",
            str(repo_relative_output),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd() / "scripts",
    )

    prompt_path = output_root / "iteration-0001" / "claude_prompt.md"

    try:
        assert result.returncode == 0
        assert "status=dry_run" in result.stdout
        assert prompt_path.exists()
    finally:
        shutil.rmtree(output_root, ignore_errors=True)
        state_path.unlink(missing_ok=True)


def test_run_autoresearch_writes_iteration_audit_artifacts(tmp_path, monkeypatch):
    runner = _load_runner_module()
    args = _build_args(tmp_path)

    def fake_run_command(command, cwd=None, env=None):
        if "run_claude_iteration.sh" in command:
            output_dir = Path(_command_arg(command, "--output-dir"))
            round_dir = output_dir / "iteration-0001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "claude_prompt.md").write_text("prompt")
            Path(_command_arg(command, "--strategy")).write_text("VALUE = 1\n")
            stdout = json.dumps(
                {
                    "hypothesis": "Preserve a filesystem audit trail",
                    "strategy_change_summary": "Set VALUE to 1",
                }
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        stdout = (
            "SCORE: 0.77\n"
            "BASELINE_SHARPE: 0.50\n"
            "DEFLATED_SR: 0.74\n"
            "NW_SHARPE_BIAS: 0.06\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    runner.run_autoresearch(args)

    state = json.loads(Path(args.state_file).read_text())
    round_dir = Path(args.iteration_root) / state["run_id"] / "iteration-0001"
    record = json.loads((round_dir / "iteration_record.json").read_text())

    assert (round_dir / "context.md").exists()
    assert (round_dir / "context.json").exists()
    assert (round_dir / "claude.stdout.log").exists()
    assert (round_dir / "backtest.stdout.log").exists()
    assert record["decision"] == "keep"
    assert record["artifact_paths"]["claude_stdout"].endswith("claude.stdout.log")
