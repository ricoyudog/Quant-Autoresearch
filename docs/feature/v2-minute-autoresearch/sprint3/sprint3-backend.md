# Sprint 3 — Backend Plan

> Feature: `v2-minute-autoresearch`
> Role: `Backend`
> Derived from: `Issue Draft C — Strategy-Facing Stock Discussion Lane`
> Last Updated: `2026-04-09`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `docs/research-tradingagents.md`
3. `docs/research-capabilities-v2.md`

## 1) Sprint Mission

- Define a TradingAgents-inspired stock-discussion structure that serves strategy refinement without becoming a separate decision engine.

## 2) Scope / Out of Scope

**Scope**
- strategy-facing stock discussion structure
- integration into autoresearch
- boundary with lightweight `analyze`

**Out of Scope**
- generic portfolio advice
- full debate-runtime orchestration

## 3) Step-by-Step Plan

### Step 1 — Define discussion entry points
- [ ] define when stock discussion is triggered inside autoresearch
- [ ] define what strategy questions it should answer
- [ ] define what it must not absorb

### Step 2 — Define output shape
- [ ] define the structured discussion output
- [ ] define how it feeds strategy hypotheses instead of final buy/sell decisions
- [ ] define how negative / contrarian reasoning is preserved

### Step 3 — Define `analyze` boundary
- [ ] define what remains a deterministic snapshot
- [ ] define what escalates into full strategy-facing discussion

## 4) Test Plan

- [ ] verify TradingAgents borrowing stays structural only
- [ ] verify the lane remains strategy-facing only
- [ ] verify `analyze` boundary remains explicit

## 5) Verification Commands

```bash
rg -n "TradingAgents|stock discussion|analyze|strategy-facing|contrarian" docs/feature/v2-minute-autoresearch/sprint3 -S
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

