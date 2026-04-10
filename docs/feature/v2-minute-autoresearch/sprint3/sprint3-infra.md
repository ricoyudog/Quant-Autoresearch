# Sprint 3 — Infra Plan

> Feature: `v2-minute-autoresearch`
> Role: `Infra`
> Derived from: `Issue Draft C — Strategy-Facing Stock Discussion Lane`
> Last Updated: `2026-04-10`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `docs/research-tradingagents.md`
3. `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-infra.md`

## 1) Sprint Mission

- Define the supporting data/runtime assumptions for the stock-discussion lane without letting it drift into a generic investing-analysis tool.

## 2) Scope / Out of Scope

**Scope**
- supporting data assumptions
- runtime constraints
- traceability of discussion outputs

**Out of Scope**
- factor mining
- minute runtime core data pipeline

## 3) Step-by-Step Plan

### Step 1 — Define data assumptions
- [x] define what market context the lane may consume
- [x] define what remains deterministic vs research-driven

### Step 2 — Define runtime constraints
- [ ] define what prevents this lane from becoming a separate decision product
- [ ] define how results stay subordinate to the backtester

### Step 3 — Define traceability expectations
- [ ] define how discussion outputs are recorded
- [ ] define how they link back to strategy candidate generation

## 4) Test Plan

- [x] verify discussion routing does not masquerade as final decisions
- [ ] verify traceability back to strategy refinement exists

## 5) Verification Commands

```bash
rg -n "traceability|discussion|decision|backtester|deterministic" docs/feature/v2-minute-autoresearch/sprint3 -S
```

## 6) Implementation Update Space

### Completed Work

- Defined the first infrastructure/runtime boundary for Sprint 3: deterministic snapshot market-state questions remain on the `analyze` path, while strategy-facing minute/intraday/liquidity/universe questions escalate into the stock-discussion lane.
- Confirmed the lane stays subordinate to the backtester and does not become a separate decision engine.

### Command Results

- `uv run pytest tests/unit/test_discussion_routing.py -q` → `3 passed`
- `uv run pytest tests/unit/test_cli_analyze.py tests/unit/test_market_context.py tests/unit/test_regime.py tests/unit/test_technical.py tests/integration/test_analyze_pipeline.py tests/unit/test_discussion_routing.py -q` → `28 passed`
- `uv run python -m compileall src cli.py` → completed without compile errors

### Blockers / Deviations

- The traceability record for strategy-facing discussion outputs is still an open follow-up for the next slice.

### Follow-ups

- Next slice should define the structured discussion artifact and how it links back to later strategy candidate generation.
