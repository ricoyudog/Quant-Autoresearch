import pytest

from memory.candidate_generation import build_candidate_strategy_hypothesis


def test_build_candidate_strategy_hypothesis_marks_candidate_pending_backtest():
    candidate = build_candidate_strategy_hypothesis(
        idea_context={
            "path": "vault/research/2026-04-09-intraday-momentum.md",
            "source": "research",
            "title": "Intraday Momentum",
            "query": "intraday momentum",
            "topic": "liquidity bursts",
            "tickers": ["AAPL"],
        },
        market_context={
            "source": "analyze:AAPL",
            "summary": "AAPL keeps extending after opening liquidity bursts.",
            "expected_effect": "improve risk-adjusted returns during high-liquidity windows",
        },
        strategy_context={
            "strategy_path": "src/strategies/active_strategy.py",
            "baseline_sharpe": 0.45,
            "components": ["momentum entry", "volume-ranked universe"],
            "results_summary": "Baseline momentum beats passive only when liquidity stays elevated.",
        },
    )

    assert candidate["change_mode"] == "modify_existing_strategy"
    assert candidate["target_component"] == "momentum entry"
    assert candidate["validation_status"] == "pending_backtest"
    assert candidate["validation_rule"] == "backtester_required"
    assert candidate["keep_revert_basis"] == "not_decided"
    assert "intraday momentum" in candidate["hypothesis"]
    assert "opening liquidity bursts" in candidate["hypothesis"]
    assert candidate["idea_reference"]["path"].endswith("intraday-momentum.md")
    assert candidate["baseline_context"]["baseline_sharpe"] == 0.45


def test_build_candidate_strategy_hypothesis_can_extend_strategy_for_new_concepts():
    candidate = build_candidate_strategy_hypothesis(
        idea_context={
            "path": "vault/knowledge/volatility-filter.md",
            "source": "knowledge",
            "title": "Volatility Filter",
            "topic": "volatility regime filter",
            "tickers": [],
        },
        market_context={
            "source": "analyze:SPY",
            "summary": "Whipsaws cluster when intraday volatility compresses before reversals.",
        },
        strategy_context={
            "strategy_path": "src/strategies/active_strategy.py",
            "baseline_sharpe": 0.45,
            "components": ["momentum entry", "volume-ranked universe"],
            "results_summary": "Current strategy degrades during compressed-volatility regimes.",
        },
    )

    assert candidate["change_mode"] == "extend_current_strategy"
    assert candidate["target_component"] == "volatility regime filter"
    assert candidate["edit_guidance"].startswith("Add one bounded component")


def test_build_candidate_strategy_hypothesis_requires_complete_context_bundle():
    with pytest.raises(ValueError, match="market_context.summary"):
        build_candidate_strategy_hypothesis(
            idea_context={
                "path": "vault/research/note.md",
                "source": "research",
                "title": "Missing Market Context",
                "query": "opening range breakout",
            },
            market_context={"source": "analyze:QQQ"},
            strategy_context={
                "strategy_path": "src/strategies/active_strategy.py",
                "baseline_sharpe": 0.45,
                "components": ["momentum entry"],
                "results_summary": "Baseline summary",
            },
        )
