# Sprint 3 -- Infra Plan

> Feature: `v2-data-pipeline`
> Role: Infra / Runtime
> Scope: CLI smoke verification, cache refresh semantics, and merge-gate evidence
> Last Updated: 2026-04-05

## 0) Governing Specs

1. `docs/data-pipeline-v2.md` -- Section 7 (CLI commands)
2. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md` -- Sprint 3 and Phase 4 tasks
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-infra.md` -- feature-level runtime contract
4. `docs/feature/v2-data-pipeline/v2-data-pipeline-test-plan.md` -- final verification expectations

## 1) Sprint Mission

Own the runtime proof that the final CLI and cache-refresh flows work outside unit tests. This
sprint captures the smoke evidence for `setup-data`, `fetch`, `backtest`, and `update-data`, and
checks that cache refresh behavior does not introduce duplicate daily rows.

## 2) Scope / Out Of Scope

**Scope**
- Validate help text and runtime availability for the CLI commands introduced by the feature
- Run final smoke commands for `setup-data`, `fetch`, `backtest`, and `update-data`
- Check DuckDB refresh behavior for duplicate-row regressions
- Capture review-ready runtime evidence for the issue or PR summary

**Out of Scope**
- Rewriting backend logic for DuckDB or backtester internals
- Unit-test authoring beyond what is needed to support smoke verification
- Performance optimization work beyond surfacing concrete runtime issues

## 3) Step-By-Step Plan

### Step 1 -- Validate CLI command surface
- [x] Run help for the relevant CLI commands and confirm the expected arguments are exposed
- [x] Confirm the documented example commands still match the actual CLI syntax
- [x] Record command-surface drift: live Typer commands are `setup-data` and `update-data`, not underscored spellings

### Step 2 -- Validate cache refresh semantics
- [x] Inspect the latest available `session_date` in `data/daily_cache.duckdb`
- [x] Run `uv run python cli.py update-data`
- [x] Re-check row counts and distinct `(ticker, session_date)` expectations after refresh
- [x] Record refresh behavior: append-oriented and idempotent when no newer sessions exist

### Step 3 -- Capture final smoke evidence
- [x] Run `uv run python cli.py setup-data --help`
- [x] Run `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05`
- [x] Run `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31`
- [x] Run `uv run python cli.py backtest`
- [x] Run `uv run python cli.py update-data`
- [x] Re-run security-focused tests under isolated temp directories so full regression leaves no repo-root artifacts
- [x] Capture the command outputs or summary observations for review

### Step 4 -- Feed runtime results into closeout
- [x] Record completed steps and command results in the update area below
- [x] Record blockers, deviations, or known limitations for review
- [x] Link runtime evidence back to the umbrella issue closeout summary

## 4) Test Plan

- [x] CLI help output matches the planned command surface
- [x] `fetch` returns minute-bar output for a known ticker/date range
- [x] `backtest` runs against the minute-data pipeline without crashing
- [x] `update-data` completes without duplicate-row regressions in DuckDB
- [x] Full regression does not leave repo-root test artifacts behind
- [x] Runtime evidence is captured in a reviewable location

## 5) Verification Commands

```bash
uv run python cli.py setup-data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
uv run python cli.py update-data --help

uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py backtest
uv run python cli.py update-data
uv run pytest tests/unit/test_security.py -v
uv run pytest tests/security/test_adversarial.py -v
uv run pytest --tb=short -v
git status --short --branch

uv run python -c "import duckdb; con = duckdb.connect('data/daily_cache.duckdb', read_only=True); row = con.execute(\"SELECT COUNT(*), COUNT(DISTINCT ticker || ':' || CAST(session_date AS VARCHAR)), MAX(session_date) FROM daily_bars\").fetchone(); print(row); con.close()"
```

## 6) Implementation Update Space

### Completed Work

- Closed out Sprint 3 infra Step 1 by re-validating the live CLI command surface for `setup-data`, `fetch`, `backtest`, and `update-data`
- Closed out Sprint 3 infra Step 2 by capturing DuckDB refresh semantics before and after `update-data`
- Closed out Sprint 3 infra Step 3 by re-running the final smoke commands against the feature worktree
- Closed out the final merge-gate hygiene regression by isolating security/adversarial tests to `tmp_path` so they no longer leave `strategy.py` in the repo root
- Closed out Sprint 3 infra Step 4 by recording runtime evidence for Sprint 3 closeout and the follow-on issue summary

### Command Results

- `uv run python cli.py setup-data --help` -> succeeded and exposed `--force`
- `uv run python cli.py fetch --help` -> succeeded and exposed `SYMBOL`, `--start`, `--end`, and `--output`
- `uv run python cli.py backtest --help` -> succeeded and exposed `--strategy`, `--start`, `--end`, and `--universe-size`
- `uv run python cli.py update-data --help` -> succeeded
- Pre-refresh DuckDB check -> `rows=13273623 distinct_rows=13273623 latest=2026-03-30`
- `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05` -> succeeded and printed minute OHLCV rows
- `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31` -> succeeded and printed the metrics block plus `PER_SYMBOL`
- `uv run python cli.py backtest` -> succeeded and printed the metrics block plus `PER_SYMBOL`
- `uv run python cli.py update-data` -> succeeded; processed `2026-03` and `2026-04`, and reported `latest session date: 2026-03-30`
- `uv run pytest tests/unit/test_security.py -v` -> `6 passed`; added a regression proving repo-root `strategy.py` is no longer created
- `uv run pytest tests/security/test_adversarial.py -v` -> `3 passed`; adversarial security checks now run with an isolated cwd
- `uv run pytest --tb=short -v` -> `144 passed in 1.15s`
- `git status --short --branch` after the full regression -> only intentional tracked doc/test edits remained; no stray `strategy.py` artifact
- Post-refresh DuckDB check -> `rows=13273623 distinct_rows=13273623 latest=2026-03-30 duplicates=0`

### Blockers / Deviations

- The incremental refresh path was exercised successfully, but the local dataset did not contain sessions newer than `2026-03-30`, so no new rows were appended during the verification run
- The runtime surface uses hyphenated Typer commands; infra closeout normalized docs away from older underscored command spellings
- A first post-closeout regression run surfaced repo-root `strategy.py` leakage from security tests; this was fixed within Sprint 3 closeout by isolating those tests to temp directories and re-running the gate

### Follow-Ups

- Sprint 3 infra is complete
- The issue-level closeout note should reference this runtime evidence and the clean post-pytest worktree when moving issue #11 toward review
