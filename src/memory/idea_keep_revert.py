from typing import Any

RESULTS_TSV_PATH = "experiments/results.tsv"


def _required_value(data: dict[str, Any], field: str, context: str) -> Any:
    """Return a required field or raise a context-rich error."""
    value = data.get(field)
    if value in (None, ""):
        raise ValueError(f"{context} requires {field}")
    return value


def build_backtest_handoff(
    candidate: dict[str, Any],
    analysis_note: dict[str, Any],
    strategy_path: str,
    previous_best: float | None = None,
) -> dict[str, Any]:
    """Build the validation payload passed from candidate generation to backtesting."""
    structured_context = _required_value(candidate, "structured_context", "candidate")

    idea_trace = {
        "path": _required_value(structured_context, "path", "structured_context"),
        "source": _required_value(structured_context, "source", "structured_context"),
        "title": _required_value(structured_context, "title", "structured_context"),
        "query": structured_context.get("query"),
        "topic": structured_context.get("topic"),
        "tickers": structured_context.get("tickers") or [],
    }

    return {
        "validation_mode": "backtest",
        "candidate_id": _required_value(candidate, "candidate_id", "candidate"),
        "hypothesis": _required_value(candidate, "hypothesis", "candidate"),
        "change_summary": _required_value(candidate, "change_summary", "candidate"),
        "idea_trace": idea_trace,
        "analysis_context": {
            "path": _required_value(analysis_note, "path", "analysis_note"),
            "title": analysis_note.get("title"),
        },
        "strategy_path": strategy_path,
        "previous_best": previous_best,
        "keep_rule": "backtester_outcome_only",
    }


def decide_keep_revert(
    backtest_metrics: dict[str, Any],
    idea_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decide keep or revert from backtester outcomes only."""
    score = float(_required_value(backtest_metrics, "score", "backtest_metrics"))
    baseline_sharpe = float(
        _required_value(backtest_metrics, "baseline_sharpe", "backtest_metrics")
    )
    previous_best = backtest_metrics.get("previous_best")
    if previous_best is not None:
        previous_best = float(previous_best)

    reasons: list[str] = []
    if score <= baseline_sharpe:
        reasons.append("score_not_above_baseline")
    if previous_best is not None and score <= previous_best:
        reasons.append("score_not_above_previous_best")

    return {
        "decision": "revert" if reasons else "keep",
        "reasons": reasons or ["score_above_baseline_and_previous_best"],
        "score": score,
        "baseline_sharpe": baseline_sharpe,
        "previous_best": previous_best,
        "ignored_inputs": sorted((idea_review or {}).keys()),
    }


def build_iteration_record(
    handoff: dict[str, Any],
    decision: dict[str, Any],
    experiment_note_path: str,
) -> dict[str, Any]:
    """Capture the required per-iteration outputs for traceable keep/revert decisions."""
    return {
        "candidate_id": handoff["candidate_id"],
        "hypothesis": handoff["hypothesis"],
        "decision": decision["decision"],
        "decision_reasons": decision["reasons"],
        "idea_trace": handoff["idea_trace"],
        "analysis_context": handoff["analysis_context"],
        "strategy_path": handoff["strategy_path"],
        "backtest_metrics": {
            "score": decision["score"],
            "baseline_sharpe": decision["baseline_sharpe"],
            "previous_best": decision["previous_best"],
        },
        "artifacts": {
            "results_tsv": RESULTS_TSV_PATH,
            "experiment_note": experiment_note_path,
        },
    }
