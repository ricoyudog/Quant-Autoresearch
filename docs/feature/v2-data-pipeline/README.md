# V2 Data Pipeline — DuckDB + Minute-Level Backtesting

## Overview

Session 2 of the V2 upgrade. Redesigns the data pipeline to use the local massive-minute-aggs dataset (US Stocks SIP, 11K+ tickers, minute-level) with DuckDB for daily aggregation caching, strategy-driven universe selection, and minute-level walk-forward backtesting.

## Branch

`feature/v2-data-pipeline`

## Dependency

Phase 1 (issue #8) must be complete before this work begins. The v2-cleanup branch should be merged.

## Issues

| Issue | Scope | Status |
| --- | --- | --- |
| #11 | Umbrella: Data Pipeline V2 | pending |
| sub-issue | Sprint 1: DuckDB integration + daily cache | pending |
| sub-issue | Sprint 2: Strategy interface + backtester integration | pending |
| sub-issue | Sprint 3: CLI commands + tests | pending |

## Execution Order

```
Sprint 1 (DuckDB + daily cache) → Sprint 2 (strategy + backtester) → Sprint 3 (CLI + tests)
```

Each sprint depends on the previous one. Sprint 3 is the final verification gate.

## Docs

- [v2-data-pipeline-development-plan.md](./v2-data-pipeline-development-plan.md) -- Main development plan with task detail
- [v2-data-pipeline-test-plan.md](./v2-data-pipeline-test-plan.md) -- Verification and test plan
- [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md) -- Sprint 1: DuckDB integration + daily cache
- [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md) -- Sprint 2: Strategy interface + backtester integration
- [sprint3/sprint3-backend.md](./sprint3/sprint3-backend.md) -- Sprint 3: CLI commands + tests

## Governing Specs

- [data-pipeline-v2.md](../../data-pipeline-v2.md) -- Full data pipeline design specification
- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) -- Complete V2 upgrade design
- [CLAUDE.md](../../../CLAUDE.md) -- Project architecture reference
