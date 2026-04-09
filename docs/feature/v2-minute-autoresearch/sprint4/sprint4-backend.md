# Sprint 4 — Backend Plan

> Feature: `v2-minute-autoresearch`
> Role: `Backend`
> Derived from: `Issue Draft D — Optional Factor-Mining Lane`
> Last Updated: `2026-04-09`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `docs/research-karpathy-autoresearch.md`
3. `docs/research-tradingagents.md`

## 1) Sprint Mission

- Define factor mining as an optional sub-mode of autoresearch that discovers new candidate features/factors only when the main loop needs them.

## 2) Scope / Out of Scope

**Scope**
- factor-mining triggers
- factor candidate generation
- result-based factor evaluation

**Out of Scope**
- mandatory factor mining every cycle
- standalone factor-mining product flow

## 3) Step-by-Step Plan

### Step 1 — Define trigger criteria
- [ ] define when the main loop should invoke factor mining
- [ ] define what symptoms or needs justify it

### Step 2 — Define candidate integration
- [ ] define how mined factors become strategy candidates
- [ ] define how they remain subordinate to the main autoresearch idea loop

### Step 3 — Define outcome judgment
- [ ] define that factor quality is only meaningful through improved validated results
- [ ] define how poor-result factors are discarded

## 4) Test Plan

- [ ] verify factor mining is optional
- [ ] verify factor ideas stay under autoresearch
- [ ] verify backtester remains the outcome judge

## 5) Verification Commands

```bash
rg -n "factor mining|optional|candidate|results|backtester" docs/feature/v2-minute-autoresearch/sprint4 -S
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

