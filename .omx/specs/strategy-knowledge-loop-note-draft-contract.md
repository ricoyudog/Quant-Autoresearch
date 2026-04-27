# Strategy Knowledge Loop Note Draft Contract

## Purpose

This contract defines the **derived note draft** surface used by runner iteration artifacts.

The note draft exists as a **dry-run/operator preview** convenience. Live
iterations materialize canonical raw Obsidian experiment notes directly after
evaluator/backtester decision; dry-runs remain non-canonical.

## Hierarchy Position

The note draft does **not** change the primary hierarchy:
1. raw experiment note
2. canonical continuation manifest
3. derived summaries

The note draft belongs to the **ephemeral audit layer** under:

```text
experiments/iterations/<run-id>/iteration-####/experiment_note_draft.md
```

It is:
- rebuildable
- disposable
- excluded from generic intake
- excluded from summary refresh

It is not:
- raw evidence
- the canonical continuation manifest
- a normal live-path artifact

## Required Fields

Frontmatter should include at minimum:
- `note_type: experiment_draft`
- `draft_type: derived_iteration_artifact`
- `run_id`
- `iteration_number`
- `validation_status`
- `artifact_status`
- `execution_mode`
- `derived_from_iteration_record`
- `continuation_manifest`
- `raw_note_materialization: pending_explicit_finalize`

## Required Sections
- Objective / hypothesis
- Proposed change
- Baseline context
- Evaluation evidence
- Bounded result
- Unrestricted result
- Decision state
- Fee / turnover lesson
- Finalization status

## Honesty Rules
- A draft must explicitly say when the round is dry-run or simulated.
- Placeholders must not look like real evaluator conclusions.
- The draft must not claim `validated` unless an explicit promotion rule sets it.
- The draft must remind the operator that dry-run previews are non-canonical.
- Live-path raw-note materialization is governed by
  `.omx/specs/strategy-knowledge-loop-artifact-contract.md`, not this preview
  draft contract.
