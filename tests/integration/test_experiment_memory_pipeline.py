from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cli import app

runner = CliRunner()


def _write_note(directory: Path, name: str, frontmatter: str, body: str) -> Path:
    note_path = directory / name
    note_path.write_text(f"---\n{frontmatter}---\n\n{body}")
    return note_path


def test_refresh_research_base_pipeline_preserves_raw_notes_and_writes_manifest(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))

    project_root = vault_root / "quant-autoresearch"
    experiments_dir = project_root / "experiments"
    research_dir = project_root / "research"
    experiments_dir.mkdir(parents=True)
    research_dir.mkdir(parents=True)

    raw_keep = _write_note(
        experiments_dir,
        "2026-04-14-minimum-hold-duration.md",
        "note_type: experiment\n"
        "experiment_slug: minimum-hold-duration\n"
        "status: completed\n"
        "tags:\n"
        "  - experiment\n"
        "  - turnover-reduction\n",
        "# Experiment - Minimum Hold Duration v1\n\n"
        "## Baseline Before This Experiment\n"
        "- Source experiment: [[2026-04-14-turnover-reduction-confirmation-bars]]\n\n"
        "## Outcome\n"
        "### Bounded result\n"
        "- SCORE: `-15.1679`\n"
        "- DRAWDOWN: `-0.5297`\n"
        "- TRADES: `1946`\n\n"
        "### Unrestricted result\n"
        "- SCORE: `-33.0516`\n"
        "- DRAWDOWN: `-0.4929`\n"
        "- TRADES: `14093`\n\n"
        "## Interpretation\n"
        "This remained fee-driven, so reducing churn mattered.\n"
        "This remains a clear keep.\n\n"
        "## Decision\n"
        "Status: **keep as the new baseline candidate**\n\n"
        "## Next Experiment\n"
        "- Test a momentum-strength threshold / no-trade band\n",
    )
    raw_revert = _write_note(
        experiments_dir,
        "2026-04-15-overfit-revert.md",
        "note_type: experiment\n"
        "experiment_slug: overfit-revert\n"
        "status: completed\n"
        "decision: revert\n"
        "tags:\n"
        "  - experiment\n"
        "  - turnover-reduction\n",
        "# Experiment - Overfit Revert\n\n"
        "## Baseline Before This Experiment\n"
        "- Source experiment: [[2026-04-14-minimum-hold-duration]]\n\n"
        "## Decision\n"
        "Status: **revert**\n"
        "Reason:\n"
        "- Score regressed after fees\n",
    )
    raw_failed = _write_note(
        experiments_dir,
        "2026-04-16-invalid-output-failed.md",
        "note_type: experiment\n"
        "experiment_slug: invalid-output-failed\n"
        "status: completed\n"
        "decision: failed\n",
        "# Experiment - Invalid Output Failed\n\n"
        "## Baseline Before This Experiment\n"
        "- Source experiment: [[2026-04-14-minimum-hold-duration]]\n\n"
        "## Decision\n"
        "Status: **failed**\n"
        "Reason:\n"
        "- Backtest output was invalid\n",
    )
    (research_dir / "2026-04-15-daily-research-kickoff.md").write_text(
        "---\nnote_type: research\nresearch_type: daily-kickoff\ndate: '2026-04-15'\n---\n\n# Daily Research Kickoff\n"
    )
    (experiments_dir / "experiment-index.md").write_text("# stale index\n")

    keep_bytes = raw_keep.read_bytes()
    revert_bytes = raw_revert.read_bytes()
    failed_bytes = raw_failed.read_bytes()
    manifest_path = tmp_path / "current_research_base.json"

    result = runner.invoke(app, ["refresh_research_base", "--manifest-path", str(manifest_path)])

    assert result.exit_code == 0
    assert f"Manifest: {manifest_path}" in result.stdout
    assert raw_keep.read_bytes() == keep_bytes
    assert raw_revert.read_bytes() == revert_bytes
    assert raw_failed.read_bytes() == failed_bytes

    manifest = json.loads(manifest_path.read_text())
    index_path = experiments_dir / "experiment-index.md"
    summary_path = experiments_dir / "summaries" / "branch-summary-turnover-reduction.md"
    failed_summary_path = experiments_dir / "summaries" / "branch-summary-invalid-output-failed.md"

    assert manifest["current_baseline"]["title"] == "Experiment - Minimum Hold Duration v1"
    assert manifest["current_baseline"]["validation_status"] == "follow_up_required"
    assert manifest["current_baseline"]["bounded_result"]["score"] == -15.1679
    assert [branch["title"] for branch in manifest["failed_branches"]] == [
        "Experiment - Invalid Output Failed",
        "Experiment - Overfit Revert",
    ]
    assert manifest["next_recommended_experiment"] == "Test a momentum-strength threshold / no-trade band"
    assert manifest["branch_summary_paths"] == [str(failed_summary_path), str(summary_path)]
    assert index_path.exists()
    assert summary_path.exists()
    index_text = index_path.read_text()
    assert "raw evidence" in index_text.lower()
    assert "quant-autoresearch/experiments/" in index_text
    assert "experiments/continuation/current_research_base.json" in index_text
    assert "experiments/iterations/..." in index_text


def test_refresh_research_base_ignores_top_level_experiment_draft_notes(monkeypatch, tmp_path):
    """Refresh should not promote draft artifacts into the continuation manifest."""
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))
    experiments_dir = vault_root / "quant-autoresearch" / "experiments"
    experiments_dir.mkdir(parents=True)
    _write_note(
        experiments_dir,
        "2026-04-20-final.md",
        "note_type: experiment\nexperiment_slug: final\ndecision: keep\n",
        "# Final\n",
    )
    _write_note(
        experiments_dir,
        "2026-04-20-draft.md",
        "note_type: experiment_draft\ndraft_type: derived_iteration_artifact\n",
        "# Draft\n",
    )
    manifest_path = tmp_path / "manifest.json"

    result = runner.invoke(app, ["refresh_research_base", "--manifest-path", str(manifest_path)])

    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text())
    assert [record["title"] for record in manifest["experiments"]] == ["Final"]
