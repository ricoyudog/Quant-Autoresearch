from unittest.mock import patch

from typer.testing import CliRunner

from cli import app

runner = CliRunner()


@patch("cli.search_arxiv")
def test_research_shallow_stdout_uses_arxiv_only(mock_search_arxiv):
    mock_search_arxiv.return_value = [
        {
            "title": "Momentum Paper",
            "summary": "Summary",
            "url": "https://example.com/paper",
            "published": "2026-01-01",
        }
    ]

    result = runner.invoke(
        app,
        ["research", "intraday momentum", "--depth", "shallow", "--output", "stdout"],
    )

    assert result.exit_code == 0
    assert "# Research: Intraday Momentum" in result.stdout
    mock_search_arxiv.assert_called_once()


@patch("cli.search_web")
@patch("cli.search_arxiv")
def test_research_deep_without_credentials_reports_skip(mock_search_arxiv, mock_search_web, monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    mock_search_arxiv.return_value = []

    result = runner.invoke(
        app,
        ["research", "macro rates", "--depth", "deep", "--output", "stdout"],
    )

    assert result.exit_code == 0
    assert "Deep web search skipped" in result.stdout
    mock_search_web.assert_not_called()


@patch("cli.search_arxiv")
def test_research_vault_reuses_matching_note(mock_search_arxiv, monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))
    research_dir = tmp_path / "vault" / "quant-autoresearch" / "research"
    research_dir.mkdir(parents=True)
    existing_note = research_dir / "2026-04-08-intraday-momentum.md"
    existing_note.write_text(
        "---\n"
        "note_type: research\n"
        "query: intraday momentum strategy\n"
        "---\n\n"
        "# Existing\n"
    )

    result = runner.invoke(
        app,
        ["research", "intraday momentum strategy", "--depth", "shallow", "--output", "vault"],
    )

    assert result.exit_code == 0
    assert f"Reused existing research note: {existing_note}" in result.stdout
    mock_search_arxiv.assert_not_called()
