# Strategy Knowledge Loop Upgrade Plan

> Status: transition design package / first cutover slice implemented
> Source evidence: `run-20260424T085227108335Z` live-run audit and deep-interview design update
> Scope: strategy context, rejection memory, strategic stock/ETF universe selection, backtest auditability, raw-note/continuation linkage, and docs/runtime cutover governance

## Cutover authority notice

This artifact is a transition record. The first implementation cutover slice has
landed for the core runner/backtester/memory surfaces, so this file should no
longer be treated as the active runtime contract.

Current authority remains with the updated `program.md`,
`docs/architecture/strategy-research-workflow.md`,
`.omx/specs/strategy-knowledge-loop-artifact-contract.md`, and
`docs/program/index.md`.

## Current-state vs target-state authority

| Phase | Authority status | Normative artifacts | Non-normative artifacts | Trigger to move forward |
|---|---|---|---|---|
| Pre-cutover / current state | Current runtime/docs are authoritative | `program.md`; `docs/architecture/strategy-research-workflow.md`; `.omx/specs/strategy-knowledge-loop-artifact-contract.md`; `docs/program/index.md` | `docs/program/strategy-knowledge-loop-upgrade-plan.md`; `.omx/plans/prd-strategy-knowledge-loop-full-autonomous-iteration.md`; `.omx/plans/test-spec-strategy-knowledge-loop-full-autonomous-iteration.md` | None; this package remains planning/design only |
| Post-cutover / future state | Updated runtime/docs become authoritative | Updated current-state docs/specs after implementation and verification | Historical planning package retained only as planning record unless explicitly retired/archived | Supersession trigger: implementation lands, verification passes, current docs are updated or retired, and collateral disposition is recorded |

First cutover slice now implemented:
- live runner summaries carry `universe_selection_summary` and
  `proofable_idea_sources`
- the backtester writes `universe_selection.json` with raw per-window
  strategy-selected tickers and any runtime cap
- live iterations materialize raw Obsidian experiment notes and refresh
  continuation memory when the notes directory maps to the configured vault
- run-level `rejection_map.json` preserves reverted/failed candidate families
  as anti-repeat guidance
- dry-run remains preview-only with `experiment_note_draft.md`

## Collateral Disposition Matrix

| Artifact | Current role | Pre-cutover status | Post-cutover disposition | Timing |
|---|---|---|---|---|
| `docs/program/strategy-knowledge-loop-upgrade-plan.md` | Upgrade umbrella / transition design package | Keep, labeled planning-only | Update into cutover record, archive, or supersede after disposition is recorded | After cutover |
| `.omx/plans/prd-strategy-knowledge-loop-full-autonomous-iteration.md` | Future-state PRD | Keep, labeled planning-only | Superseded by updated normative docs/specs; retain as planning history | At cutover completion |
| `.omx/plans/test-spec-strategy-knowledge-loop-full-autonomous-iteration.md` | Future-state test plan | Keep, labeled planning-only | Superseded by implemented verification evidence and updated normative docs/specs | At cutover completion |
| `.omx/specs/strategy-knowledge-loop-artifact-contract.md` | Current normative artifact contract | Keep as authority | Update or supersede with implemented contract text | During cutover |
| `docs/architecture/strategy-research-workflow.md` | Current normative workflow doc | Keep as authority | Update to reflect implemented future state, or explicitly retire if replaced | During cutover |
| `docs/program/index.md` | Current program hub / authority locator | Keep as authority | Update to distinguish current authority from landed future-state docs | During cutover |
| `.omx/plans/prd-strategy-knowledge-loop-note-template-iteration-artifacts.md` | Prior narrower planning collateral | Keep as historical/non-normative planning input | Merge-forward needed content, then retire/supersede explicitly by name | Before or during cutover |
| `.omx/plans/test-spec-strategy-knowledge-loop-note-template-iteration-artifacts.md` | Prior narrower planning collateral | Keep as historical/non-normative planning input | Merge-forward needed content, then retire/supersede explicitly by name | Before or during cutover |

## Why this upgrade exists

The 2026-04-24 live strategy search completed normally but did not produce a keeper.
The run completed 15 evaluated iterations and stopped at `max_no_improve_reached`.
All 15 iterations reverted with `score_not_above_baseline`.

The best candidate was iteration 11:

| Metric | Value |
|---|---:|
| Score | `-17.0154` |
| Current baseline score | `-15.1679` |
| Trades | `23,910` |
| Profit factor | `0.8229` |
| Drawdown | `-0.6146` |

This showed some improvement versus the worst candidates, but it still failed to beat the current kept baseline, `Experiment - Minimum Hold Duration v1`.

## Verified evidence from the failed 15-round run

| Evidence question | Verified finding |
|---|---|
| Run status | Completed normally |
| Stop reason | `max_no_improve_reached` |
| Iterations | 15 |
| Keeps | 0 |
| Reverts | 15 |
| Common revert reason | `score_not_above_baseline` |
| Main strategy family | Daily/intraday momentum, z-score thresholding, trend filtering, turnover reduction, long/flat gating |
| Obsidian sources actually used | `experiment-index.md`, `branch-summary-turnover-reduction.md`, `branch-summary-runtime-repair.md` |
| Broader strategy knowledge used | Not materially present in iteration context artifacts |

## Backtest form used by those 15 rounds

| Item | Verified value |
|---|---|
| Evaluator mode | Default evaluator, not scenario evaluator |
| Command | `uv run python cli.py backtest --strategy src/strategies/active_strategy.py` |
| Explicit date bounds | None |
| Explicit universe-size cap | None |
| Backtest mode | V2 minute-mode walk-forward validation |
| Number of walk-forward windows | 5 |
| Daily data | `data/daily_cache.duckdb` |
| Minute data | local `massive-minute-aggs` parquet dataset through `minute-aggs` CLI |
| Effective audited daily range | `2021-03-30` to `2026-03-30` |

Walk-forward windows verified from the daily cache:

| Window | Training start | Training end | Test start | Test end |
|---:|---|---|---|---|
| 1 | 2021-03-30 | 2022-01-26 | 2022-01-27 | 2022-11-25 |
| 2 | 2021-03-30 | 2022-11-25 | 2022-11-28 | 2023-09-27 |
| 3 | 2021-03-30 | 2023-09-27 | 2023-09-28 | 2024-07-29 |
| 4 | 2021-03-30 | 2024-07-29 | 2024-07-30 | 2025-05-29 |
| 5 | 2021-03-30 | 2025-05-29 | 2025-05-30 | 2026-03-30 |

## Key diagnosis

| Diagnosis | Consequence |
|---|---|
| The iteration context was too narrow | The model repeatedly searched near the same turnover/momentum idea |
| Reverted candidate memory was not first-class enough | Similar failed families could be retried without a strong anti-repeat guard |
| Raw universe-selection evidence was missing | We could see `PER_SYMBOL`, but not raw per-window `selected_tickers` from `select_universe()` |
| ETF presence was misinterpretable | The issue is not ETF inclusion; the issue is whether stock/ETF selection is intentional and auditable |
| Epoch evidence was not linked end-to-end | The run could not prove how each stock/ETF choice, research idea, and backtest decision related to one proofable hypothesis |

## Direction decision

ETF inclusion is allowed.

The upgrade must **not** add a stock-only default filter simply because ETFs appeared in evaluated universes.
Instead, the loop must prove that stocks and/or ETFs were selected intentionally as part of the candidate strategy thesis.

The future-state loop must also prove that every epoch has a traceable proof chain:

```text
proofable idea / evidence source
  -> strategic stock/ETF selection
  -> candidate strategy research/change
  -> backtest and universe audit
  -> keep/revert/failed/blocked decision
  -> raw note + continuation memory when candidate evidence exists
  -> next-epoch anti-repeat guidance
```

Pre-evidence operational blocks, such as persistent model rate limits before an
iteration agent returns a candidate, remain runtime audit records only; they do
not become canonical Obsidian raw experiment notes.

## Target architecture and responsibility boundaries

| Surface | Future-state responsibility | Explicit non-responsibility |
|---|---|---|
| Autoresearch supervisor / runner | Assemble bounded continuation context, launch each epoch, collect artifacts, persist iteration records, run keep/revert governance | It does not invent a new data source or silently override current docs before cutover |
| Per-iteration research/change agent | Propose a proofable hypothesis, explain stock/ETF selection thesis, modify candidate strategy, return `universe_selection_summary` | It does not treat raw `PER_SYMBOL` as screener evidence |
| Backtester / minute validation layer | Run walk-forward validation, capture raw `select_universe()` output per window before minute-data validation, record cap effects and evaluation output | It does not decide that ETFs are invalid by default |
| Experiment memory / Obsidian bridge | Preserve raw Obsidian experiment notes as canonical, refresh continuation manifest and derived summaries, link runtime artifacts back to raw notes | It does not replace raw notes with iteration artifacts |
| Evaluator / keep-revert governance | Compare candidate metrics with baseline, classify decision, record failure reasons and anti-repeat guidance | It does not auto-promote one improved run into fully validated truth |

## Future-state artifact contracts

### Strategy knowledge pack

Each live continuation epoch should receive a bounded, source-attributed strategy-knowledge pack.

| Field | Requirement |
|---|---|
| `path` | Source note or manifest path |
| `category` | `continuation_baseline`, `raw_experiment`, `branch_summary`, `research_note`, `knowledge_note`, or `rejection_lesson` |
| `excerpt` | Bounded excerpt relevant to the next hypothesis |
| `inclusion_reason` | Why this source is relevant to the epoch |
| `recency_or_priority` | Deterministic ordering signal |
| `canonicality` | `raw`, `canonical_manifest`, `derived`, or `runtime_audit` |

Generic intake/search must remain conservative; this broader pack is only for explicit continuation-mode strategy iteration.

### Rejection map

Each reverted candidate should create or update a machine-readable rejection map.

| Field | Purpose |
|---|---|
| `run_id` / `iteration_number` | Locate the failed round |
| `hypothesis` / `strategy_family` | Identify repeated idea families |
| `proofable_idea_sources` | Capture the evidence trail behind the attempted idea |
| `universe_selection_rule_attempted` | Capture screener behavior |
| `signal_generation_rule_attempted` | Capture trade logic |
| `score` and `baseline_score` | Explain keep/revert result |
| `trades` / `turnover_proxy` | Capture churn cost |
| `profit_factor` | Capture trade expectancy |
| `drawdown` | Capture risk failure |
| `decision` and `reasons` | Preserve evaluator judgment |
| `anti_repeat_guidance` | Tell the next epoch what not to retry without a materially different hypothesis |

The next iteration prompt/context should use this map to avoid another near-duplicate momentum/trend-filter candidate unless it introduces a materially different hypothesis.

### Universe-selection artifact

`PER_SYMBOL` is not enough to prove screener behavior. It shows evaluated symbols after minute-data validation and signal evaluation, not the raw strategy-selected universe.

Each live round should persist `universe_selection.json` or an equivalent linked artifact with at least:

| Field | Requirement |
|---|---|
| `instrument_scope` | Stocks, ETFs, inverse/leveraged ETFs, bond/cash ETFs, or other explicitly allowed classes |
| `etfs_allowed` | `true` when strategy thesis allows ETFs |
| `selection_thesis` | Plain-language reason why these stocks/ETFs fit the strategy |
| `proofable_idea_sources` | Evidence sources that motivated the selector |
| `selection_rules` | Filters/ranking inputs used by `select_universe(daily_data)` |
| `windows[].selected_tickers_raw` | Raw per-window `select_universe()` output before minute-data validation |
| `windows[].selected_tickers_after_cap` | Tickers after `--universe-size` cap, if any |
| `windows[].selected_tickers_after_validation` | Tickers that survive minute-data validation and are evaluated |
| `windows[].test_start/test_end` | Window where the selected universe was evaluated |
| `reason_codes` or feature snapshots | Enough evidence to answer why a ticker/ETF was selected |
| `per_symbol_reference` | Link to `PER_SYMBOL` as evaluation output, not raw screener evidence |

### Iteration summary extension

The per-iteration wrapper output should include a universe-selection summary alongside the existing summary fields.

Required fields:

- `hypothesis`
- `proofable_idea_sources`
- `strategy_change_summary`
- `universe_selection_summary`
- `files_touched`

The agent must state how stock/ETF screening is part of the candidate strategy thesis.

### Raw-note and continuation-memory linkage

Canonical live-round notes should include:

- proofable idea / evidence source trail
- universe-selection thesis
- selected stock/ETF evidence summary
- link to `universe_selection.json`
- backtest data/window summary
- keep/revert/failed/blocked decision
- rejection-map update when the decision is `revert` or candidate-level `failed`
- anti-repeat guidance for the next experiment
- continuation manifest linkage

## Implementation sequence

| Slice | Scope | Depends on |
|---:|---|---|
| 1 | Contract and schema tests for strategy knowledge pack, rejection map, universe artifact, and iteration summary | This design package |
| 2 | Strategy-knowledge pack assembly in runner / memory helpers | Slice 1 |
| 3 | Rejection-map artifact and prompt/context integration | Slice 1 |
| 4 | Backtester hook to capture raw per-window `selected_tickers` before minute-data validation | Slice 1 |
| 5 | Universe-selection artifact writing and iteration-record linkage | Slices 3-4 |
| 6 | Wrapper prompt/output contract update for `universe_selection_summary` and proofable idea sources | Slices 2-5 |
| 7 | Raw note / continuation manifest integration | Slices 2-6 |
| 8 | Cutover documentation update for current-state authorities and collateral disposition | Implementation verification |
| 9 | Bounded live E2E autoresearch proof | Slices 1-8 |

## Docs-only acceptance criteria for this revision

These criteria apply to this docs/plans update itself, before code implementation:

| # | Acceptance criterion |
|---:|---|
| 1 | No current doc falsely describes the future-state loop as already active before cutover. |
| 2 | Every future-state artifact is explicitly labeled planning-only and non-normative pre-cutover. |
| 3 | `docs/program/index.md` distinguishes current authority from the future-state planning package. |
| 4 | Superseded artifacts are named explicitly, not implied. |
| 5 | The supersession trigger is stated consistently across the upgrade plan, PRD, and test spec. |
| 6 | Current authority is explicitly listed as `program.md`, `docs/architecture/strategy-research-workflow.md`, `.omx/specs/strategy-knowledge-loop-artifact-contract.md`, and `docs/program/index.md`. |
| 7 | PRD/test-spec brownfield anchors match current file locations. |

## Future implementation acceptance criteria

| # | Acceptance criterion |
|---:|---|
| 1 | Live context includes a bounded strategy-knowledge pack beyond the latest three experiment notes. |
| 2 | Each included strategy source records path, category, excerpt, and inclusion reason. |
| 3 | Every epoch/iteration references at least one proofable idea or evidence source. |
| 4 | Reverted and candidate-level failed candidates update rejection memory with score/baseline evidence when available, decision, reasons, and anti-repeat guidance. |
| 5 | Repeated failed strategy families generate anti-repeat guidance for the next round. |
| 6 | Live backtest artifacts persist raw per-window `selected_tickers` from `select_universe()` before minute-data validation. |
| 7 | Universe artifacts record cap effects and distinguish raw selected tickers, after-cap tickers, after-validation tickers, and `PER_SYMBOL` evaluation output. |
| 8 | ETF-containing universes remain valid when ETFs are intentionally selected by the strategy thesis. |
| 9 | The system does not add a stock-only default filter. |
| 10 | Iteration summaries include `universe_selection_summary` and `proofable_idea_sources`. |
| 11 | Canonical raw experiment notes include universe-selection evidence and rejection lessons. |
| 12 | A bounded real autoresearch run proves stock picker, strategy research, backtesting, artifacts, and result/learning behavior all work after implementation. |

## Non-goals

- Do not add a new external data source.
- Do not change external data-source schema without explicit user approval.
- Do not ban ETFs.
- Do not force stock-only screening by default.
- Do not replace raw Obsidian evidence with iteration artifacts.
- Do not let generic intake/search silently consume all experiment history.
- Do not treat `PER_SYMBOL` as raw screener evidence.
- Do not treat documentation parity as proof that the runtime has already changed.
- Do not treat a single improved run as validation proof.

## Verification plan

| Gate | Required proof |
|---|---|
| Docs package coherence | Authority table, non-normative labels, supersession trigger, and collateral matrix appear in the upgrade plan, PRD, and test spec. |
| Brownfield anchors | PRD/test-spec use `cli.py:374-383` and `scripts/autoresearch_runner.py:1228`, `1533`, `1570` for current references. |
| Strategy context | Context assembly tests include categorized broader sources and remain bounded. |
| Rejection memory | Reverted candidates produce rejection-map records and anti-repeat guidance. |
| Universe artifact | Raw per-window `selected_tickers` are persisted before minute-data validation. |
| ETF allowed | A synthetic stock+ETF strategy passes when the thesis allows ETFs. |
| PER_SYMBOL separation | Tests prove `PER_SYMBOL` is evaluation output, not raw screener evidence. |
| Raw note integration | Canonical notes include proofable idea trail, universe-selection thesis, and rejection lessons. |
| Live E2E | A bounded real autoresearch run emits stock picker, strategy research, backtest, keep/revert, note, continuation, and anti-repeat evidence. |

## Evidence references

| Evidence | Path |
|---|---|
| Deep-interview design spec | `.omx/specs/deep-interview-strategy-knowledge-loop-upgrade-plan-design-update.md` |
| Run state | `experiments/autoresearch_live_3h_omx_session_20260424T085226Z.json` |
| Live-run audit summary | Embedded in this upgrade plan from the 2026-04-24 audit pass |
| Machine iteration artifacts | `experiments/iterations/run-20260424T085227108335Z/iteration-*/{decision.json,iteration_record.json,omx_summary.json,backtest.stdout.log}` |
| PRD sync target | `.omx/plans/prd-strategy-knowledge-loop-full-autonomous-iteration.md` |
| Test-spec sync target | `.omx/plans/test-spec-strategy-knowledge-loop-full-autonomous-iteration.md` |
