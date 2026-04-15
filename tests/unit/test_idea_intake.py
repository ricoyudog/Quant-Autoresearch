from pathlib import Path

import pytest

from memory.idea_intake import build_minimum_structured_context, collect_vault_idea_notes


def test_collect_vault_idea_notes_reads_research_and_knowledge(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))

    research_dir = vault_root / "quant-autoresearch" / "research"
    knowledge_dir = vault_root / "quant-autoresearch" / "knowledge"
    research_dir.mkdir(parents=True)
    knowledge_dir.mkdir(parents=True)

    (research_dir / "2026-04-09-intraday-alpha.md").write_text(
        "---\n"
        "note_type: research\n"
        "query: intraday alpha\n"
        "---\n\n"
        "# Intraday Alpha\n"
        "Research body\n"
    )
    (knowledge_dir / "microstructure.md").write_text(
        "---\n"
        "note_type: knowledge\n"
        "topic: market-microstructure\n"
        "---\n\n"
        "# Market Microstructure\n"
        "Knowledge body\n"
    )

    notes = collect_vault_idea_notes()

    assert [note["source"] for note in notes] == ["research", "knowledge"]
    assert notes[0]["title"] == "Intraday Alpha"
    assert notes[0]["frontmatter"]["query"] == "intraday alpha"
    assert notes[1]["title"] == "Market Microstructure"
    assert notes[1]["frontmatter"]["topic"] == "market-microstructure"


def test_collect_vault_idea_notes_limits_results(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))

    research_dir = vault_root / "quant-autoresearch" / "research"
    research_dir.mkdir(parents=True)

    for index in range(3):
        (research_dir / f"2026-04-0{index + 1}-note-{index}.md").write_text(
            "---\n"
            f"query: note-{index}\n"
            "---\n\n"
            f"# Note {index}\n"
        )

    notes = collect_vault_idea_notes(limit=2, include_knowledge=False)

    assert len(notes) == 2
    assert [note["title"] for note in notes] == ["Note 2", "Note 1"]


def test_build_minimum_structured_context_extracts_seed_fields(tmp_path):
    note_path = tmp_path / "2026-04-09-intraday-alpha.md"
    note = {
        "path": note_path,
        "source": "research",
        "title": "Intraday Alpha",
        "frontmatter": {
            "note_type": "research",
            "query": "intraday alpha",
            "tickers": ["AAPL"],
        },
    }

    context = build_minimum_structured_context(note)

    assert context == {
        "path": str(note_path),
        "source": "research",
        "title": "Intraday Alpha",
        "note_type": "research",
        "query": "intraday alpha",
        "topic": None,
        "tickers": ["AAPL"],
    }


def test_collect_vault_idea_notes_ignores_experiment_notes(monkeypatch, tmp_path):
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_root))

    project_root = vault_root / "quant-autoresearch"
    research_dir = project_root / "research"
    knowledge_dir = project_root / "knowledge"
    experiments_dir = project_root / "experiments"
    research_dir.mkdir(parents=True)
    knowledge_dir.mkdir(parents=True)
    experiments_dir.mkdir(parents=True)

    (research_dir / "2026-04-09-intraday-alpha.md").write_text(
        "---\nquery: intraday alpha\n---\n\n# Intraday Alpha\n"
    )
    (knowledge_dir / "market-microstructure.md").write_text(
        "---\ntopic: market-microstructure\n---\n\n# Market Microstructure\n"
    )
    (experiments_dir / "2026-04-09-alpha-check.md").write_text(
        "---\nnote_type: experiment\n---\n\n# Experiment\n"
    )

    notes = collect_vault_idea_notes()

    assert [note["source"] for note in notes] == ["research", "knowledge"]


def test_build_minimum_structured_context_requires_metadata_seed(tmp_path):
    note = {
        "path": tmp_path / "unstructured.md",
        "source": "research",
        "title": "Unstructured Idea",
        "frontmatter": {"note_type": "research"},
    }

    with pytest.raises(ValueError, match="query, topic, or tickers"):
        build_minimum_structured_context(note)
