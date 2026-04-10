import pytest

from analysis.discussion_packet import build_strategy_discussion_packet


def test_build_strategy_discussion_packet_preserves_strategy_guardrails_and_traceability():
    packet = build_strategy_discussion_packet(
        question="Should AAPL stay in the intraday universe for the minute strategy?",
        route={
            "route": "strategy_stock_discussion",
            "reason": "strategy_oriented_stock_reasoning",
        },
        tickers=["AAPL", "NVDA"],
        strategy_thesis=(
            "Retain liquid names only while opening depth remains stable enough to "
            "support the minute strategy's entry quality."
        ),
        supporting_observations=[
            "AAPL still shows consistent opening spread compression after the first five minutes.",
            "NVDA keeps clearing the baseline liquidity threshold on high-volume sessions.",
        ],
        contrarian_observations=[
            "NVDA can lose entry quality quickly when the opening auction exhausts too fast.",
        ],
        candidate_hooks=[
            {
                "hook_id": "opening-liquidity-retention",
                "seed_type": "topic",
                "seed_value": "opening liquidity retention",
                "rationale": "Use opening-depth resilience as a bounded strategy refinement input.",
                "expected_effect": "improve entry quality during high-liquidity windows",
                "tickers": ["AAPL", "NVDA"],
            }
        ],
        analysis_context={
            "source": "analyze:AAPL,NVDA",
            "path": "vault/analysis/2026-04-10-aapl-nvda.md",
            "title": "AAPL NVDA Analyze Snapshot",
            "summary": "Opening liquidity remains strong but fades faster in thin midday sessions.",
        },
        strategy_context={
            "mode": "minute",
            "timeframe": "intraday",
        },
    )

    assert packet == {
        "route": "strategy_stock_discussion",
        "question": "Should AAPL stay in the intraday universe for the minute strategy?",
        "tickers": ["AAPL", "NVDA"],
        "discussion_type": "strategy_stock_discussion",
        "strategy_thesis": (
            "Retain liquid names only while opening depth remains stable enough to "
            "support the minute strategy's entry quality."
        ),
        "supporting_observations": [
            "AAPL still shows consistent opening spread compression after the first five minutes.",
            "NVDA keeps clearing the baseline liquidity threshold on high-volume sessions.",
        ],
        "contrarian_observations": [
            "NVDA can lose entry quality quickly when the opening auction exhausts too fast.",
        ],
        "candidate_hooks": [
            {
                "hook_id": "opening-liquidity-retention",
                "seed_type": "topic",
                "seed_value": "opening liquidity retention",
                "rationale": "Use opening-depth resilience as a bounded strategy refinement input.",
                "expected_effect": "improve entry quality during high-liquidity windows",
                "tickers": ["AAPL", "NVDA"],
            }
        ],
        "decision_guard": "research_input_only",
        "validation_rule": "backtester_required",
        "traceability": {
            "source_question": "Should AAPL stay in the intraday universe for the minute strategy?",
            "route_reason": "strategy_oriented_stock_reasoning",
            "analysis_context": {
                "source": "analyze:AAPL,NVDA",
                "path": "vault/analysis/2026-04-10-aapl-nvda.md",
                "title": "AAPL NVDA Analyze Snapshot",
                "summary": "Opening liquidity remains strong but fades faster in thin midday sessions.",
            },
            "strategy_context": {
                "mode": "minute",
                "timeframe": "intraday",
            },
        },
    }


def test_build_strategy_discussion_packet_requires_strategy_discussion_route():
    with pytest.raises(ValueError, match="strategy_stock_discussion"):
        build_strategy_discussion_packet(
            question="What regime is SPY in right now?",
            route={"route": "analyze_snapshot", "reason": "snapshot_market_state"},
            tickers=["SPY"],
            strategy_thesis="Do not use this packet for deterministic snapshot questions.",
            supporting_observations=["Snapshot questions belong in analyze."],
            contrarian_observations=["A discussion packet would blur the boundary."],
            candidate_hooks=[
                {
                    "hook_id": "invalid",
                    "seed_type": "topic",
                    "seed_value": "snapshot misuse",
                    "rationale": "This should fail before any downstream use.",
                }
            ],
        )


def test_build_strategy_discussion_packet_requires_explicit_contrarian_reasoning():
    with pytest.raises(ValueError, match="contrarian_observations"):
        build_strategy_discussion_packet(
            question="Should AAPL stay in the intraday universe for the minute strategy?",
            route={
                "route": "strategy_stock_discussion",
                "reason": "strategy_oriented_stock_reasoning",
            },
            tickers=["AAPL"],
            strategy_thesis="Retain AAPL only when liquidity remains reliable.",
            supporting_observations=["AAPL remains liquid enough at the open."],
            contrarian_observations=[],
            candidate_hooks=[
                {
                    "hook_id": "aapl-liquidity",
                    "seed_type": "topic",
                    "seed_value": "opening liquidity reliability",
                    "rationale": "Need a reversible input for later hypothesis generation.",
                }
            ],
        )
