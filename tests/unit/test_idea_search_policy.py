from datetime import date
from pathlib import Path

from memory.idea_search_policy import decide_self_search


def _research_note(path: str, note_date: str) -> dict:
    return {
        "path": Path(path),
        "source": "research",
        "title": "Idea Note",
        "frontmatter": {
            "note_type": "research",
            "date": note_date,
        },
    }


def test_self_search_runs_when_no_research_notes_are_available():
    decision = decide_self_search([], completed_experiments=0, today=date(2026, 4, 9))

    assert decision["should_search"] is True
    assert decision["reasons"] == ["missing_recent_research_note"]


def test_self_search_skips_when_recent_research_note_exists():
    notes = [_research_note("2026-04-08-intraday-alpha.md", "2026-04-08")]

    decision = decide_self_search(notes, completed_experiments=3, today=date(2026, 4, 9))

    assert decision["should_search"] is False
    assert decision["reasons"] == []


def test_self_search_runs_when_latest_research_note_is_stale():
    notes = [_research_note("2026-03-29-intraday-alpha.md", "2026-03-29")]

    decision = decide_self_search(notes, completed_experiments=4, today=date(2026, 4, 9))

    assert decision["should_search"] is True
    assert decision["reasons"] == ["stale_research_note"]


def test_self_search_ignores_experiment_notes_when_research_is_missing():
    notes = [
        {
            "path": Path("2026-04-09-turnover-check.md"),
            "source": "experiment",
            "title": "Turnover Check",
            "frontmatter": {
                "note_type": "experiment",
                "date": "2026-04-09",
            },
        }
    ]

    decision = decide_self_search(notes, completed_experiments=1, today=date(2026, 4, 9))

    assert decision["should_search"] is True
    assert decision["reasons"] == ["missing_recent_research_note"]


def test_self_search_runs_on_refresh_cadence_even_with_recent_notes():
    notes = [_research_note("2026-04-09-intraday-alpha.md", "2026-04-09")]

    decision = decide_self_search(notes, completed_experiments=10, today=date(2026, 4, 9))

    assert decision["should_search"] is True
    assert decision["reasons"] == ["scheduled_refresh"]
