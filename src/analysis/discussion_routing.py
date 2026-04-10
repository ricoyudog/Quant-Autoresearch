def route_stock_question(question: str, context: dict | None = None) -> dict[str, str]:
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
        "intraday",
        "minute",
    )

    if any(keyword in normalized for keyword in snapshot_keywords):
        return {
            "route": "analyze_snapshot",
            "reason": "snapshot_market_state",
        }

    if context.get("strategy_mode") == "minute" or any(
        keyword in normalized for keyword in strategy_keywords
    ):
        return {
            "route": "strategy_stock_discussion",
            "reason": "strategy_oriented_stock_reasoning",
        }

    return {
        "route": "analyze_snapshot",
        "reason": "default_snapshot_path",
    }
