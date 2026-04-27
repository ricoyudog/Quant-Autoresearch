# Strategy Knowledge Loop Artifact Contract

## Purpose

This contract defines the documentation and artifact boundaries for the
strategy knowledge loop used by Quant-Autoresearch.

The goal is **complete memory**: future research runs must retain both wins and
losses, preserve fee / turnover lessons, and keep raw evidence available even
when summaries are auto-generated.

## Source-of-Truth Hierarchy

1. **Raw experiment note** — append-only Obsidian note under
   `quant-autoresearch/experiments/`
2. **Canonical automation manifest** — repo-local machine contract at
   `experiments/continuation/current_research_base.json`
3. **Derived summaries** — rebuildable views such as `experiment-index.md`,
   kickoff updates, and branch summaries

Outside that hierarchy, the runtime may also emit an **ephemeral audit layer**
under `experiments/iterations/<run-id>/iteration-####/`. Those iteration
artifacts are rebuildable runtime evidence only — not raw notes and not the
canonical continuation manifest.

Automation may read or regenerate items in layers 2-3, but it must not rewrite
layer 1 as part of summarization.

## Required Behavioral Rules

- Keep failed experiments, rejected hypotheses, and weak branches as first-class
  knowledge.
- Capture trading-fee / turnover lessons explicitly, not only score deltas.
- Treat one improved backtest as **follow-up evidence**, not proof.
- Do not automatically stop exploring alternate directions because one branch
  improved.
- Do not let summarization collapse uncertainty into a “validated” claim.

## Artifact Boundaries

### 1) Raw experiment note

Raw notes are human-readable evidence. They are append-only and may be
summarized, but not deleted or replaced by summaries.

Only rounds that complete the proof chain at least through worker-produced
strategy/universe evidence should become raw notes. Pre-evidence operational
blocks (for example persistent model rate limits before a candidate is
produced) stay in runtime audit artifacts and must not be promoted into
canonical experiment memory.

Required content:
- baseline reference
- analysis context
- idea trace / hypothesis
- proofable idea sources
- strategy changes
- stock/ETF universe-selection thesis
- universe-selection artifact path when produced
- bounded result
- unrestricted result
- decision (`keep` / `revert` / `failed` / `blocked` / `follow_up_required`)
- decision reasons
- turnover / fee lesson
- next experiment
- validation status
- raw note path

### 2) Canonical automation manifest

The manifest is the stable machine-readable source for continuation.

Canonical path:

```text
experiments/continuation/current_research_base.json
```

Required fields:
- `branch_id`
- `parent_experiment`
- `raw_note_path`
- `baseline_reference`
- `analysis_context`
- `bounded_result`
- `unrestricted_result`
- `validation_status`
- `decision`
- `decision_reasons`
- `turnover_fee_lesson`
- `next_experiment`
- `proofable_idea_sources`
- `universe_selection_summary`
- `universe_selection_artifact`

Recommended `validation_status` values:
- `candidate`
- `follow_up_required`
- `validated`

Only the documented validation rules may promote a result to `validated`.

### 3) Derived summaries

Derived summaries are rebuildable views and may be refreshed automatically.
They must always link back to the raw note and canonical manifest.

Examples:
- `experiment-index.md`
- daily kickoff summaries
- compressed branch summaries for older experiment chains

## Ephemeral Audit Layer

Examples:
- `context.json`
- `context.md`
- `claude_prompt.md`
- `decision.json`
- `iteration_record.json`
- `universe_selection.json`
- run-level `rejection_map.json`
- `experiment_note_draft.md`

Rules:
- These files may explain one round end-to-end.
- They must remain excluded from generic intake.
- `universe_selection.json` records raw per-window
  `select_universe(daily_data)` outputs before minute-data validation and any
  runtime `--universe-size` cap.
- `rejection_map.json` records reverted/failed candidate families so later
  epochs can avoid materially equivalent repeats.
- `experiment_note_draft.md` is a dry-run/operator-preview draft, not a raw
  experiment note.
- A **live** runner iteration may materialize a raw vault note directly after
  evaluator/backtester decision, then refresh the continuation manifest.
- A **dry-run** iteration must remain preview-only and must not materialize a
  raw vault note.

## Continuation Modes

### Generic intake

Default research intake must stay anchored to:
- `quant-autoresearch/research/`
- `quant-autoresearch/knowledge/`

Generic intake must **not** silently absorb experiment history or recent branch
state.

### Explicit continuation mode

Experiment history may be read only when the operator or runner enters an
explicit continuation surface.

Continuation mode may consume:
- raw experiment notes
- the canonical manifest
- derived summaries
- bounded strategy knowledge packs assembled from current baseline, raw
  experiment evidence, relevant `research/` and `knowledge/` notes, and
  rejection memory

Continuation mode must still preserve the distinction between:
- promising improvement
- candidate baseline
- validated strategy

## Universe Selection Evidence

Stock/ETF selection is a first-class strategy output.

Rules:
- `select_universe(daily_data)` owns the trade universe.
- ETFs are allowed when the strategy thesis intentionally selects them.
- The evaluator/backtester must not replace an empty or invalid strategy
  universe with a synthetic fallback.
- `PER_SYMBOL` output remains evaluation evidence, but it is not sufficient as
  screener evidence.
- Live iterations must link a plain-language `universe_selection_summary` to
  machine-readable raw per-window `selected_tickers` evidence.

The `universe_selection.json` artifact should include:
- `instrument_scope: stocks_or_etfs`
- `selection_owner`
- `selection_thesis`
- `universe_size_cap`
- per-window `raw_selected_tickers`
- per-window post-cap `selected_tickers`
- whether a cap was applied

## Rejection Memory

Reverted and failed candidates are retained as anti-repeat guidance.

The run-level `rejection_map.json` should include:
- hypothesis
- strategy-change summary
- universe-selection summary
- decision
- decision reasons
- universe-selection artifact path when available

Subsequent iteration contexts should surface the rejection map so the next
agent changes the proofable idea, universe rule, or signal mechanism before
retrying.

## Fee / Turnover Lesson Capture

Every experiment note and continuation manifest should record:
- observed turnover
- fee impact or slippage implication
- why the cost matters for the strategy
- whether the improvement survives costs

If a branch improves before costs, the contract treats it as incomplete until
fee/turnover impact is explicit.

## Summary Refresh Rules

- Summaries may be auto-generated.
- Raw note content must remain unchanged.
- Summary refresh must be idempotent.
- If a summary conflicts with a raw note, the raw note wins.
- Summaries must preserve raw-note lineage and evaluation surfaces.

## Minimal Experiment Note Frontmatter

```yaml
---
note_type: experiment
experiment_id: "003"
branch_id: "003-turnover-reduction"
parent_experiment: "002-claude-autoresearch-loop"
raw_note_path: "/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/2026-04-14-turnover-reduction-confirmation-bars.md"
validation_status: candidate
decision: keep
baseline_reference: "previous kept branch or active_strategy commit"
analysis_context: "latest market context note / analyze report"
turnover_fee_lesson: "Higher turnover erodes the backtest gain after fees"
---
```

## Handoff Rule

Downstream docs, runners, and future autoresearch lanes must treat this contract
as the documentation boundary for knowledge-loop behavior.
