from datetime import datetime

from core.research import (
    find_existing_research_note,
    format_research_report,
    render_research_report,
)


def test_format_research_report_includes_frontmatter_and_sections():
    report = format_research_report(
        query="intraday momentum strategy minute bars",
        papers=[
            {
                "title": "Intraday Momentum",
                "summary": "Momentum summary",
                "url": "https://example.com/paper",
                "published": "2026-01-01",
            }
        ],
        web_results=[],
        generated_at=datetime(2026, 4, 8, 12, 0, 0),
        depth="shallow",
    )

    assert report.startswith("---\n")
    assert 'note_type: research' in report
    assert 'query: intraday momentum strategy minute bars' in report
    assert "# Research: Intraday Momentum Strategy Minute Bars" in report
    assert "## Academic Papers" in report
    assert "Intraday Momentum" in report
    assert "## Web Resources" not in report


def test_render_research_report_writes_new_note(monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))

    report, output_path, reused_existing = render_research_report(
        query="momentum mean reversion",
        papers=[],
        web_results=[],
        output="vault",
        generated_at=datetime(2026, 4, 8, 9, 30, 0),
    )

    assert report.startswith("---\n")
    assert output_path is not None
    assert output_path.exists()
    assert output_path.read_text() == report
    assert output_path.name == "2026-04-08-momentum-mean-reversion.md"
    assert reused_existing is False


def test_find_existing_research_note_reuses_matching_query(monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))

    _, first_path, reused_existing = render_research_report(
        query="intraday momentum strategy minute bars",
        papers=[],
        web_results=[],
        output="vault",
        generated_at=datetime(2026, 4, 8, 10, 0, 0),
    )

    assert first_path is not None
    assert reused_existing is False

    match = find_existing_research_note(
        "momentum strategy minute bars",
        first_path.parent,
    )

    assert match == first_path
