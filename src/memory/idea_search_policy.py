from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_IDEA_FRESHNESS_DAYS = 7
DEFAULT_SEARCH_REFRESH_INTERVAL = 10


def _coerce_note_date(raw_date: Any) -> date | None:
    if raw_date is None:
        return None
    if isinstance(raw_date, datetime):
        return raw_date.date()
    if isinstance(raw_date, date):
        return raw_date
    if isinstance(raw_date, str):
        normalized = raw_date.strip()
        if not normalized:
            return None
        normalized = normalized.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            try:
                return date.fromisoformat(normalized)
            except ValueError:
                return None
    return None


def _extract_note_date(note: dict[str, Any]) -> date | None:
    frontmatter = note.get("frontmatter", {})
    note_date = _coerce_note_date(frontmatter.get("date"))
    if note_date is not None:
        return note_date

    note_path = note.get("path")
    if isinstance(note_path, Path):
        prefix = note_path.stem.split("-", 3)[:3]
        if len(prefix) == 3:
            return _coerce_note_date("-".join(prefix))
    return None


def _is_research_note(note: dict[str, Any]) -> bool:
    frontmatter = note.get("frontmatter", {})
    note_type = frontmatter.get("note_type")
    return note.get("source") == "research" or note_type == "research"


def decide_self_search(
    notes: list[dict[str, Any]],
    completed_experiments: int,
    today: date | None = None,
    freshness_window_days: int = DEFAULT_IDEA_FRESHNESS_DAYS,
    refresh_interval: int = DEFAULT_SEARCH_REFRESH_INTERVAL,
) -> dict[str, Any]:
    if completed_experiments < 0:
        raise ValueError("completed_experiments must be non-negative")

    reference_day = today or date.today()
    freshness_cutoff = reference_day - timedelta(days=freshness_window_days)
    reasons: list[str] = []

    latest_research_note = max(
        (
            note_date
            for note in notes
            if _is_research_note(note)
            for note_date in [_extract_note_date(note)]
            if note_date is not None
        ),
        default=None,
    )

    if latest_research_note is None:
        reasons.append("missing_recent_research_note")
    elif latest_research_note < freshness_cutoff:
        reasons.append("stale_research_note")

    if completed_experiments > 0 and completed_experiments % refresh_interval == 0:
        reasons.append("scheduled_refresh")

    return {
        "should_search": bool(reasons),
        "reasons": reasons,
        "latest_research_note": latest_research_note.isoformat() if latest_research_note else None,
    }
