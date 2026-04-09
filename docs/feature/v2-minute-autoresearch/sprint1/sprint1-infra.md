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
- Reviewed the merged Sprint 1 branch and confirmed that shallow research remains usable without web credentials while deep search degrades explicitly in `cli.py` when `EXA_API_KEY` / `SERPAPI_KEY` are absent.
- Reviewed the same branch for recording/traceability expectations and confirmed that Sprint 1 currently stops at `results.tsv` and experiment-note guidance; it does not yet define a durable artifact linking each candidate change back to the exact input idea note and validation verdict.

### Command Results

- `uv run pytest tests/unit/test_idea_intake.py tests/unit/test_idea_search_policy.py tests/unit/test_program_guidance.py tests/unit/test_vault_config.py tests/unit/test_cli_setup_vault.py -q` → `13 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors
- `rg -n "EXA_API_KEY|SERPAPI_KEY|research --depth shallow|degrade|degraded|traceability|results.tsv|validated run" program.md cli.py src tests docs/feature/v2-minute-autoresearch -S` → verified explicit degraded-search messaging and `results.tsv` / validated-run guidance, but found no Sprint 1 traceability artifact or per-iteration record contract for candidate-to-backtester decisions.

### Blockers / Deviations

- Missing-note fallback beyond triggering supplemental self-search remains open.
- External-credential requirements are only partially defined: deep-search degradation is explicit, but the sprint still does not separate required vs optional services beyond the current CLI fallback.
- Recording expectations remain open because the branch does not yet define how a kept/reverted candidate should preserve traceability back to the source idea note and validation result.

### Follow-ups

- Keep the infrastructure contract aligned with future runtime wiring so the same freshness window, refresh cadence, and metadata seed rules are enforced end-to-end.
- Add an explicit candidate-traceability artifact in a later slice so each iteration can point back to the originating idea note, analyze context, and backtester verdict.
- Define the optional-vs-required service contract for deep research before Sprint 1 infra is considered fully closed.
