> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

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
- [x] define the structured discussion output
- [x] define how it feeds strategy hypotheses instead of final buy/sell decisions
- [x] define how negative / contrarian reasoning is preserved

### Step 3 — Define `analyze` boundary
- [x] define what remains a deterministic snapshot
- [x] define what escalates into full strategy-facing discussion

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
- Added `src/analysis/discussion_packet.py` with `build_strategy_discussion_packet()` so strategy-facing discussion now emits a stable packet contract instead of ad hoc output.
- Preserved explicit contrarian reasoning via `contrarian_observations`, kept the lane non-decision-making via `decision_guard`, and carried a future handoff surface via `candidate_hooks` and `traceability`.
- Landed a post-merge review fix on `main-dev` (`ec6240f`) so deterministic snapshot-style intraday/minute questions stay on `analyze` unless explicit strategy intent is present.
- Added regression coverage in `tests/unit/test_discussion_routing.py` for intraday snapshot wording and minute-context snapshot queries so the analyze-vs-discussion boundary now matches the intended Sprint 3 contract under realistic inputs.

### Command Results

- `uv run pytest tests/unit/test_discussion_packet.py -q` → `3 passed`
- `uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_discussion_routing.py tests/unit/test_cli_analyze.py tests/integration/test_analyze_pipeline.py -q` → `13 passed`
- `uv run pytest tests/unit/test_discussion_routing.py -q` → `3 passed`
- `uv run pytest tests/unit/test_cli_analyze.py tests/unit/test_market_context.py tests/unit/test_regime.py tests/unit/test_technical.py tests/integration/test_analyze_pipeline.py tests/unit/test_discussion_routing.py -q` → `28 passed`
- `uv run python -m compileall src cli.py` → completed without compile errors
- `uv run pytest tests/unit/test_discussion_routing.py tests/unit/test_cli_analyze.py tests/integration/test_analyze_pipeline.py -q` → `14 passed`
- `uv run python -m compileall src cli.py` → passed after the routing review fix on `main-dev`

### Blockers / Deviations

- No new backend blockers remain in Sprint 3 after the packet contract landed.
- A post-merge review finding showed that generic `minute` / `intraday` wording could over-escalate deterministic snapshot questions into the discussion lane; this was fixed on `main-dev` without reopening the broader Sprint 3 scope.

### Follow-ups

- When the runtime loop starts consuming discussion packets, keep the handoff aligned with Sprint 1 candidate-generation / keep-revert schemas.
- Keep future routing edits snapshot-first unless there is explicit strategy intent, so minute-mode runtime questions do not regress back into over-escalation.
