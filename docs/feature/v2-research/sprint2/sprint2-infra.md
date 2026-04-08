# Sprint 2 -- Infra Plan

> Feature: `v2-research`
> Role: Infra
> Derived from: `#13` -- API fallback + analysis runtime validation
> Last Updated: 2026-04-08

## 0) Governing Specs

1. `docs/research-capabilities-v2.md` -- Sections 2-5 and 7 for research CLI, analysis flow, and
   knowledge-note expectations
2. `docs/upgrade-plan-v2.md` -- V2 CLI decisions and surrounding runtime assumptions
3. `docs/feature/v2-research/v2-research-development-plan.md` -- Sprint 2 infra tasks and
   verification expectations
4. `docs/feature/v2-research/v2-research-infra.md` -- cross-sprint runtime contract
5. `docs/feature/v2-research/sprint2/sprint2-backend.md` -- backend deliverables that depend on
   runtime validation

## 1) Sprint Mission

Lock the runtime assumptions behind the Sprint 2 research surface. This lane defines the safe
fallback behavior for missing web-search credentials, validates the actual local data prerequisite
for `analyze`, and captures the smoke evidence that proves the new commands work outside the test
suite.

## 2) Scope / Out of Scope

**Scope**
- Define shallow vs deep behavior for `research` when `EXA_API_KEY` or `SERPAPI_KEY` is absent
- Validate the local market-data dependency used by `analyze`
- Run and record Sprint 2 smoke commands
- Feed runtime findings back into the issue or review evidence

**Out of Scope**
- Implementing backend logic inside the CLI or helper modules
- Long-term infra automation beyond what is needed to make Sprint 2 reviewable
- UI / Playwright coverage, which is not relevant for this feature scope

## 3) Step-by-Step Plan

### Step 1 -- Lock the research API fallback behavior
- [x] Check the presence or absence of `EXA_API_KEY` and `SERPAPI_KEY` on the implementation
      machine.
- [x] Define and verify what `research --depth shallow` does when deep-web credentials are missing.
- [x] Define and verify what `research --depth deep` does when credentials are missing, partial, or
      available.
- [x] Record the operator guidance needed to enable deep mode intentionally.

### Step 2 -- Validate the `analyze` runtime data prerequisite
- [x] Identify the exact local data surface used by `analyze`.
- [x] Validate that the required data path, cache, or connector input is present on the current
      machine.
- [x] Record the clear error behavior that should be surfaced if the data prerequisite is missing.
- [x] Update any stale assumption in docs or evidence notes before closeout if the actual runtime
      surface differs from the earlier draft.

### Step 3 -- Capture Sprint 2 smoke evidence
- [x] Run `uv run python cli.py research ...` in shallow mode and capture the output.
- [x] Run deep mode only if the required credentials are intentionally available.
- [x] Run `uv run python cli.py analyze ...` and capture the output or the clear missing-data error
      behavior.
- [x] Confirm any vault outputs land in the expected location and are easy to reference later.

### Step 4 -- Prepare closeout-ready runtime notes
- [x] Record smoke results in the update space with enough detail for review.
- [x] Note any unresolved infra follow-ups that should not be hidden inside backend tasks.
- [x] Link the final smoke evidence back to the umbrella issue or PR summary.

## 4) Test Plan

- [x] Shallow `research` behavior works without deep-web credentials.
- [x] Deep `research` behavior has an explicit, documented outcome when credentials are missing or
      available.
- [x] The exact `analyze` data prerequisite is validated and recorded.
- [x] Sprint 2 smoke commands produce reviewable evidence for stdout or vault output.
- [x] Any runtime blockers are recorded explicitly instead of being treated as implicit assumptions.

## 5) Verification Commands

```bash
python -c "
import os
print('EXA_API_KEY' in os.environ)
print('SERPAPI_KEY' in os.environ)
"

uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output stdout

uv run python cli.py analyze SPY --start 2025-01-01 --output stdout
```

## 6) Implementation Update Space

### Completed Work

- Confirmed the current machine is missing both `EXA_API_KEY` and `SERPAPI_KEY`.
- Verified `research --depth shallow` still returns a report successfully without deep-web
  credentials.
- Verified `research --depth deep` now prints an explicit fallback message and returns an ArXiv-only
  report when deep-web credentials are unavailable.
- Validated that `analyze` currently depends on cached local market data exposed through
  `DataConnector.load_symbol(...)` and `data/cache`.
- Confirmed `data/cache/SPY.parquet` already exists on this machine and verified a successful
  `analyze` smoke run against that cached dataset.
- Confirmed the knowledge-note files land under the expected vault path and remain easy to inspect.

### Command Results

- `python3 - <<'PY' ...` -> `EXA_API_KEY=missing`, `SERPAPI_KEY=missing`
- `uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output stdout`
  -> rendered a report successfully from local BM25 / ArXiv sources
- `uv run python cli.py research "intraday momentum strategy minute bars" --depth deep --output stdout`
  -> printed `Deep web search skipped: EXA_API_KEY / SERPAPI_KEY missing. Returning ArXiv-only report.`
- `python3 - <<'PY' ... Path('data/cache').glob('*') ...`
  -> confirmed `data/cache/SPY.parquet` exists before the smoke run
- `uv run python cli.py analyze SPY --start 2025-01-01 --output stdout`
  -> rendered a deterministic stock-analysis report using cached local market data
- `python3 - <<'PY' ... get_vault_paths().knowledge ...` -> confirmed all four knowledge notes in
  `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/knowledge`

### Blockers / Deviations

- The implementation machine still lacks `EXA_API_KEY` and `SERPAPI_KEY`, so deep mode remains a
  documented fallback path rather than an end-to-end external-web smoke pass.
- `analyze` is wired to cached market data in `data/cache`; successful smoke evidence now depends
  on that local cache being populated first.

### Follow-ups

- Closeout evidence should explicitly call out `data/cache` as the active analyze prerequisite until
  a different runtime surface is intentionally introduced.
- If review is repeated on a fresh machine, populate `data/cache/SPY*` first or document the clear
  missing-data path before judging the `analyze` smoke.
