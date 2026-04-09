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
- Reviewed the merged Sprint 1 branch and confirmed that this slice currently defines the gate before a hypothesis can exist, not the full hypothesis-to-strategy mutation flow: the branch requires structured idea context, a deterministic `analyze` artifact, and the current baseline before any proposal is allowed.
- Reviewed the same branch for the first keep/revert rule slice and confirmed that Sprint 1 still does not encode a backend handoff helper or a backtester-authority rule in `program.md`/`src`; keep/revert remains a higher-level contract that is not yet implemented in this sprint slice.

### Command Results

- `uv run pytest tests/unit/test_idea_intake.py tests/unit/test_idea_search_policy.py tests/unit/test_program_guidance.py tests/unit/test_vault_config.py tests/unit/test_cli_setup_vault.py -q` → `13 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors
- `rg -n "minimum structured context|do not propose strategy changes|validated run|keep / revert|keep/revert|backtester outcomes|idea quality|hypothesis" program.md src/memory tests/unit docs/feature/v2-minute-autoresearch -S` → verified that the current slice defines a structured-context gate and post-validation note writing, while backtester-driven keep/revert language still only appears in higher-level feature docs, not in Sprint 1 runtime guidance or helpers.

### Blockers / Deviations

- Step 2 is only partially advanced by the structured-context gate; the branch still does not define how retrieved ideas become concrete strategy hypotheses or how they modify `src/strategies/active_strategy.py`.
- The first keep/revert rule slice is still open in Sprint 1 backend terms: there is no explicit candidate package handoff to the backtester and no local rule that says idea quality alone cannot justify keeping a change.
- Recording semantics remain open beyond the existing `results.tsv` / experiment-note guidance.

### Follow-ups

- Carry the new self-search decision reasons and structured-context bundle forward into Sprint 2+ runtime orchestration instead of re-deriving them ad hoc.
- Add an explicit hypothesis-to-strategy-change contract before closing Sprint 1 Step 2.
- Add the backtester handoff and keep/revert authority rule to the next backend slice before treating Sprint 1 keep/revert semantics as complete.
