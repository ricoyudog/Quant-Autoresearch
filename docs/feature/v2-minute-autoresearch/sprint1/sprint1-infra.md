> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

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
- [x] define fallback behavior when no suitable idea note exists

### Step 2 — Define search/runtime assumptions
- [x] define when self-search is allowed to supplement local ideas
- [x] define what credentials or external services are optional vs required
- [x] define how missing search credentials degrade gracefully

### Step 3 — Define recording expectations
- [x] define what outputs should be written back after a loop iteration
- [x] define how traceability to the input ideas is preserved

## 4) Test Plan

- [x] verify Obsidian remains the primary upstream idea source
- [x] verify search remains supplemental, not authoritative
- [x] verify degraded modes are explicit

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
- Verified that `src/memory/idea_keep_revert.py` now records a durable per-iteration artifact containing the idea trace, analysis context, strategy path, backtest metrics, `experiments/results.tsv`, and the experiment-note path.

### Command Results

- `uv run pytest tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py tests/unit/test_idea_intake.py tests/unit/test_idea_search_policy.py tests/unit/test_program_guidance.py tests/unit/test_vault_config.py tests/unit/test_cli_setup_vault.py tests/unit/test_cli_research.py -q` → `25 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors
- `rg -n "EXA_API_KEY|SERPAPI_KEY|research --depth shallow|degrade|degraded|idea_trace|analysis_context|results.tsv|experiment_note" program.md cli.py src tests docs/feature/v2-minute-autoresearch -S` → verified explicit missing-credential degradation in `cli.py`, persistent `results.tsv` guidance in `program.md`, and per-iteration traceability fields in `src/memory/idea_keep_revert.py`.

### Blockers / Deviations

- No new Sprint 1 infra blockers remain inside this idea-intake / search / traceability slice.
- Full runtime persistence and downstream consumers of the iteration record remain future work and stay out of scope for Sprint 1.

### Follow-ups

- Keep the infrastructure contract aligned with future runtime wiring so the same freshness window, refresh cadence, and metadata seed rules are enforced end-to-end.
- Preserve the current traceability fields (`idea_trace`, `analysis_context`, `results.tsv`, `experiment_note`) when later runtime slices write real iteration artifacts.
