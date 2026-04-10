# Sprint 3 — Backend Plan

> Feature: `v2-minute-autoresearch`
> Role: `Backend`
> Derived from: `Issue Draft C — Strategy-Facing Stock Discussion Lane`
> Last Updated: `2026-04-10`

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
- [x] define when stock discussion is triggered inside autoresearch
- [x] define what strategy questions it should answer
- [x] define what it must not absorb

### Step 2 — Define output shape
- [ ] define the structured discussion output
- [ ] define how it feeds strategy hypotheses instead of final buy/sell decisions
- [ ] define how negative / contrarian reasoning is preserved

### Step 3 — Define `analyze` boundary
- [ ] define what remains a deterministic snapshot
- [ ] define what escalates into full strategy-facing discussion

## 4) Test Plan

- [x] verify TradingAgents borrowing stays structural only
- [x] verify the lane remains strategy-facing only
- [x] verify `analyze` boundary remains explicit

## 5) Verification Commands

```bash
rg -n "TradingAgents|stock discussion|analyze|strategy-facing|contrarian" docs/feature/v2-minute-autoresearch/sprint3 -S
```

## 6) Implementation Update Space

### Completed Work

- Added `src/analysis/discussion_routing.py` with `route_stock_question()` so the runtime can distinguish lightweight snapshot analysis from strategy-facing stock discussion.
- Locked the boundary that simple regime/state questions stay in `analyze`, while minute/intraday/liquidity/universe-selection questions escalate into the strategy-stock-discussion lane.

### Command Results

- `uv run pytest tests/unit/test_discussion_routing.py -q` → `3 passed`
- `uv run pytest tests/unit/test_cli_analyze.py tests/unit/test_market_context.py tests/unit/test_regime.py tests/unit/test_technical.py tests/integration/test_analyze_pipeline.py tests/unit/test_discussion_routing.py -q` → `28 passed`
- `uv run python -m compileall src cli.py` → completed without compile errors

### Blockers / Deviations

- Output-shape design and final documentation of the discussion packet still remain for later Sprint 3 slices.

### Follow-ups

- Next slice should define the structured output of the strategy-facing stock discussion itself, not just the routing boundary.
