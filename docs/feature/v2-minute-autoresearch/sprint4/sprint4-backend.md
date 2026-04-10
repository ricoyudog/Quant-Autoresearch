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
- [x] define that factor quality is only meaningful through improved validated results
- [x] define how poor-result factors are discarded

Once a promoted factor hook becomes a candidate, it stays on the existing validation contract: `validation_status`
remains `pending_backtest` and `validation_rule` remains `backtester_required` until the normal validation flow
finishes. Factor novelty, rationale quality, or how interesting the mined hook looks cannot upgrade a candidate to
`keep`, cannot bypass backtesting, and cannot create a second scoring lane.

Keep / revert authority remains the existing keep/revert rule only: `keep_rule=backtester_outcome_only`. A
factor-derived candidate is judged by the same validated backtester outcomes used for every other candidate, so the
decision boundary is improved measured results rather than upstream factor quality.

Poor-result factor-derived candidates therefore follow the same existing outcome path as any other weak candidate: once
validated results fail the keep thresholds, the candidate is discarded / reverted through the normal keep/revert rule.
Step 3 does not add a new persistence surface, does not add a factor-quality rubric, and does not introduce a separate
result-judgment lane beyond the current candidate -> backtest -> keep/revert contract.

## 4) Test Plan

- [x] verify factor mining is optional
- [x] verify factor ideas stay under autoresearch
- [x] verify promoted factor-derived candidates stay `pending_backtest` / `backtester_required` until validation completes
- [x] verify backtester remains the outcome judge

## 5) Verification Commands

```bash
rg -n "Step 2|candidate integration|canonical proposal|promotion blocked|raw hooks|hook_id|contrarian_observations|traceability" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md docs/feature/v2-minute-autoresearch/sprint4/sprint4-infra.md docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S
rg -n "pending_backtest|backtester_required|backtester_outcome_only|discard|revert|scoring lane|persistence surface" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md src/memory tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -S
uv run pytest tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q
```

## 6) Implementation Update Space

### Completed Work

- Defined the Step 2 promotion boundary so factor mining stays research-input-only until the minute autoresearch loop materializes one canonical proposal record from a selected hook.
- Locked the raw-hook boundary explicitly: raw `candidate_hooks` cannot bypass canonicalization, cannot call `build_candidate_strategy_hypothesis()` directly, and cannot create a second candidate lane.
- Added a no-guess mapping table for `idea_context.path`, `idea_context.source`, `idea_context.title`, `market_context.source`, and `market_context.summary`, including the existing `research` / `knowledge` note-origin rule.
- Added supported-seed gating so promotion is blocked unless `hook_id` is non-empty, `seed_type` is one of `query|topic|tickers`, and the corresponding seed payload is non-empty.
- Made the market-context rule explicit: `market_context.source` and `market_context.summary` are canonical proposal fields that may copy packet `traceability.analysis_context` only when present, otherwise promotion remains blocked.
- Limited the promoted proposal's downstream lineage claims to current candidate/backtest surfaces only: `candidate_id`, `idea_trace`, `analysis_context.path`, `analysis_context.title`, `artifacts.results_tsv`, and `artifacts.experiment_note`.
- Closed Step 3 by documenting that promoted factor-derived candidates remain `pending_backtest` / `backtester_required` until validation completes, so factor novelty or rationale quality never bypasses the existing validation gate.
- Tied factor-result judgment explicitly to the current keep/revert authority only: `keep_rule=backtester_outcome_only` remains the sole decision rule for factor-derived candidates as well.
- Recorded that poor-result factor-derived candidates are discarded / reverted through the same existing keep/revert path used for all other candidates, without adding a new persistence surface or a separate factor-scoring lane.

### Command Results

- `rg -n "canonical|candidate_hooks|build_candidate_strategy_hypothesis|hook_id|seed_type|idea_context|market_context|candidate_id|idea_trace" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md -S` → confirms Step 2 now documents the canonical promotion boundary, raw-hook restrictions, required mapping fields, supported seed gating, and bounded lineage surfaces.
- `rg -n "query|topic|tickers|research|knowledge|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md -S` → confirms the backend doc records the supported seed types, no-guess source mapping, and current downstream artifact surfaces.
- `rg -n "pending_backtest|backtester_required|backtester_outcome_only|discard|revert|scoring lane|persistence surface" docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md src/memory tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -S` → confirms the Step 3 wording matches the existing candidate-generation and keep/revert contract, including `pending_backtest`, `backtester_required`, and `backtester_outcome_only`.
- `uv run pytest tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q` → verifies the focused contract still passes for pending-backtest candidate generation and backtester-only keep/revert decisions.

### Blockers / Deviations

- No blocker for backend Step 3 closeout; the wording stays within the existing candidate -> backtest -> keep/revert contract and does not introduce new persistence or scoring behavior.

### Follow-ups

- Keep any later runtime or infra follow-up constrained to execution wiring or artifact reporting; do not let future work reintroduce factor-quality judgment as a parallel authority to backtester outcomes.
