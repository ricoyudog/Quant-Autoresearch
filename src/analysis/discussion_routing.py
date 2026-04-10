def route_stock_question(question: str, context: dict | None = None) -> dict[str, str]:
    """Route deterministic snapshot questions away from strategy discussion."""
    context = context or {}
    normalized = question.lower()

    snapshot_keywords = ("regime", "what regime", "market state", "snapshot")
    strategy_keywords = (
        "strategy",
        "universe",
        "entry",
        "alpha",
        "microstructure",
        "liquidity",
        "execution",
    )

    has_snapshot_signal = any(keyword in normalized for keyword in snapshot_keywords)
    has_strategy_signal = any(keyword in normalized for keyword in strategy_keywords)

    if has_snapshot_signal and not has_strategy_signal:
        return {
            "route": "analyze_snapshot",
            "reason": "snapshot_market_state",
        }

    if has_strategy_signal:
        return {
            "route": "strategy_stock_discussion",
            "reason": "strategy_oriented_stock_reasoning",
        }

    return {
        "route": "analyze_snapshot",
        "reason": "default_snapshot_path",
    }
