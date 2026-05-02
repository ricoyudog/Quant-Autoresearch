# MartinLuk Phase 5 T020 Bounded Autoresearch Launch Gate

Generated at: `2026-05-02T10:29:00+00:00`

## Decision

- Overall decision: `bounded_autoresearch_launched_with_no_overclaim_boundary`
- Launch status: `completed`
- Launch attempted: `true`
- Launch authorized: `true`
- T020 state: `- [X] T020 Launch bounded autoresearch only after validator, focused tests, and replay gates pass`

## No-overclaim boundary

This artifact records a bounded autoresearch/backtest evaluation only. It does not prove profit, does not replicate Martin Luk realized P&L, does not replicate private-account outcomes, does not provide exact-fill replication, and does not upgrade public-operation rows while exact primary public evidence remains insufficient_evidence.

## Gate checks

- **Validator:** pass
  - Evidence: Phase 4/5 validator and bounded replay contracts exist and the mission validator passed after recording bounded launch evidence.
  - Source: `.omx/specs/autoresearch-martinluk-t020/validate.py`
- **Focused tests:** pass
  - Evidence: Focused reconciliation tests passed: 56 passed in 1.24s covering T020 launch artifact, Phase 5.7 no-overclaim/plan surfaces, strategy interface, backtester universe artifact, and minute backtest integration.
  - Source: `uv run pytest --import-mode=importlib -q tests/unit/test_martinluk_phase5_t020_bounded_autoresearch_launch.py tests/unit/test_martinluk_phase5_7_public_evidence_plan.py tests/unit/test_martinluk_phase5_7_no_overclaim_closeout.py tests/unit/test_martinluk_phase5_no_overclaim_boundaries.py tests/unit/test_strategy_interface.py tests/unit/test_backtester_v2.py::test_walk_forward_validation_writes_universe_selection_artifact tests/integration/test_minute_backtest.py`
- **Public-operation replay gates:** research_only_insufficient_evidence
  - Evidence: Public operation replay candidates remain 0/5 reproduced and insufficient_evidence for exact date/fill/account fields; this launch does not claim private-ledger reproduction.
  - Source: `specs/004-martinluk-primitive/phase5-bounded-validation-report.json`
- **Bounded backtest evaluation:** pass
  - Evidence: Constrained 2024-01-16..2024-02-16 evaluation with universe size 5 recorded Sharpe 1.0610, deflated SR 0.6770, baseline Sharpe -0.4602, and 8 trades.
  - Source: `experiments/martinluk_t020/t020_positive_window_backtest.log`

## Bounded evaluation summary

- Overall run status: `bounded_evaluation_complete`
- Promoted as public-operation reproduction: `false`
- Public replay candidates: `5`
- Reproduced public replay candidates: `0`
- Public status counts: `{"insufficient_evidence": 5}`
- Public gap classification counts: `{"evidence_not_sufficient": 5}`
- Controls counted toward promotion: `0`
- False-positive control row IDs: `[]`
- Diagnostic promotion veto active: `false`
- Bounded backtest metrics: Sharpe `1.0610`, naive Sharpe `1.0110`, deflated SR `0.6770`, drawdown `-0.0076`, trades `8`, win rate `0.1632`, profit factor `0.5109`, baseline Sharpe `-0.4602`.
- Best no-code full-period cap sweep: universe size `3`, Sharpe `-0.1303`, deflated SR `0.4000`, drawdown `-0.0176`, trades `9`.

## Required next step

Keep public-operation rows insufficient_evidence until cited primary public evidence closes exact date/fill/account fields; treat Sharpe/backtest work as strategy evaluation only.

## Source artifacts

- `experiments/martinluk_t020/t020_positive_window_backtest.log`
- `experiments/martinluk_t020/t020_positive_window_universe.json`
- `.omx/specs/autoresearch-martinluk-t020/result.json`
- `specs/004-martinluk-primitive/phase5-bounded-validation-report.json`
- `specs/004-martinluk-primitive/phase5-7-public-evidence-upgrade-plan.json`
- `specs/004-martinluk-primitive/phase5-7-no-overclaim-closeout.json`
- `specs/004-martinluk-primitive/tasks.md`

## Machine-readable artifact

- `specs/004-martinluk-primitive/phase5-t020-bounded-autoresearch-launch.json`
