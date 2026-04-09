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
- [ ] define how retrieved ideas become strategy hypotheses
- [ ] define how those hypotheses modify or extend the current strategy
- [ ] define how the loop avoids treating ideas as success before validation

### Step 3 — Define keep / revert semantics
- [ ] define the handoff from candidate generation to the backtester
- [ ] define that backtester outcomes, not idea quality, determine keep / revert
- [ ] define the outputs the loop must record after each iteration

## 4) Test Plan

- [ ] verify the loop contract still centers `program.md` / autoresearch
- [ ] verify idea sources include both Obsidian and self-search
- [ ] verify keep / revert remains backtester-driven

## 5) Verification Commands

```bash
rg -n "autoresearch|Obsidian|idea|backtester|keep / revert|keep/revert" docs/feature/v2-minute-autoresearch/sprint1 -S
```

## 6) Implementation Update Space

### Completed Work

- Added `src/memory/idea_intake.py` with `collect_vault_idea_notes()` so the runtime can enumerate research and knowledge notes from the configured Obsidian vault.
- Added `src/memory/idea_search_policy.py` so self-search runs only after vault notes are checked and only when research notes are missing, stale, or due for the 10-experiment refresh cadence.
- Added `build_minimum_structured_context()` in `src/memory/idea_intake.py` so strategy changes require a stable note path/source/title plus a metadata seed from `query`, `topic`, or `tickers`.
- Updated `program.md` to document the self-search trigger and the minimum structured-context bundle required before proposing strategy changes.
- Added `tests/unit/test_idea_intake.py`, `tests/unit/test_idea_search_policy.py`, `tests/unit/test_program_guidance.py`, `tests/unit/test_vault_config.py`, and `tests/unit/test_cli_setup_vault.py` to lock the intake, search-trigger, guidance, and vault-path contracts.

### Command Results

- `uv run pytest tests/unit/test_idea_intake.py tests/unit/test_idea_search_policy.py tests/unit/test_program_guidance.py tests/unit/test_vault_config.py tests/unit/test_cli_setup_vault.py -q` → `13 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors

### Blockers / Deviations

- Step 1 idea-intake contract is now defined, but candidate-generation, keep/revert, and recording semantics remain open.

### Follow-ups

- Carry the new self-search decision reasons and structured-context bundle forward into Sprint 2+ runtime orchestration instead of re-deriving them ad hoc.
