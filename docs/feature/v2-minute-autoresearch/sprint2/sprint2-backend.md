> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Sprint 2 — Backend Plan

> Feature: `v2-minute-autoresearch`
> Role: `Backend`
> Derived from: `Issue Draft B — Minute Runtime + Validation Alignment`
> Last Updated: `2026-04-09`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `docs/data-pipeline-v2.md`
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md`

## 1) Sprint Mission

- Define how the runtime converges on the minute-level mission while preserving the backtester as a hard invariant and final judge.

## 2) Scope / Out of Scope

**Scope**
- minute-level mission contract
- runtime/data alignment
- backtester invariants

**Out of Scope**
- stock-discussion and factor-mining specifics

## 3) Step-by-Step Plan

### Step 1 — Define minute-level mission enforcement
- [x] define what it means for strategy-facing work to be truly minute-level
- [x] define what current daily-style behavior is no longer acceptable
- [x] define how minute-level purpose constrains future runtime surfaces

### Step 2 — Preserve validation invariants
- [x] define the invariants that may not regress: sandbox, walk-forward, forced lag, metrics
- [x] define what parts of the backtester are architecture-level constraints rather than implementation details
- [x] define how keep / revert depends on validation outputs

### Step 3 — Define runtime convergence targets
- [x] define the current-state vs target-state gap for runtime/data flow
- [x] define the sequencing for closing that gap without losing validation integrity

## 4) Test Plan

- [x] verify the sprint keeps the backtester as final authority
- [x] verify minute-level purpose is explicit
- [x] verify no architecture drift back into generic daily research

## 5) Verification Commands

```bash
rg -n "minute|intraday|backtester|walk-forward|sandbox|forced lag" docs/feature/v2-minute-autoresearch/sprint2 -S
```

## 6) Implementation Update Space

### Completed Work

- Disabled the top-level legacy runtime fallback in `walk_forward_validation()` so V2 minute mode now fails explicitly when daily DuckDB prerequisites are missing instead of silently dropping into the legacy cache-based runtime.
- Documented the runtime conclusion that strategy-facing execution must stay minute-level, while the backtester invariants (sandbox, walk-forward, forced lag, metrics) remain non-negotiable.
- Confirmed the surviving minute pipeline is the primary runtime path and treated the remaining legacy helper code as compatibility scaffolding rather than the allowed execution path for V2.

### Command Results

- `uv run pytest tests/unit/test_backtester_v2.py -q` → `38 passed`
- `uv run pytest tests/unit/test_cli.py tests/unit/test_backtester_v2.py tests/unit/test_duckdb_connector.py tests/integration/test_minute_backtest.py -q` → `87 passed`

### Blockers / Deviations

- Legacy helper functions still exist in `src/core/backtester.py`, but the public V2 execution path no longer falls back to them when minute-mode prerequisites are absent.

### Follow-ups

- If later cleanup is desired, remove or quarantine the remaining legacy helper code only after confirming no surviving tests or operators still rely on it.
- Keep future runtime work aligned to the minute pipeline rather than reintroducing daily-cache fallback behavior.
