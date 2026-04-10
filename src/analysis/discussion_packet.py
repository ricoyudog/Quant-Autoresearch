from typing import Any


DISCUSSION_ROUTE = "strategy_stock_discussion"
DISCUSSION_TYPE = "strategy_stock_discussion"
DECISION_GUARD = "research_input_only"
VALIDATION_RULE = "backtester_required"


def _require_text(value: Any, label: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _normalize_points(values: list[str], label: str) -> list[str]:
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    if not cleaned:
        raise ValueError(f"{label} requires at least one item")
    return cleaned


def _normalize_hook_list(candidate_hooks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not candidate_hooks:
        raise ValueError("candidate_hooks requires at least one item")

    normalized: list[dict[str, Any]] = []
    for hook in candidate_hooks:
        if not isinstance(hook, dict):
            raise ValueError("candidate_hooks entries must be mappings")
        normalized.append(
            {
                key: value
                for key, value in hook.items()
                if value is not None and (not isinstance(value, str) or value.strip())
            }
        )
    return normalized


def _normalize_tickers(tickers: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for ticker in tickers or []:
        candidate = str(ticker).strip().upper()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized


def _build_string_map(
    values: dict[str, Any] | None,
    allowed_keys: tuple[str, ...],
) -> dict[str, str]:
    if not values:
        return {}

    normalized: dict[str, str] = {}
    for key in allowed_keys:
        value = values.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            normalized[key] = text
    return normalized


def _build_analysis_context(analysis_context: dict[str, Any] | None) -> dict[str, str]:
    if not analysis_context:
        return {}
    return _build_string_map(
        analysis_context,
        ("source", "path", "title", "summary"),
    )


def _build_strategy_context(strategy_context: dict[str, Any] | None) -> dict[str, str]:
    return _build_string_map(
        strategy_context,
        ("mode", "timeframe"),
    )


def build_strategy_discussion_packet(
    question: str,
    route: dict[str, str],
    tickers: list[str] | None,
    strategy_thesis: str,
    supporting_observations: list[str],
    contrarian_observations: list[str],
    candidate_hooks: list[dict[str, Any]],
    analysis_context: dict[str, Any] | None = None,
    strategy_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the narrow research-input packet for strategy-facing stock discussion."""
    route_name = _require_text(route.get("route"), "route.route")
    if route_name != DISCUSSION_ROUTE:
        raise ValueError("discussion packet requires strategy_stock_discussion route")

    normalized_question = _require_text(question, "question")
    normalized_thesis = _require_text(strategy_thesis, "strategy_thesis")
    normalized_support = _normalize_points(supporting_observations, "supporting_observations")
    normalized_contrarian = _normalize_points(
        contrarian_observations,
        "contrarian_observations",
    )
    normalized_candidate_hooks = _normalize_hook_list(candidate_hooks)
    normalized_tickers = _normalize_tickers(tickers)
    normalized_analysis_context = _build_analysis_context(analysis_context)
    normalized_strategy_context = _build_strategy_context(strategy_context)
    route_reason = str(route.get("reason") or "strategy_discussion_requested").strip()

    return {
        "route": route_name,
        "question": normalized_question,
        "tickers": normalized_tickers,
        "discussion_type": DISCUSSION_TYPE,
        "strategy_thesis": normalized_thesis,
        "supporting_observations": normalized_support,
        "contrarian_observations": normalized_contrarian,
        "candidate_hooks": normalized_candidate_hooks,
        "decision_guard": DECISION_GUARD,
        "validation_rule": VALIDATION_RULE,
        "traceability": {
            "source_question": normalized_question,
            "route_reason": route_reason,
            "analysis_context": normalized_analysis_context,
            "strategy_context": normalized_strategy_context,
        },
    }
