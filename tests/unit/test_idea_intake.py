from pathlib import Path

from memory.idea_intake import collect_vault_idea_notes


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
