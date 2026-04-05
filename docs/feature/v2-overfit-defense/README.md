# V2 Overfit Defense — Multi-Layer Overfit Defense Architecture

## Overview

Session 3 feature. Builds a multi-layer overfit defense architecture based on Lopez de Prado, Bailey et al. academic research. Layer 1 (built-in, every backtest) adds Newey-West Sharpe and Deflated Sharpe Ratio, removes Monte Carlo. Layer 2 (on-demand CLI) adds CPCV validation, regime robustness check, and parameter stability testing.

## Branch

`feature/v2-overfit-defense`

## Dependency

Phase 1 (issue #8) must be complete: backtester upgrades (dynamic class loading, multi-metric output, Buy&Hold baseline, Per-Symbol split, walk-forward 5 windows).

## Issues

| Issue | Scope | Status |
| --- | --- | --- |
| #12 | Umbrella: Session 3 Overfit Defense | review |
| Sprint 1 | Newey-West Sharpe + Deflated SR + remove Monte Carlo | complete |
| Sprint 2 | CPCV CLI + Regime check + Param stability | complete |

## Execution Order

```
Sprint 1 → Sprint 2
```

Sprint 2 depends on Sprint 1 (Newey-West Sharpe is used by regime analysis).

## Docs

- [v2-overfit-defense-development-plan.md](./v2-overfit-defense-development-plan.md) — Main development plan with task detail
- [v2-overfit-defense-test-plan.md](./v2-overfit-defense-test-plan.md) — Verification and test plan
- [overfit-defense-knowledge-base.md](./overfit-defense-knowledge-base.md) — Research note for Sprint 2 validation methods

## Sprint Docs

- [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md) — Sprint 1 closeout complete; ready to proceed to Sprint 2
- [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md) — Sprint 2 complete; verification synced and ready for review

## Governing Specs

- [overfit-defense-v2.md](../../overfit-defense-v2.md) — Complete overfit defense design specification
- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) — V2 upgrade plan (Phase 1 backtester changes)
- [CLAUDE.md](../../../CLAUDE.md) — Project architecture reference
