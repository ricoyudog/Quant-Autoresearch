from pathlib import Path
from typing import Any

from config.vault import get_vault_paths
from core.research import read_frontmatter


def _read_title(note_path: Path) -> str:
    for line in note_path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return note_path.stem


def _collect_from_directory(directory: Path, source: str) -> list[dict[str, Any]]:
    if not directory.exists():
        return []

    notes: list[dict[str, Any]] = []
    for note_path in sorted(directory.glob("*.md"), reverse=True):
        notes.append(
            {
                "path": note_path,
                "source": source,
                "title": _read_title(note_path),
                "frontmatter": read_frontmatter(note_path),
            }
        )
    return notes


def build_minimum_structured_context(note: dict[str, Any]) -> dict[str, Any]:
    frontmatter = note.get("frontmatter") or {}
    tickers = frontmatter.get("tickers") or []
    if isinstance(tickers, str):
        tickers = [tickers]

    if not any((frontmatter.get("query"), frontmatter.get("topic"), tickers)):
        raise ValueError(
            "minimum structured context requires query, topic, or tickers metadata"
        )

    return {
        "path": str(note["path"]),
        "source": note["source"],
        "title": note["title"],
        "note_type": frontmatter.get("note_type"),
        "query": frontmatter.get("query"),
        "topic": frontmatter.get("topic"),
        "tickers": tickers,
    }


def collect_vault_idea_notes(
    limit: int = 10,
    include_research: bool = True,
    include_knowledge: bool = True,
) -> list[dict[str, Any]]:
    paths = get_vault_paths()
    notes: list[dict[str, Any]] = []

    if include_research:
        notes.extend(_collect_from_directory(paths.research, "research"))
    if include_knowledge:
        notes.extend(_collect_from_directory(paths.knowledge, "knowledge"))

    return notes[:limit]
