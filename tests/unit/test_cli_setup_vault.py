from typer.testing import CliRunner

from cli import app

runner = CliRunner()


def test_setup_vault_is_idempotent_with_override(monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))

    first = runner.invoke(app, ["setup_vault"])
    second = runner.invoke(app, ["setup_vault"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "project_root: created" in first.stdout
    assert "project_root: already existed" in second.stdout
