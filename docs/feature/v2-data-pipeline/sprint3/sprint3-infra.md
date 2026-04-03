# Sprint 3 -- Infra Plan

> Feature: `v2-data-pipeline`
> Role: Infra / Runtime
> Scope: CLI smoke verification, cache refresh semantics, and merge-gate evidence
> Last Updated: 2026-04-04

## 0) Governing Specs

1. `docs/data-pipeline-v2.md` -- Section 7 (CLI commands)
2. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md` -- Sprint 3 and Phase 4 tasks
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-infra.md` -- feature-level runtime contract
4. `docs/feature/v2-data-pipeline/v2-data-pipeline-test-plan.md` -- final verification expectations

## 1) Sprint Mission

Own the runtime proof that the final CLI and cache-refresh flows work outside unit tests. This
sprint captures the smoke evidence for `setup_data`, `fetch`, `backtest`, and `update_data`, and
checks that cache refresh behavior does not introduce duplicate daily rows.

## 2) Scope / Out Of Scope

**Scope**
- Validate help text and runtime availability for the CLI commands introduced by the feature
- Run final smoke commands for `setup_data`, `fetch`, `backtest`, and `update_data`
- Check DuckDB refresh behavior for duplicate-row regressions
- Capture review-ready runtime evidence for the issue or PR summary

**Out of Scope**
- Rewriting backend logic for DuckDB or backtester internals
- Unit-test authoring beyond what is needed to support smoke verification
- Performance optimization work beyond surfacing concrete runtime issues

## 3) Step-By-Step Plan

### Step 1 -- Validate CLI command surface
- [ ] Run help for the relevant CLI commands and confirm the expected arguments are exposed
- [ ] Confirm the documented example commands still match the actual CLI syntax
- [ ] Record any command-surface drift before the final smoke run

### Step 2 -- Validate cache refresh semantics
- [ ] Inspect the latest available `session_date` in `data/daily_cache.duckdb`
- [ ] Run `uv run python cli.py update_data`
- [ ] Re-check row counts and distinct `(ticker, session_date)` expectations after refresh
- [ ] Record whether refresh is append-only, rebuild-on-miss, or otherwise special-cased

### Step 3 -- Capture final smoke evidence
- [ ] Run `uv run python cli.py setup_data --help`
- [ ] Run `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05`
- [ ] Run `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31`
- [ ] Run `uv run python cli.py update_data`
- [ ] Capture the command outputs or summary observations for review

### Step 4 -- Feed runtime results into closeout
- [ ] Record completed steps and command results in the update area below
- [ ] Record blockers, deviations, or known limitations for review
- [ ] Link runtime evidence back to the umbrella issue or PR summary

## 4) Test Plan

- [ ] CLI help output matches the planned command surface
- [ ] `fetch` returns minute-bar output for a known ticker/date range
- [ ] `backtest` runs against the minute-data pipeline without crashing
- [ ] `update_data` completes without duplicate-row regressions in DuckDB
- [ ] Runtime evidence is captured in a reviewable location

## 5) Verification Commands

```bash
uv run python cli.py setup_data --help
uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py update_data

python -c "
import duckdb
con = duckdb.connect('data/daily_cache.duckdb', read_only=True)
print(con.execute('SELECT COUNT(*) FROM daily_bars').fetchone())
print(con.execute('SELECT COUNT(*) - COUNT(DISTINCT ticker || \":\" || CAST(session_date AS VARCHAR)) FROM daily_bars').fetchone())
con.close()
"
```

## 6) Implementation Update Space

### Completed Work

(To be filled during implementation)

### Command Results

(To be filled during implementation)

### Blockers / Deviations

(To be filled during implementation)

### Follow-Ups

- Close any runtime gaps before the issue is marked review-ready
