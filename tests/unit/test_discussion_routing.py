from analysis.discussion_routing import route_stock_question


def test_route_stock_question_keeps_snapshot_regime_queries_in_analyze():
    result = route_stock_question(
        question="What regime is SPY in right now?",
        context={"tickers": ["SPY"]},
    )

    assert result == {
        "route": "analyze_snapshot",
        "reason": "snapshot_market_state",
    }


def test_route_stock_question_escalates_strategy_selection_to_stock_discussion():
    result = route_stock_question(
        question="Should AAPL stay in the intraday universe for the minute strategy?",
        context={"tickers": ["AAPL"], "strategy_mode": "minute"},
    )

    assert result == {
        "route": "strategy_stock_discussion",
        "reason": "strategy_oriented_stock_reasoning",
    }


def test_route_stock_question_escalates_microstructure_questions():
    result = route_stock_question(
        question="How does NVDA opening liquidity affect intraday entry quality?",
        context={"tickers": ["NVDA"]},
    )

    assert result == {
        "route": "strategy_stock_discussion",
        "reason": "strategy_oriented_stock_reasoning",
    }
