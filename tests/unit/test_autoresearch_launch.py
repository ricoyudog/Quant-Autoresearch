from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "autoresearch_launch",
        Path("scripts/autoresearch_launch.py"),
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_lane_targets_omx_autoresearch(monkeypatch, capsys):
    launcher = _load_module()
    calls = []

    def fake_run(command, cwd=None):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(launcher, "run_command", fake_run)

    exit_code = launcher.main(["--dry-run"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert calls == []
    assert "lane=omx" in output
    assert "omx autoresearch" in output


def test_explicit_claude_lane_targets_repo_runner(monkeypatch, capsys):
    launcher = _load_module()
    calls = []

    def fake_run(command, cwd=None):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(launcher, "run_command", fake_run)

    exit_code = launcher.main(["--lane", "claude", "--dry-run", "--iterations", "3"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert calls == []
    assert "lane=claude" in output
    assert "scripts/autoresearch_runner.py" in output
    assert "--iterations 3" in output


def test_non_dry_run_executes_selected_lane(monkeypatch):
    launcher = _load_module()
    calls = []

    def fake_run(command, cwd=None):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 7)

    monkeypatch.setattr(launcher, "run_command", fake_run)

    exit_code = launcher.main(["--lane", "omx", "--topic", "minute alpha"])

    assert exit_code == 7
    assert calls[0][0][:2] == ["omx", "autoresearch"]
    assert "--topic" in calls[0][0]
    assert "minute alpha" in calls[0][0]


def test_non_dry_run_claude_lane_uses_repo_root_and_streams_output(monkeypatch, capsys):
    launcher = _load_module()
    calls = []

    def fake_run(command, cwd=None):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 0, stdout="runner ok\n", stderr="warn\n")

    monkeypatch.setattr(launcher, "run_command", fake_run)

    exit_code = launcher.main(["--lane", "claude", "--status-only"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls == [([launcher.sys.executable, str(launcher.REPO_RUNNER), "--status-only"], launcher.REPO_ROOT)]
    assert captured.out == "runner ok\n"
    assert captured.err == "warn\n"
