# Sprint 4 — Infra Plan

> Feature: `v2-minute-autoresearch`
> Role: `Infra`
> Derived from: `Issue Draft D — Optional Factor-Mining Lane`
> Last Updated: `2026-04-10`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-infra.md`

## 1) Sprint Mission

- Define the supporting constraints for optional factor mining so it remains lightweight, traceable, and subordinate to the main autoresearch loop.

## 2) Scope / Out of Scope

**Scope**
- trigger environment assumptions
- storage / traceability expectations
- failure boundaries

**Out of Scope**
- generic factor library productization

## 3) Step-by-Step Plan

### Step 1 — Define environment assumptions
- [x] define what data or compute assumptions factor mining may rely on
- [x] define how it degrades when those assumptions are missing

### Step 2 — Define canonical proposal traceability/storage
- [x] define the canonical proposal record required before raw factor hooks can reach candidate generation
- [x] define the blocking rules for `hook_id`, supported seeds, note provenance, market context, and honest downstream lineage

### Step 3 — Define failure boundaries
- [ ] define how factor-mining failure should not stall the main loop unnecessarily
- [ ] define when the lane should be skipped entirely

## 4) Test Plan

- [x] verify factor mining remains optional
- [x] verify canonical proposal promotion gating is explicit
- [x] verify lineage claims stop at currently persisted keep/revert fields
- [ ] verify failure does not silently redefine the system mission

## 5) Verification Commands

```bash
rg -n "canonical proposal|hook_id|seed_type|candidate_hooks|traceability|contrarian_observations|candidate_id|idea_trace|analysis_context|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S
rg -n "candidate_hooks|traceability|contrarian_observations|hook_id|seed_type|build_candidate_strategy_hypothesis|idea_context\\.path|idea_context\\.source|idea_context\\.title|market_context\\.source|market_context\\.summary|idea_trace|analysis_context|results_tsv|experiment_note" src tests -S
uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q
```

## 6) Implementation Update Space

### Completed Work

- Defined the Step 2 promotion boundary as `packet -> canonical proposal -> candidate`: raw `candidate_hooks` remain research input only and cannot bypass canonical proposal materialization before `build_candidate_strategy_hypothesis()`.
- Defined the canonical proposal record to carry `idea_context.path`, `idea_context.source`, `idea_context.title`, exactly one supported seed family from `query|topic|tickers`, proposal-note provenance, `market_context.source`, `market_context.summary`, plus the original `candidate_hooks`, `traceability`, and `contrarian_observations`.
- Defined Step 2 gating to block promotion when `hook_id` is empty, the selected seed family is unsupported or has an empty payload, proposal note path/title/source is missing, or `market_context.source` / `market_context.summary` cannot be materialized as explicit non-empty canonical proposal fields.
- Limited lineage claims to currently real downstream surfaces only: `candidate_id`, `idea_trace`, `analysis_context.path`, `analysis_context.title`, `artifacts.results_tsv`, and `artifacts.experiment_note`; raw hook-level keep/revert lineage is not yet persisted and is documented as out of scope for this step.

### Command Results

- `rg -n "canonical proposal|hook_id|seed_type|candidate_hooks|traceability|contrarian_observations|candidate_id|idea_trace|analysis_context|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S` → confirmed the Step 2 docs now state canonical proposal promotion, hook/seed gating, and the narrowed lineage ceiling.
- `rg -n "candidate_hooks|traceability|contrarian_observations|hook_id|seed_type|build_candidate_strategy_hypothesis|idea_context\\.path|idea_context\\.source|idea_context\\.title|market_context\\.source|market_context\\.summary|idea_trace|analysis_context|results_tsv|experiment_note" src tests -S` → confirmed the docs match current packet names, candidate-generation inputs, and keep/revert artifact surfaces.
- `uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q` → `11 passed`

### Blockers / Deviations

- No new infra blockers remain after Step 2.
- Keep/revert storage still does not persist raw `hook_id`, `candidate_hooks`, or `contrarian_observations`; the docs intentionally stop short of claiming that deeper lineage.

### Follow-ups

- Step 3 should define failure-boundary behavior for rejected or incomplete canonical proposals without broadening into new keep/revert judgment semantics.
