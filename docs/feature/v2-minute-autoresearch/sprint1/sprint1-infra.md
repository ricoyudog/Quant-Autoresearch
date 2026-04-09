# Sprint 1 — Infra Plan

> Feature: `v2-minute-autoresearch`
> Role: `Infra`
> Derived from: `Issue Draft A — Autoresearch Core + Idea Intake`
> Last Updated: `2026-04-09`

## 0) Governing Specs

1. `.omx/specs/deep-interview-spec-vs-impl.md`
2. `program.md`
3. `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-infra.md`

## 1) Sprint Mission

- Define the environment and source-of-truth assumptions that allow the autoresearch loop to read ideas from Obsidian and search for new ideas safely.

## 2) Scope / Out of Scope

**Scope**
- Obsidian idea-source assumptions
- search/runtime assumptions
- persistent note expectations

**Out of Scope**
- minute runtime execution details
- factor mining runtime specifics

## 3) Step-by-Step Plan

### Step 1 — Define idea-source assumptions
- [x] define where daily collected ideas live
- [x] define what minimum metadata or structure the loop can rely on
- [ ] define fallback behavior when no suitable idea note exists

### Step 2 — Define search/runtime assumptions
- [x] define when self-search is allowed to supplement local ideas
- [ ] define what credentials or external services are optional vs required
- [ ] define how missing search credentials degrade gracefully

### Step 3 — Define recording expectations
- [ ] define what outputs should be written back after a loop iteration
- [ ] define how traceability to the input ideas is preserved

## 4) Test Plan

- [ ] verify Obsidian remains the primary upstream idea source
- [ ] verify search remains supplemental, not authoritative
- [ ] verify degraded modes are explicit

## 5) Verification Commands

```bash
rg -n "Obsidian|search|credentials|fallback|idea" docs/feature/v2-minute-autoresearch/sprint1 -S
```

## 6) Implementation Update Space

### Completed Work

- Verified that the vault idea-source root is `quant-autoresearch/` under `OBSIDIAN_VAULT_PATH` (or the default `~/Documents/Obsidian Vault`) with daily/autoresearch inputs read from `quant-autoresearch/research/` and `quant-autoresearch/knowledge/`.
- Verified that `setup_vault` creates the expected directories idempotently before idea-intake code reads from them.
- Verified that the minimum metadata seed for an idea note is `query`, `topic`, or `tickers`, and that strategy changes stay blocked until that structured context exists.
- Verified that self-search is supplemental only: it runs after vault-note intake and only when recent research notes are missing, stale beyond the 7-day freshness window, or every 10 completed experiments as a refresh cadence.

### Command Results

- `uv run pytest tests/unit/test_idea_intake.py tests/unit/test_idea_search_policy.py tests/unit/test_program_guidance.py tests/unit/test_vault_config.py tests/unit/test_cli_setup_vault.py -q` → `13 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors

### Blockers / Deviations

- Missing-note fallback beyond triggering supplemental self-search, external-credential requirements, and degraded-search handling remain open.

### Follow-ups

- Keep the infrastructure contract aligned with future runtime wiring so the same freshness window, refresh cadence, and metadata seed rules are enforced end-to-end.
