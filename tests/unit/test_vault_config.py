from config.vault import ensure_vault_directories, get_vault_paths


def test_get_vault_paths_uses_env_override(monkeypatch, tmp_path):
    custom_root = tmp_path / "vault-root"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(custom_root))

    paths = get_vault_paths()

    assert paths.vault_root == custom_root
    assert paths.project_root == custom_root / "quant-autoresearch"
    assert paths.experiments == custom_root / "quant-autoresearch" / "experiments"
    assert paths.research == custom_root / "quant-autoresearch" / "research"
    assert paths.knowledge == custom_root / "quant-autoresearch" / "knowledge"


def test_get_vault_paths_uses_default_home(monkeypatch, tmp_path):
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.setattr("config.vault.Path.home", lambda: tmp_path)

    paths = get_vault_paths()

    assert paths.vault_root == tmp_path / "Documents" / "Obsidian Vault"
    assert paths.project_root == paths.vault_root / "quant-autoresearch"


def test_ensure_vault_directories_is_idempotent(monkeypatch, tmp_path):
    custom_root = tmp_path / "vault-root"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(custom_root))

    first_run = ensure_vault_directories()
    second_run = ensure_vault_directories()

    assert all(status.path.exists() for status in first_run)
    assert [status.created for status in first_run] == [True, True, True, True]
    assert [status.created for status in second_run] == [False, False, False, False]
