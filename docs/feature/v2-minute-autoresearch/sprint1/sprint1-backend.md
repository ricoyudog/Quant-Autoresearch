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
- [ ] define when the loop should search for new ideas itself
- [ ] define the minimum structured context the loop consumes before proposing strategy changes

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
- Updated `program.md` to state that vault idea notes should be read before self-searching for new ideas.
- Added `tests/unit/test_idea_intake.py` and extended `tests/unit/test_program_guidance.py`.

### Command Results

- `uv run pytest tests/unit/test_idea_intake.py tests/unit/test_program_guidance.py -q` → `3 passed`
- `uv run pytest tests/unit/test_cli.py tests/unit/test_backtester_v2.py -q` → `66 passed`

### Blockers / Deviations

- leave blank until implemented

### Follow-ups

- leave blank until implemented
