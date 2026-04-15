# Strategy Knowledge Loop Note Draft Contract

## Purpose

This contract defines the **derived note draft** surface used by runner iteration artifacts.

The note draft exists to make a round human-auditable before any explicit finalize step
creates or updates a raw Obsidian experiment note.

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
- excluded from summary refresh unless an explicit continuation/finalize path opts in

It is not:
- raw evidence
- the canonical continuation manifest
- a substitute for explicit raw-note finalization

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
- The draft must remind the operator that final raw-note materialization is a separate explicit step.
