from __future__ import annotations

import json
from pathlib import Path

from memory.experiment_memory import build_continuation_context, collect_experiment_memory


def _write_note(directory: Path, name: str, frontmatter: str, body: str) -> Path:
    note_path = directory / name
    note_path.write_text(f"---\n{frontmatter}---\n\n{body}")
    return note_path


def test_collect_experiment_memory_parses_keep_and_revert(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))
    experiments_dir = vault_root / "quant-autoresearch" / "experiments"
    experiments_dir.mkdir(parents=True)

    _write_note(
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
        "Status: **keep as the new baseline candidate**\n"
        "Reason:\n"
        "- Improved bounded score and drawdown\n"
        "- Reduced turnover-driven churn\n\n"
        "## Next Experiment\n"
        "- Test a momentum-strength threshold / no-trade band\n",
    )
    _write_note(
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
        "- Score regressed after fees\n"
        "- Turnover increased again\n",
    )

    records = collect_experiment_memory()

    assert [record["decision"] for record in records] == ["keep", "revert"]
    keep_record = records[0]
    revert_record = records[1]

    assert keep_record["branch_id"] == "turnover-reduction"
    assert keep_record["baseline_reference"] == "2026-04-14-turnover-reduction-confirmation-bars"
    assert keep_record["validation_status"] == "follow_up_required"
    assert keep_record["bounded_result"]["score"] == -15.1679
    assert keep_record["unrestricted_result"]["trades"] == 14093.0
    assert "fee-driven" in keep_record["turnover_fee_lesson"]

    assert revert_record["decision"] == "revert"
    assert revert_record["validation_status"] == "rejected"
    assert revert_record["parent_experiment"] == "2026-04-14-minimum-hold-duration"


def test_build_continuation_context_prefers_latest_keep_and_preserves_failures(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))
    experiments_dir = vault_root / "quant-autoresearch" / "experiments"
    experiments_dir.mkdir(parents=True)

    _write_note(
        experiments_dir,
        "2026-04-14-keep-alpha.md",
        "note_type: experiment\nexperiment_slug: keep-alpha\nstatus: completed\ndecision: keep\n",
        "# Alpha\n\n## Decision\nStatus: **keep**\n\n## Next Experiment\n- Keep refining alpha\n",
    )
    _write_note(
        experiments_dir,
        "2026-04-15-revert-beta.md",
        "note_type: experiment\nexperiment_slug: revert-beta\nstatus: completed\ndecision: revert\n",
        "# Beta\n\n## Decision\nStatus: **revert**\n",
    )
    _write_note(
        experiments_dir,
        "2026-04-16-keep-gamma.md",
        "note_type: experiment\nexperiment_slug: keep-gamma\nstatus: completed\ndecision: keep\n",
        "# Gamma\n\n## Decision\nStatus: **keep**\n\n## Next Experiment\n- Validate gamma on unrestricted universe\n",
    )

    context = build_continuation_context(collect_experiment_memory())

    assert context["current_baseline"]["title"] == "Gamma"
    assert context["recent_winning_branch"]["title"] == "Gamma"
    assert len(context["failed_branches"]) == 1
    assert context["failed_branches"][0]["title"] == "Beta"
    assert context["next_recommended_experiment"] == "Validate gamma on unrestricted universe"


def test_build_continuation_context_prefers_terminal_keep_in_parent_chain(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))
    experiments_dir = vault_root / "quant-autoresearch" / "experiments"
    experiments_dir.mkdir(parents=True)

    _write_note(
        experiments_dir,
        "2026-04-14-confirmation-bars.md",
        "note_type: experiment\n"
        "experiment_slug: confirmation-bars\n"
        "status: completed\n"
        "decision: keep\n",
        "# Confirmation Bars\n\n## Decision\nStatus: **keep**\n",
    )
    _write_note(
        experiments_dir,
        "2026-04-14-minimum-hold-duration.md",
        "note_type: experiment\n"
        "experiment_slug: minimum-hold-duration\n"
        "status: completed\n"
        "decision: keep\n",
        "# Minimum Hold Duration\n\n"
        "## Baseline Before This Experiment\n"
        "- Source experiment: [[2026-04-14-confirmation-bars]]\n\n"
        "## Decision\n"
        "Status: **keep**\n",
    )

    context = build_continuation_context(collect_experiment_memory())

    assert context["current_baseline"]["title"] == "Minimum Hold Duration"


def test_collect_experiment_memory_ignores_iteration_drafts(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))
    experiments_dir = vault_root / "quant-autoresearch" / "experiments"
    experiments_dir.mkdir(parents=True)
    iteration_dir = experiments_dir / "iterations" / "run-001" / "iteration-0001"
    iteration_dir.mkdir(parents=True)

    _write_note(
        experiments_dir,
        "2026-04-14-real-note.md",
        "note_type: experiment\nexperiment_slug: real-note\nstatus: completed\ndecision: keep\n",
        "# Real Note\n\n## Decision\nStatus: **keep**\n",
    )
    (iteration_dir / "experiment_note_draft.md").write_text(
        "---\nnote_type: experiment_draft\n---\n\n# Draft\n"
    )

    records = collect_experiment_memory()

    assert len(records) == 1
    assert records[0]["title"] == "Real Note"
