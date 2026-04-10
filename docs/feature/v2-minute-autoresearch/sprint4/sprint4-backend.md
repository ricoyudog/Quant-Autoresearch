# Sprint 4 — Backend Plan

> Feature: `v2-minute-autoresearch`
> Role: `Backend`
> Derived from: `Issue Draft D — Optional Factor-Mining Lane`
> Last Updated: `2026-04-10`

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
- [x] define when the main loop should invoke factor mining
- [x] define what symptoms or needs justify it

### Step 2 — Define candidate integration
- [x] define how mined factors become strategy candidates
- [x] define how they remain subordinate to the main autoresearch idea loop
- [x] define the canonical promotion boundary before candidate generation
- [x] define the minimum mapping and gating fields required for promotion

Factor mining remains research input only until the minute-level autoresearch loop promotes one selected hook into a
canonical proposal record. Raw `candidate_hooks` cannot bypass this canonicalization boundary, and factor mining must
not call `build_candidate_strategy_hypothesis()` directly or create a second candidate lane.

Promotion is blocked unless the selected hook has a non-empty `hook_id`, the seed is explicitly supported, the seed
payload is non-empty, the proposal note identity is real, and the packet carries explicit non-empty market context.

| Canonical field | Source | Required rule |
| --- | --- | --- |
| `idea_context.path` | proposal note path | must be a non-empty real note path; no guessed fallback |
| `idea_context.source` | proposal note origin | map only to the existing note-origin values `research` or `knowledge`; do not guess new labels |
| `idea_context.title` | proposal note title | must be a non-empty note title from the promoted proposal |
| `market_context.source` | canonical proposal record field | copy packet `traceability.analysis_context.source` only when present; otherwise promotion stays blocked until a non-empty value is captured explicitly |
| `market_context.summary` | canonical proposal record field | copy packet `traceability.analysis_context.summary` only when present; otherwise promotion stays blocked until a non-empty value is captured explicitly |

| Supported `seed_type` | Required payload |
| --- | --- |
| `query` | non-empty query string |
| `topic` | non-empty topic string |
| `tickers` | non-empty ticker list |

The canonical proposal may then flow through the existing `build_candidate_strategy_hypothesis()` path and carry its
lineage forward only through the currently real downstream surfaces: `candidate_id`, `idea_trace`,
`analysis_context.path`, `analysis_context.title`, `artifacts.results_tsv`, and `artifacts.experiment_note`.

### Step 3 — Define outcome judgment
- [ ] define that factor quality is only meaningful through improved validated results
- [ ] define how poor-result factors are discarded

## 4) Test Plan

- [ ] verify factor mining is optional
- [x] verify factor ideas stay under autoresearch
- [ ] verify backtester remains the outcome judge

## 5) Verification Commands

```bash
rg -n "Step 2|candidate integration|canonical proposal|promotion blocked|raw hooks|hook_id|contrarian_observations|traceability" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md docs/feature/v2-minute-autoresearch/sprint4/sprint4-infra.md docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S
```

## 6) Implementation Update Space

### Completed Work

- Defined the Step 2 promotion boundary so factor mining stays research-input-only until the minute autoresearch loop materializes one canonical proposal record from a selected hook.
- Locked the raw-hook boundary explicitly: raw `candidate_hooks` cannot bypass canonicalization, cannot call `build_candidate_strategy_hypothesis()` directly, and cannot create a second candidate lane.
- Added a no-guess mapping table for `idea_context.path`, `idea_context.source`, `idea_context.title`, `market_context.source`, and `market_context.summary`, including the existing `research` / `knowledge` note-origin rule.
- Added supported-seed gating so promotion is blocked unless `hook_id` is non-empty, `seed_type` is one of `query|topic|tickers`, and the corresponding seed payload is non-empty.
- Made the market-context rule explicit: `market_context.source` and `market_context.summary` are canonical proposal fields that may copy packet `traceability.analysis_context` only when present, otherwise promotion remains blocked.
- Limited the promoted proposal's downstream lineage claims to current candidate/backtest surfaces only: `candidate_id`, `idea_trace`, `analysis_context.path`, `analysis_context.title`, `artifacts.results_tsv`, and `artifacts.experiment_note`.

### Command Results

- `rg -n "canonical|candidate_hooks|build_candidate_strategy_hypothesis|hook_id|seed_type|idea_context|market_context|candidate_id|idea_trace" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md -S` → confirms Step 2 now documents the canonical promotion boundary, raw-hook restrictions, required mapping fields, supported seed gating, and bounded lineage surfaces.
- `rg -n "query|topic|tickers|research|knowledge|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md -S` → confirms the backend doc records the supported seed types, no-guess source mapping, and current downstream artifact surfaces.

### Blockers / Deviations

- No new backend blockers remain after Step 2.

### Follow-ups

- Step 3 should define result-based keep/discard semantics for promoted factor candidates without widening or bypassing the Step 2 canonical promotion contract.
