> Status: historical
>
> This workspace is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Phase 1 — Backtester Upgrades + program.md + Strategy Interface

## Overview

Phase 1 of the V2 upgrade. Upgrades the backtester with full metrics suite and dynamic class loading, creates the root `program.md` agent instruction file, and removes the EDITABLE REGION markers from `active_strategy.py`.

## Branch

`feature/v2-phase1`

## Issues

| Issue | Scope | Status |
| --- | --- | --- |
| [#8](https://github.com/ricoyudog/Quant-Autoresearch/issues/8) | Phase 1: Backtester + program.md + strategy interface | complete |

## Execution Order

```
Sprint 1 (backtester core) → Sprint 2 (program.md + strategy + tests)
```

Sprint 2 depends on Sprint 1: tests in Sprint 2 validate the functions added in Sprint 1.

## Docs

- [v2-phase1-development-plan.md](./v2-phase1-development-plan.md) — Main development plan with task detail
- [v2-phase1-test-plan.md](./v2-phase1-test-plan.md) — Verification and test plan

## Sprints

- [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md) — Backtester core upgrades (find_strategy_class, calculate_metrics, baseline, per-symbol, output format)
- [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md) — program.md + strategy interface + tests

## Governing Specs

- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) — Complete V2 upgrade design (Section 5 program.md, Section 7 backtester, Section 8 tests, Phase 1 in Section 9)
- [CLAUDE.md](../../../CLAUDE.md) — Current architecture reference
