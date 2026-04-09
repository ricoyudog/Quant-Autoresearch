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
- [ ] define what it means for strategy-facing work to be truly minute-level
- [ ] define what current daily-style behavior is no longer acceptable
- [ ] define how minute-level purpose constrains future runtime surfaces

### Step 2 — Preserve validation invariants
- [ ] define the invariants that may not regress: sandbox, walk-forward, forced lag, metrics
- [ ] define what parts of the backtester are architecture-level constraints rather than implementation details
- [ ] define how keep / revert depends on validation outputs

### Step 3 — Define runtime convergence targets
- [ ] define the current-state vs target-state gap for runtime/data flow
- [ ] define the sequencing for closing that gap without losing validation integrity

## 4) Test Plan

- [ ] verify the sprint keeps the backtester as final authority
- [ ] verify minute-level purpose is explicit
- [ ] verify no architecture drift back into generic daily research

## 5) Verification Commands

```bash
rg -n "minute|intraday|backtester|walk-forward|sandbox|forced lag" docs/feature/v2-minute-autoresearch/sprint2 -S
```

## 6) Implementation Update Space

### Completed Work

- leave blank until implemented

### Command Results

- leave blank until implemented

### Blockers / Deviations

- leave blank until implemented

### Follow-ups

- leave blank until implemented

