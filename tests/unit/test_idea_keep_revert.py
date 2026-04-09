from memory.idea_keep_revert import (
    build_backtest_handoff,
    build_iteration_record,
    decide_keep_revert,
)


def _candidate() -> dict:
    return {
        "candidate_id": "cand-001",
        "hypothesis": "Add intraday volume confirmation to the breakout filter",
        "change_summary": "Gate entries on relative volume expansion.",
        "structured_context": {
            "path": "vault/research/2026-04-09-volume-breakout.md",
            "source": "research",
            "title": "Intraday Volume Breakout",
            "query": "intraday breakout volume confirmation",
            "topic": "breakout",
            "tickers": ["AAPL", "NVDA"],
        },
    }


def test_build_backtest_handoff_preserves_candidate_traceability():
    handoff = build_backtest_handoff(
        _candidate(),
        analysis_note={"path": "vault/analysis/2026-04-09-aapl.md", "title": "AAPL Analysis"},
        strategy_path="src/strategies/active_strategy.py",
        previous_best=0.62,
    )

    assert handoff == {
        "validation_mode": "backtest",
        "candidate_id": "cand-001",
        "hypothesis": "Add intraday volume confirmation to the breakout filter",
        "change_summary": "Gate entries on relative volume expansion.",
        "idea_trace": {
            "path": "vault/research/2026-04-09-volume-breakout.md",
            "source": "research",
            "title": "Intraday Volume Breakout",
            "query": "intraday breakout volume confirmation",
            "topic": "breakout",
            "tickers": ["AAPL", "NVDA"],
        },
        "analysis_context": {
            "path": "vault/analysis/2026-04-09-aapl.md",
            "title": "AAPL Analysis",
        },
        "strategy_path": "src/strategies/active_strategy.py",
        "previous_best": 0.62,
        "keep_rule": "backtester_outcome_only",
    }


def test_decide_keep_revert_reverts_even_when_idea_quality_is_high():
    decision = decide_keep_revert(
        {
            "score": 0.41,
            "baseline_sharpe": 0.45,
            "previous_best": 0.62,
        },
        idea_review={"idea_quality": 0.99, "novelty": "high"},
    )

    assert decision == {
        "decision": "revert",
        "reasons": [
            "score_not_above_baseline",
            "score_not_above_previous_best",
        ],
        "score": 0.41,
        "baseline_sharpe": 0.45,
        "previous_best": 0.62,
        "ignored_inputs": ["idea_quality", "novelty"],
    }


def test_decide_keep_revert_keeps_when_backtest_beats_thresholds_even_if_idea_quality_is_low():
    decision = decide_keep_revert(
        {
            "score": 0.74,
            "baseline_sharpe": 0.45,
            "previous_best": 0.62,
        },
        idea_review={"idea_quality": 0.1},
    )

    assert decision == {
        "decision": "keep",
        "reasons": ["score_above_baseline_and_previous_best"],
        "score": 0.74,
        "baseline_sharpe": 0.45,
        "previous_best": 0.62,
        "ignored_inputs": ["idea_quality"],
    }


def test_build_iteration_record_lists_required_outputs():
    handoff = build_backtest_handoff(
        _candidate(),
        analysis_note={"path": "vault/analysis/2026-04-09-aapl.md", "title": "AAPL Analysis"},
        strategy_path="src/strategies/active_strategy.py",
        previous_best=0.62,
    )
    decision = decide_keep_revert(
        {
            "score": 0.74,
            "baseline_sharpe": 0.45,
            "previous_best": 0.62,
        }
    )

    record = build_iteration_record(
        handoff,
        decision,
        experiment_note_path="vault/experiments/2026-04-09-volume-breakout.md",
    )

    assert record == {
        "candidate_id": "cand-001",
        "hypothesis": "Add intraday volume confirmation to the breakout filter",
        "decision": "keep",
        "decision_reasons": ["score_above_baseline_and_previous_best"],
        "idea_trace": {
            "path": "vault/research/2026-04-09-volume-breakout.md",
            "source": "research",
            "title": "Intraday Volume Breakout",
            "query": "intraday breakout volume confirmation",
            "topic": "breakout",
            "tickers": ["AAPL", "NVDA"],
        },
        "analysis_context": {
            "path": "vault/analysis/2026-04-09-aapl.md",
            "title": "AAPL Analysis",
        },
        "strategy_path": "src/strategies/active_strategy.py",
        "backtest_metrics": {
            "score": 0.74,
            "baseline_sharpe": 0.45,
            "previous_best": 0.62,
        },
        "artifacts": {
            "results_tsv": "experiments/results.tsv",
            "experiment_note": "vault/experiments/2026-04-09-volume-breakout.md",
        },
    }
