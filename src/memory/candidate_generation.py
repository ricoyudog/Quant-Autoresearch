import re
from hashlib import sha1
from typing import Any


def _require_non_empty(mapping: dict[str, Any], key: str, label: str) -> Any:
    value = mapping.get(key)
    if value is None:
        raise ValueError(f"{label} is required")
    if isinstance(value, str) and not value.strip():
        raise ValueError(f"{label} is required")
    if isinstance(value, list) and not value:
        raise ValueError(f"{label} is required")
    return value


def _normalize_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", value.lower())
        if token
    }


def _coerce_tickers(raw_tickers: Any) -> list[str]:
    if raw_tickers is None:
        return []
    if isinstance(raw_tickers, str):
        return [raw_tickers]
    return [str(ticker) for ticker in raw_tickers]


def _select_seed(idea_context: dict[str, Any]) -> tuple[str, str]:
    query = idea_context.get("query")
    if isinstance(query, str) and query.strip():
        return "query", query.strip()

    topic = idea_context.get("topic")
    if isinstance(topic, str) and topic.strip():
        return "topic", topic.strip()

    tickers = _coerce_tickers(idea_context.get("tickers"))
    if tickers:
        return "tickers", ", ".join(tickers)

    raise ValueError("idea_context requires query, topic, or tickers")


def determine_strategy_change(
    idea_context: dict[str, Any],
    strategy_context: dict[str, Any],
) -> dict[str, Any]:
    _, seed_value = _select_seed(idea_context)
    seed_tokens = _normalize_tokens(seed_value)

    best_component = None
    best_overlap: set[str] = set()
    for component in strategy_context.get("components", []):
        overlap = seed_tokens & _normalize_tokens(str(component))
        if len(overlap) > len(best_overlap):
            best_component = str(component)
            best_overlap = overlap

    if best_component:
        return {
            "change_mode": "modify_existing_strategy",
            "target_component": best_component,
            "matched_terms": sorted(best_overlap),
            "edit_guidance": "Change one existing component and keep the remaining baseline logic fixed until validation.",
        }

    return {
        "change_mode": "extend_current_strategy",
        "target_component": seed_value,
        "matched_terms": [],
        "edit_guidance": "Add one bounded component on top of the current baseline and keep existing logic fixed until validation.",
    }


def build_candidate_strategy_hypothesis(
    idea_context: dict[str, Any],
    market_context: dict[str, Any],
    strategy_context: dict[str, Any],
) -> dict[str, Any]:
    idea_path = _require_non_empty(idea_context, "path", "idea_context.path")
    idea_source = _require_non_empty(idea_context, "source", "idea_context.source")
    idea_title = _require_non_empty(idea_context, "title", "idea_context.title")

    market_source = _require_non_empty(market_context, "source", "market_context.source")
    market_summary = _require_non_empty(market_context, "summary", "market_context.summary")

    strategy_path = _require_non_empty(strategy_context, "strategy_path", "strategy_context.strategy_path")
    baseline_sharpe = _require_non_empty(strategy_context, "baseline_sharpe", "strategy_context.baseline_sharpe")
    _require_non_empty(strategy_context, "components", "strategy_context.components")
    results_summary = _require_non_empty(strategy_context, "results_summary", "strategy_context.results_summary")

    seed_type, seed_value = _select_seed(idea_context)
    change = determine_strategy_change(idea_context, strategy_context)
    expected_effect = market_context.get("expected_effect") or "improve risk-adjusted returns"

    hypothesis = (
        f"If we {change['change_mode'].replace('_', ' ')} via {change['target_component']} "
        f"using {seed_type} '{seed_value}', the minute strategy should {expected_effect} "
        f"because {market_summary}"
    )
    structured_context = {
        "path": str(idea_path),
        "source": idea_source,
        "title": idea_title,
        "query": idea_context.get("query"),
        "topic": idea_context.get("topic"),
        "tickers": _coerce_tickers(idea_context.get("tickers")),
    }
    candidate_id = "cand-" + sha1(
        f"{structured_context['path']}|{change['change_mode']}|{change['target_component']}".encode()
    ).hexdigest()[:12]
    change_summary = (
        f"{change['change_mode']} via {change['target_component']} "
        f"from {seed_type} '{seed_value}'"
    )

    return {
        "candidate_id": candidate_id,
        "hypothesis": hypothesis,
        "change_summary": change_summary,
        "change_mode": change["change_mode"],
        "target_component": change["target_component"],
        "matched_terms": change["matched_terms"],
        "edit_guidance": change["edit_guidance"],
        "validation_status": "pending_backtest",
        "validation_rule": "backtester_required",
        "keep_revert_basis": "not_decided",
        "structured_context": structured_context,
        "idea_reference": {
            "path": structured_context["path"],
            "source": structured_context["source"],
            "title": structured_context["title"],
            "seed_type": seed_type,
            "seed_value": seed_value,
            "tickers": structured_context["tickers"],
        },
        "market_context": {
            "source": market_source,
            "summary": market_summary,
            "expected_effect": expected_effect,
        },
        "baseline_context": {
            "strategy_path": str(strategy_path),
            "baseline_sharpe": float(baseline_sharpe),
            "results_summary": results_summary,
            "components": [str(component) for component in strategy_context.get("components", [])],
        },
    }
