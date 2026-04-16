> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Sprint 1 — Backend Plan

> Feature: `v2-minute-autoresearch`
> Role: `Backend`
> Derived from: `Issue Draft A — Autoresearch Core + Idea Intake`
> Last Updated: `2026-04-09`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `docs/research-karpathy-autoresearch.md`
3. `program.md`

## 1) Sprint Mission

- Define the core autoresearch loop that uses Obsidian ideas and self-search to generate candidate strategy refinements for minute-level strategy research.

## 2) Scope / Out of Scope

**Scope**
- loop semantics
- idea-ingestion surfaces
- candidate-generation contract

**Out of Scope**
- minute runtime internals
- stock-discussion lane specifics
- factor-mining details

## 3) Step-by-Step Plan

### Step 1 — Define idea intake
- [x] define how daily Obsidian notes enter the loop
- [x] define when the loop should search for new ideas itself
- [x] define the minimum structured context the loop consumes before proposing strategy changes

### Step 2 — Define candidate generation
- [x] define how retrieved ideas become strategy hypotheses
- [x] define how those hypotheses modify or extend the current strategy
- [x] define how the loop avoids treating ideas as success before validation

### Step 3 — Define keep / revert semantics
- [x] define the handoff from candidate generation to the backtester
- [x] define that backtester outcomes, not idea quality, determine keep / revert
- [x] define the outputs the loop must record after each iteration

## 4) Test Plan

- [x] verify the loop contract still centers `program.md` / autoresearch
- [x] verify idea sources include both Obsidian and self-search
- [x] verify keep / revert remains backtester-driven

## 5) Verification Commands

```bash
rg -n "autoresearch|Obsidian|idea|backtester|keep / revert|keep/revert" docs/feature/v2-minute-autoresearch/sprint1 -S
```

## 6) Implementation Update Space

### Completed Work

- Added `src/memory/idea_intake.py` with `collect_vault_idea_notes()` so the runtime can enumerate research and knowledge notes from the configured Obsidian vault.
- Added `src/memory/idea_search_policy.py` so self-search runs only after vault notes are checked and only when research notes are missing, stale, or due for the 10-experiment refresh cadence.
- Added `build_minimum_structured_context()` in `src/memory/idea_intake.py` so strategy changes require a stable note path/source/title plus a metadata seed from `query`, `topic`, or `tickers`.
- Added `src/memory/candidate_generation.py` with `build_candidate_strategy_hypothesis()` and `determine_strategy_change()` so structured idea + market + baseline context becomes a candidate hypothesis that either modifies one existing strategy component or adds one bounded extension.
- Added `src/memory/idea_keep_revert.py` with `build_backtest_handoff()`, `decide_keep_revert()`, and `build_iteration_record()` so candidate generation hands a traceable payload to validation, keep/revert depends only on backtester metrics, and each iteration records the required artifacts.
- Updated `program.md` to document the self-search trigger and the minimum structured-context bundle required before proposing strategy changes.
- Added `tests/unit/test_candidate_generation.py`, `tests/unit/test_idea_keep_revert.py`, `tests/unit/test_idea_intake.py`, `tests/unit/test_idea_search_policy.py`, `tests/unit/test_program_guidance.py`, `tests/unit/test_vault_config.py`, and `tests/unit/test_cli_setup_vault.py` to lock the candidate-generation, keep/revert, intake, search-trigger, guidance, and vault-path contracts.
- Verified that the merged Sprint 1 branch now defines the full Step 2/Step 3 contract for this slice: structured context gates proposal creation, candidate generation marks hypotheses `pending_backtest`, and keep/revert stays subordinate to validation outputs.

### Command Results

- `uv run pytest tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py tests/unit/test_idea_intake.py tests/unit/test_idea_search_policy.py tests/unit/test_program_guidance.py tests/unit/test_vault_config.py tests/unit/test_cli_setup_vault.py tests/unit/test_cli_research.py -q` → `25 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors
- `rg -n "candidate_generation|keep_revert|build_backtest_handoff|decide_keep_revert|build_iteration_record|pending_backtest|backtester_required|backtester_outcome_only" src tests program.md docs/feature/v2-minute-autoresearch -S` → verified that candidate-generation and keep/revert helpers are present in `src/memory/`, their focused tests exist in `tests/unit/`, and the Sprint 1 docs now reflect the backtester-driven contract.

### Blockers / Deviations

- No new Sprint 1 backend blockers remain inside the Step 2 / Step 3 contract slice.
- Full runtime orchestration that consumes these helpers is still future work and remains out of scope for Sprint 1.

### Follow-ups

- Carry the new self-search decision reasons and structured-context bundle forward into Sprint 2+ runtime orchestration instead of re-deriving them ad hoc.
- Wire the candidate-generation and keep/revert helpers into the later runtime loop instead of re-encoding their contracts ad hoc.
