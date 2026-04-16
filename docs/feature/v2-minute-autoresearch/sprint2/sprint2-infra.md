> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Sprint 2 — Infra Plan

> Feature: `v2-minute-autoresearch`
> Role: `Infra`
> Derived from: `Issue Draft B — Minute Runtime + Validation Alignment`
> Last Updated: `2026-04-09`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `docs/data-pipeline-v2.md`
3. `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-infra.md`

## 1) Sprint Mission

- Define the infrastructure assumptions needed for a real minute-level runtime and ensure they stay aligned with the merge target.

## 2) Scope / Out of Scope

**Scope**
- minute-data prerequisites
- environment/data assumptions
- merge-target documentation

**Out of Scope**
- strategy-discussion content
- factor-mining behavior

## 3) Step-by-Step Plan

### Step 1 — Define minute-data prerequisites
- [x] define required data sources and local datasets
- [x] define what is optional vs mandatory
- [x] define the failure mode when minute-level prerequisites are absent

### Step 2 — Define merge-target and baseline assumptions
- [x] define `main-dev` as the merge target baseline
- [x] define how future execution should avoid stale branch drift

### Step 3 — Define infrastructure risks
- [x] document performance, storage, and environment risks for minute-level operation
- [x] document any blockers that could delay runtime convergence

## 4) Test Plan

- [x] verify minute-level prerequisites are explicit
- [x] verify branch/merge assumptions are explicit
- [x] verify infra risks are documented before execution

## 5) Verification Commands

```bash
rg -n "minute|dataset|main-dev|merge target|risk|prerequisite" docs/feature/v2-minute-autoresearch/sprint2 -S
```

## 6) Implementation Update Space

### Completed Work

- Verified that the minute-mode runtime now requires daily DuckDB data and fails with a stable `DATA ERROR` when those prerequisites are absent.
- Confirmed that `main-dev` is the correct merge target baseline for this issue branch.
- Confirmed the primary minute runtime still depends on the DuckDB daily cache plus minute-bar queries, and that this path remains the required execution surface for V2.

### Command Results

- `uv run pytest tests/unit/test_backtester_v2.py -q` → `38 passed`
- `uv run pytest tests/unit/test_cli.py tests/unit/test_backtester_v2.py tests/unit/test_duckdb_connector.py tests/integration/test_minute_backtest.py -q` → `87 passed`

### Blockers / Deviations

- Local datasets / minute CLI availability remain environmental dependencies; the code now reports their absence explicitly instead of masking it behind a legacy fallback.

### Follow-ups

- Preserve the explicit failure mode for missing minute prerequisites in later runtime work.
- Review whether the remaining legacy cache helpers should be isolated further once no tests depend on them.
