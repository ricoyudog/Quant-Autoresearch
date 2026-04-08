from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_DIRECTORY = "quant-autoresearch"


@dataclass(frozen=True)
class VaultPaths:
    vault_root: Path
    project_root: Path
    experiments: Path
    research: Path
    knowledge: Path


@dataclass(frozen=True)
class DirectoryStatus:
    name: str
    path: Path
    created: bool


def get_vault_root() -> Path:
    override = os.getenv("OBSIDIAN_VAULT_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Documents" / "Obsidian Vault"


def get_vault_paths(vault_root: str | Path | None = None) -> VaultPaths:
    resolved_root = Path(vault_root).expanduser() if vault_root else get_vault_root()
    project_root = resolved_root / PROJECT_DIRECTORY
    return VaultPaths(
        vault_root=resolved_root,
        project_root=project_root,
        experiments=project_root / "experiments",
        research=project_root / "research",
        knowledge=project_root / "knowledge",
    )


def ensure_vault_directories(vault_root: str | Path | None = None) -> list[DirectoryStatus]:
    paths = get_vault_paths(vault_root)
    statuses: list[DirectoryStatus] = []

    for name, path in (
        ("project_root", paths.project_root),
        ("experiments", paths.experiments),
        ("research", paths.research),
        ("knowledge", paths.knowledge),
    ):
        existed = path.exists()
        path.mkdir(parents=True, exist_ok=True)
        statuses.append(DirectoryStatus(name=name, path=path, created=not existed))

    return statuses
