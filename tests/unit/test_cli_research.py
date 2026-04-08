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


@patch("cli.search_arxiv")
def test_research_stdout_suppresses_helper_noise(mock_search_arxiv):
    def noisy_search(query):
        print("  [Research] Local BM25 hit: Found 2 relevant papers.")
        return [
            {
                "title": "Momentum Paper",
                "summary": "Summary",
                "url": "https://example.com/paper",
                "published": "2026-01-01",
            }
        ]

    mock_search_arxiv.side_effect = noisy_search

    result = runner.invoke(
        app,
        ["research", "intraday momentum", "--depth", "shallow", "--output", "stdout"],
    )

    assert result.exit_code == 0
    assert result.stdout.startswith("---\n")
    assert "[Research]" not in result.stdout


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


@patch("cli.search_web")
@patch("cli.search_arxiv")
def test_research_deep_vault_upgrades_existing_shallow_note(
    mock_search_arxiv, mock_search_web, monkeypatch, tmp_path
):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("EXA_API_KEY", "test-key")
    research_dir = tmp_path / "vault" / "quant-autoresearch" / "research"
    research_dir.mkdir(parents=True)
    existing_note = research_dir / "2026-04-08-intraday-momentum.md"
    existing_note.write_text(
        "---\n"
        "note_type: research\n"
        "query: intraday momentum strategy\n"
        "depth: shallow\n"
        "---\n\n"
        "# Existing shallow note\n"
    )
    mock_search_arxiv.return_value = []
    mock_search_web.return_value = [
        {
            "title": "Macro rates note",
            "url": "https://example.com/rates",
            "source": "example",
            "snippet": "Fresh web result",
        }
    ]

    result = runner.invoke(
        app,
        ["research", "intraday momentum strategy", "--depth", "deep", "--output", "vault"],
    )

    assert result.exit_code == 0
    assert f"Wrote research note: {existing_note}" in result.stdout
    mock_search_arxiv.assert_called_once()
    mock_search_web.assert_called_once()
    updated_note = existing_note.read_text()
    assert "depth: deep" in updated_note
    assert "## Web Resources" in updated_note
