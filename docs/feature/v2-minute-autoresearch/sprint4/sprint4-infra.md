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
- [x] define how factor-mining failure should not stall the main loop unnecessarily
- [x] define when the lane should be skipped entirely

Once a factor hook clears Step 2 and becomes a promoted factor-derived candidate, infra treats it as an ordinary
candidate that remains `pending_backtest` until the existing validation path produces a real outcome. Factor novelty,
proposal rhetoric, or raw hook quality does not create a second success/failure score.

- If Step 2 gating cannot materialize one canonical proposal record, factor mining is skipped for that loop iteration
  and the main minute-autoresearch mission continues unchanged.
- If a promoted factor-derived candidate later produces weak or failed validated results, it is removed through the
  existing keep/revert outcome used for every other candidate; Step 3 does not add a new factor-specific scoring or
  review authority.
- If factor mining is noisy, incomplete, or temporarily unhelpful, the system may defer another attempt to a later
  loop; this is a local skip/defer decision inside the current mission, not a license to redefine the mission or spin
  up a parallel decision-maker.
- Step 3 does not claim any new artifact persistence; the currently documented lineage ceiling remains
  `candidate_id`, `idea_trace`, `analysis_context.path`, `analysis_context.title`, `artifacts.results_tsv`, and
  `artifacts.experiment_note`.

## 4) Test Plan

- [x] verify factor mining remains optional
- [x] verify canonical proposal promotion gating is explicit
- [x] verify lineage claims stop at currently persisted keep/revert fields
- [x] verify failure does not silently redefine the system mission

## 5) Verification Commands

```bash
rg -n "canonical proposal|hook_id|seed_type|candidate_hooks|traceability|contrarian_observations|candidate_id|idea_trace|analysis_context|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S
rg -n "candidate_hooks|traceability|contrarian_observations|hook_id|seed_type|build_candidate_strategy_hypothesis|idea_context\\.path|idea_context\\.source|idea_context\\.title|market_context\\.source|market_context\\.summary|idea_trace|analysis_context|results_tsv|experiment_note" src tests -S
rg -n "pending_backtest|backtester_required|backtester_outcome_only|keep/revert|discard|revert|skip|defer|mission" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S
uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q
```

## 6) Implementation Update Space

### Completed Work

- Defined the Step 2 promotion boundary as `packet -> canonical proposal -> candidate`: raw `candidate_hooks` remain research input only and cannot bypass canonical proposal materialization before `build_candidate_strategy_hypothesis()`.
- Defined the canonical proposal record to carry `idea_context.path`, `idea_context.source`, `idea_context.title`, exactly one supported seed family from `query|topic|tickers`, proposal-note provenance, `market_context.source`, `market_context.summary`, plus the original `candidate_hooks`, `traceability`, and `contrarian_observations`.
- Defined Step 2 gating to block promotion when `hook_id` is empty, the selected seed family is unsupported or has an empty payload, proposal note path/title/source is missing, or `market_context.source` / `market_context.summary` cannot be materialized as explicit non-empty canonical proposal fields.
- Limited lineage claims to currently real downstream surfaces only: `candidate_id`, `idea_trace`, `analysis_context.path`, `analysis_context.title`, `artifacts.results_tsv`, and `artifacts.experiment_note`; raw hook-level keep/revert lineage is not yet persisted and is documented as out of scope for this step.
- Defined the Step 3 result boundary so promoted factor-derived candidates stay `pending_backtest` until the existing
  candidate/backtest path yields a validated outcome.
- Bound poor-result factor proposals and candidates to the same keep/revert elimination rule already used elsewhere;
  Step 3 rejects new factor-specific scoring, ranking, or manual approval authority.
- Defined skip/defer behavior for incomplete or low-value factor-mining attempts so the optional lane can be skipped or
  retried later without redefining the system mission.
- Kept persistence claims unchanged: Step 3 does not assert any new hook-level, proposal-level, or factor-level
  artifact storage beyond the currently real keep/revert surfaces.

### Command Results

- `rg -n "canonical proposal|hook_id|seed_type|candidate_hooks|traceability|contrarian_observations|candidate_id|idea_trace|analysis_context|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S` → confirmed the Step 2 docs now state canonical proposal promotion, hook/seed gating, and the narrowed lineage ceiling.
- `rg -n "candidate_hooks|traceability|contrarian_observations|hook_id|seed_type|build_candidate_strategy_hypothesis|idea_context\\.path|idea_context\\.source|idea_context\\.title|market_context\\.source|market_context\\.summary|idea_trace|analysis_context|results_tsv|experiment_note" src tests -S` → confirmed the docs match current packet names, candidate-generation inputs, and keep/revert artifact surfaces.
- `rg -n "pending_backtest|backtester_required|backtester_outcome_only|keep/revert|discard|revert|skip|defer|mission" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S` → confirms Step 3 now documents `pending_backtest`, backtester-owned keep/revert judgment, skip/defer handling, and the no-mission-redefinition rule without claiming new persistence.
- `uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q` → `11 passed`

### Blockers / Deviations

- No new infra blockers remain after Step 3 doc closeout.
- Keep/revert storage still does not persist raw `hook_id`, `candidate_hooks`, or `contrarian_observations`; the docs intentionally stop short of claiming that deeper lineage.

### Follow-ups

- Issue-level closeout should move the next-step pointer to review / PR once the Step 3 docs and issue card are synchronized.
