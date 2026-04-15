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

Required content:
- baseline reference
- analysis context
- idea trace / hypothesis
- strategy changes
- bounded result
- unrestricted result
- decision (`keep` / `revert` / `follow_up`)
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

Continuation mode must still preserve the distinction between:
- promising improvement
- candidate baseline
- validated strategy

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

