> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Data Pipeline -- Backend Lane Plan

> Feature branch: `feature/v2-data-pipeline`
> Role: Backend
> Historical workspace: `docs/feature/v2-data-pipeline/`
> Last updated: 2026-04-05

## Mission

Implement the code-surface changes that move the project from the legacy data-loader pair
(`connector.py`, `preprocessor.py`) to a DuckDB daily cache plus minute-level query pipeline. This
lane owns the runtime contracts between the data layer, the strategy interface, the backtester, and
the CLI.

## Code Surface

| Surface | Sprint | Contract |
| --- | --- | --- |
| `src/data/duckdb_connector.py` | Sprint 1 | build/load DuckDB daily cache, expose trading days, bridge minute-data queries |
| `src/core/backtester.py` | Sprint 2 | load daily data, run universe selection, validate minute-window completeness, compute trading-day windows, evaluate minute-data signals, and report portfolio/per-symbol metrics |
| `src/strategies/active_strategy.py` | Sprint 2 | expose `select_universe(daily_data)` and minute-data `generate_signals()` example |
| `cli.py` | Sprint 1 + Sprint 3 | build cache, fetch minute bars, backtest minute mode, refresh the cache incrementally via `update-data` |
| `program.md` / `CLAUDE.md` | Sprint 3 | document the final backend/runtime contracts once implementation settles |

## Cross-Sprint Contract Decisions

- Daily data is the screening surface. Minute data is loaded only for the selected universe and only
  for the current walk-forward window, and each window must contain the full selected ticker set.
- `select_universe(daily_data)` is optional. If omitted, the backtester must still have a safe
  fallback universe rule.
- `generate_signals(minute_data)` works on `dict[str, pd.DataFrame]` keyed by ticker and must still
  honor the existing lag and sandbox rules.
- `walk_forward_validation()` must fail fast on empty or incomplete minute windows instead of
  silently skipping them.
- Portfolio trade metrics are computed from gross exposure plus summed per-symbol trade activity, so
  offsetting books still report non-zero trading activity.
- The CLI remains the operator-facing surface for cache build, fetch, backtest, and refresh flows.

## Backend Deliverables

| Task ID | Deliverable | Sprint | Dependency | Acceptance |
| --- | --- | --- | --- | --- |
| DUCK-02 | Add `duckdb` dependency and implement DuckDB helper module | Sprint 1 | INFRA-01, DUCK-01 | cache build/load helpers import cleanly and match the planned schema |
| DUCK-03 | Replace `setup-data` and retire the old data-loader modules | Sprint 1 | DUCK-02 | `setup-data` builds DuckDB cache and legacy modules are no longer referenced |
| STRAT-01 | Extend the strategy contract | Sprint 2 | Sprint 1 complete | `select_universe(daily_data)` and minute-data `generate_signals()` are callable |
| STRAT-02 | Update backtester discovery and trading-day window logic | Sprint 2 | STRAT-01 | backtester detects the optional universe step and computes valid windows |
| STRAT-03 | Integrate daily -> universe -> minute -> signals flow | Sprint 2 | STRAT-02 | minute-level walk-forward runs through full evaluation |
| CLI-01 | Update `fetch`, `backtest`, and `update-data` | Sprint 3 | Sprint 2 complete | CLI behavior matches the DuckDB/minute-data runtime model |
| DOC-01 | Update runtime docs after implementation stabilizes | Sprint 3 | CLI-01 | `program.md` and `CLAUDE.md` describe the new backend flow accurately |

## Execution Handoff

Use the sprint docs as the execution queue:

- [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md)
- [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md)
- [sprint3/sprint3-backend.md](./sprint3/sprint3-backend.md)

This lane doc is the cross-sprint contract summary. It does not replace the sprint-level
step-by-step plans.

## Backend Acceptance

- [x] The old data-loader modules are fully retired
- [x] The backtester supports the dual-stage daily/minute pipeline
- [x] The strategy example demonstrates the new interface clearly
- [x] CLI commands expose the new runtime model without hidden manual steps
- [x] Runtime docs match the implemented behavior

## Backend Risks

| Risk | Mitigation |
| --- | --- |
| Contract drift between DuckDB helpers and backtester integration | Keep helper function names and schemas explicit in Sprint 1 before Sprint 2 begins |
| Strategy API changes break existing tests or sandbox expectations | Expand `tests/unit/test_strategy_interface.py` before declaring Sprint 2 complete |
| CLI behavior diverges from the runtime docs | Treat Sprint 3 docs updates as part of the implementation definition of done |
