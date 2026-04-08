import pandas as pd
from typer.testing import CliRunner

from cli import app

runner = CliRunner()


def build_symbol_frame() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=120, freq="D")
    close = pd.Series([100 + i for i in range(120)], index=dates, dtype=float)
    return pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 1,
            "Low": close - 2,
            "Close": close,
            "Volume": pd.Series([1000 + i * 10 for i in range(120)], index=dates, dtype=float),
        }
    )


def test_analyze_pipeline_writes_vault_note_and_seeds_knowledge(monkeypatch, tmp_path):
    frame = build_symbol_frame()

    class StubConnector:
        def load_symbol(self, symbol):
            return frame

    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setattr("cli.DataConnector", lambda: StubConnector())

    result = runner.invoke(
        app,
        ["analyze", "SPY", "--start", "2025-01-01", "--output", "vault"],
    )

    research_dir = tmp_path / "vault" / "quant-autoresearch" / "research"
    knowledge_dir = tmp_path / "vault" / "quant-autoresearch" / "knowledge"

    assert result.exit_code == 0
    assert list(research_dir.glob("*.md"))
    assert (knowledge_dir / "overfit-defense.md").exists()
