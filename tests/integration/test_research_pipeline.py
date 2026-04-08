from unittest.mock import patch

from typer.testing import CliRunner

from cli import app

runner = CliRunner()


@patch("cli.search_arxiv")
def test_research_pipeline_writes_vault_note(mock_search_arxiv, monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))
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
        ["research", "intraday momentum", "--depth", "shallow", "--output", "vault"],
    )

    research_dir = tmp_path / "vault" / "quant-autoresearch" / "research"
    files = list(research_dir.glob("*.md"))

    assert result.exit_code == 0
    assert len(files) == 1
    assert "Momentum Paper" in files[0].read_text()
