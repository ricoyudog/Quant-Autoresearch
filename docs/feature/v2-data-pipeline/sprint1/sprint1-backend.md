> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Sprint 1 -- Backend Plan

> Feature: `v2-data-pipeline`
> Role: Backend
> Scope: DuckDB integration + daily aggregation cache
> Last Updated: 2026-04-04

## 0) Governing Specs

1. `docs/data-pipeline-v2.md` -- Section 1 (data source), Section 2 (architecture), Section 3 (daily cache / DuckDB)
2. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md` -- Sprint 1 task table (DUCK-01 through DUCK-07)
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-backend.md` -- cross-sprint backend contract
4. `docs/feature/v2-data-pipeline/v2-data-pipeline-infra.md` -- runtime paths, CLI binary, and smoke-command expectations

## 1) Sprint Mission

Add DuckDB as a project dependency and create `src/data/duckdb_connector.py` to manage a pre-computed daily aggregation cache built from the massive-minute-aggs dataset. The daily cache aggregates 11K+ tickers of minute-level OHLCV data into daily bars stored in a local DuckDB file. Update `cli.py setup_data` to trigger the cache build. This is the foundation for strategy-driven universe selection in Sprint 2.

## 2) Scope / Out of Scope

**Scope**
- Add `duckdb` to `pyproject.toml` dependencies
- Create `src/data/duckdb_connector.py` with:
  - `build_daily_cache(output_path)` -- month-by-month CLI SQL aggregation into DuckDB
  - `load_daily_data(start_date, end_date)` -- query daily bars from DuckDB
  - `get_trading_days(start_date, end_date)` -- distinct trading dates from cache
  - `query_minute_data(tickers, start_date, end_date)` -- CLI subprocess for minute bars
- Update `cli.py setup_data` to call `build_daily_cache()`
- Write `tests/unit/test_duckdb_connector.py`
- Remove `src/data/connector.py` and `src/data/preprocessor.py`
- Clean all imports referencing removed modules

**Out of Scope**
- Strategy interface changes (`select_universe`) -- Sprint 2
- Backtester minute-level walk-forward -- Sprint 2
- CLI `fetch`, `backtest`, `update_data` commands -- Sprint 3
- `program.md` updates -- Sprint 3
- Integration tests -- Sprint 3

## 3) Step-by-Step Plan

### Step 1 -- Create feature branch + baseline (DUCK-01)
- [x] `git checkout -b feature/v2-data-pipeline main`
- [x] Run `pytest --tb=short -q` and record test count as baseline
- [x] Record baseline: `92 pass, 0 fail`

### Step 2 -- Add DuckDB dependency (DUCK-02)
- [x] Edit `pyproject.toml`: add `duckdb>=1.0.0` to dependencies
- [x] Run `uv sync` and verify DuckDB installs
- [x] Verify: `python -c "import duckdb; print(duckdb.__version__)"`

### Step 3 -- Create duckdb_connector.py (DUCK-03, DUCK-04, DUCK-05)
- [x] Create `src/data/duckdb_connector.py`
- [x] Implement `build_daily_cache(output_path)`:
  - Connect to DuckDB at `output_path` (default: `data/daily_cache.duckdb`)
  - Create `daily_bars` table with schema from spec
  - Loop year/month from 2021-03 to current date
  - For each month: call `minute-aggs sql` with aggregation query, output to CSV, load CSV into DuckDB
  - Clean up temp CSVs
  - Create PRIMARY KEY index on (ticker, session_date)
- [x] Implement `load_daily_data(start_date, end_date)`:
  - Open DuckDB read-only
  - Query with optional date range filter
  - Return pd.DataFrame
- [x] Implement `get_trading_days(start_date, end_date)`:
  - Query DISTINCT session_date from daily_bars
  - Return ordered list of date strings
- [x] Implement `query_minute_data(tickers, start_date, end_date)`:
  - Build CLI subprocess command: `minute-aggs bars --symbols ... --start ... --end ... --output /tmp/...`
  - Run subprocess with 300s timeout
  - Parse CSV output, group by ticker
  - Return dict[str, pd.DataFrame]
  - Handle errors: CLI failure, missing output, timeout
- [x] Verify: `python -c "from src.data.duckdb_connector import build_daily_cache, load_daily_data, get_trading_days, query_minute_data; print('IMPORT OK')"`

### Step 4 -- Update cli.py setup_data (DUCK-06)
- [x] Update `cli.py setup_data` command to call `build_daily_cache()`
- [x] Add progress output (year/month being processed)
- [x] Add `--force` flag to rebuild from scratch
- [x] Verify: `uv run python cli.py setup-data` (dry-run or short test)

### Step 5 -- Remove old data modules
- [x] `git rm src/data/connector.py`
- [x] `git rm src/data/preprocessor.py`
- [x] Search for references: `grep -rn "data.connector\|data.preprocessor\|DataConnector\|prepare_data\|Preprocessor" src/ tests/ cli.py`
- [x] Clean any imports found in surviving files
- [x] Verify: `grep -rn "data.connector\|data.preprocessor\|DataConnector\|prepare_data\|Preprocessor" src/ cli.py` returns 0 hits

### Step 6 -- Write unit tests (DUCK-07)
- [x] Create `tests/unit/test_duckdb_connector.py`
- [x] Test `build_daily_cache`: creates file, correct schema, primary key
- [x] Test `load_daily_data`: returns DataFrame, date filtering, all tickers
- [x] Test `get_trading_days`: ordered list, date range
- [x] Test `query_minute_data`: returns dict, per-ticker split, timeout handling
- [x] Use test fixtures: in-memory DuckDB or temp file
- [x] Run: `pytest tests/unit/test_duckdb_connector.py -v`

### Step 7 -- Commit sprint 1 changes
- [x] `git add src/data/duckdb_connector.py tests/unit/test_duckdb_connector.py pyproject.toml cli.py`
- [x] `git rm src/data/connector.py src/data/preprocessor.py` (if not already staged)
- [x] Record the Sprint 1 backend implementation in atomic commits instead of a single squash commit

## 4) Test Plan

- [x] After Step 2: `uv sync` succeeds, `import duckdb` works
- [x] After Step 3: `from src.data.duckdb_connector import *` works
- [x] After Step 4: `uv run python cli.py setup-data --help` shows new flags
- [x] After Step 5: no imports of old connector/preprocessor in surviving files
- [x] After Step 6: all new unit tests pass
- [x] Verify surviving tests still pass: `pytest --tb=short -q`

## 5) Verification Commands

```bash
# DuckDB dependency
python -c "import duckdb; print(f'DuckDB {duckdb.__version__}')"

# New module imports
python -c "from src.data.duckdb_connector import build_daily_cache, load_daily_data, get_trading_days, query_minute_data; print('ALL IMPORTS OK')"

# Old modules removed
test ! -f src/data/connector.py && echo "connector.py GONE"
test ! -f src/data/preprocessor.py && echo "preprocessor.py GONE"

# No references to old modules
grep -rn "data.connector\|data.preprocessor\|DataConnector\|prepare_data\|Preprocessor" src/ cli.py || echo "ALL CLEAN"

# Tests pass
pytest tests/unit/test_duckdb_connector.py -v
pytest --tb=short -q
```

## 6) Implementation Update Space

### Completed Work

- Confirmed the execution surface is the dedicated worktree at
  `/private/tmp/quant-worktrees/feature/v2-data-pipeline` on branch
  `feature/v2-data-pipeline`, so the branch-creation intent of Step 1 is already satisfied.
- Ran the Sprint 1 baseline test command via `uv run pytest --tb=short -q` because `pytest` is not
  available on the shell `PATH` in this environment.
- Resolved the baseline collection blocker in `src/utils/logger.py` by creating the parent log
  directory before instantiating `RotatingFileHandler`.
- Added `tests/unit/test_logger.py` as a regression test to prove `utils.logger` can be imported
  when `experiments/logs/` does not exist yet.
- Re-ran the baseline after the logger fix and got a clean result.
- Added `duckdb>=1.0.0` to `pyproject.toml` under `[project].dependencies`.
- Ran `uv sync`, which installed `duckdb==1.5.1`.
- Verified `duckdb` imports successfully from the repo environment.
- Added `src/data/duckdb_connector.py` with additive-only Step 3 behavior so existing CLI and
  backtester imports were left untouched for Step 4 / Step 5.
- Implemented `build_daily_cache()`, `load_daily_data()`, `get_trading_days()`, and
  `query_minute_data()` in the new module.
- Used month-by-month range generation from `2021-03` through the current month with actual
  month-end boundaries instead of the spec sample's fixed day-28 shortcut.
- Added `tests/unit/test_duckdb_connector.py` as Step 3 TDD coverage for schema creation, date
  filtering, trading-day ordering, minute-query splitting, and timeout handling.
- Verified the new module imports cleanly from `src.data.duckdb_connector`.
- Re-ran the full repo baseline after the additive connector landed and got a clean result.
- Updated `cli.py setup_data` to call `build_daily_cache()` from `data.duckdb_connector` while
  keeping the legacy `DataConnector` fetch path intact for the remaining Sprint 1 steps.
- Added per-month progress output to the CLI through a `build_daily_cache()` progress callback.
- Added a `--force` flag so `setup-data` skips an existing cache by default and only rebuilds when
  explicitly requested.
- Added CLI unit coverage for the `setup-data` missing-cache, skip, and forced-rebuild paths.
- Verified the Step 4 CLI surface through `setup-data --help`, a skip-path dry-run, and a fresh
  full-suite regression run.
- Added `src/data/cache_connector.py` as the surviving cache-loader module and renamed the runtime
  class to `CacheConnector` so the legacy `DataConnector` symbol no longer appears in live code.
- Removed `src/data/connector.py` and `src/data/preprocessor.py`.
- Updated `cli.py` and `src/core/backtester.py` to import `CacheConnector` from
  `data.cache_connector`.
- Replaced the obsolete preprocessor-based unit test with direct `CacheConnector` coverage and
  added a cleanup test that locks down file removal plus no stale import strings in live runtime
  modules.
- Verified the old-module file checks, stale-import grep, and full test suite after the cleanup.
- Finalized the dedicated `duckdb_connector` unit-test checklist with a verbose targeted run.
- Carried Sprint 1 backend forward as incremental, reviewable commits instead of a single large
  squash commit so each step remains independently auditable.

### Command Results

- Worktree / branch verification:
  - `pwd` -> `/private/tmp/quant-worktrees/feature/v2-data-pipeline`
  - `git branch --show-current` -> `feature/v2-data-pipeline`
  - `git status --short` -> clean before the baseline fix work started
- Initial baseline attempt:
  - `pytest --tb=short -q` -> `command not found`
  - equivalent repo command: `uv run pytest --tb=short -q`
  - first `uv run pytest --tb=short -q` result: interrupted during collection with 9 errors
  - shared root cause: missing `experiments/logs/run.log` parent directory during `utils.logger`
    import
- Regression TDD cycle for the blocker:
  - RED: `uv run pytest tests/unit/test_logger.py -q` -> `1 failed`
  - GREEN: `uv run pytest tests/unit/test_logger.py -q` -> `1 passed`
- Final baseline:
  - `uv run pytest --tb=short -q` -> `92 passed in 2.59s`
- DuckDB dependency step:
  - `uv sync` -> success; installed `duckdb==1.5.1`
  - `uv run python -c "import duckdb; print(duckdb.__version__)"` -> `1.5.1`
- Step 3 TDD cycle:
  - RED: `uv run pytest tests/unit/test_duckdb_connector.py -q` -> `5 failed`
  - GREEN: `uv run pytest tests/unit/test_duckdb_connector.py -q` -> `5 passed in 0.05s`
- Step 3 import verification:
  - `uv run python -c "from src.data.duckdb_connector import build_daily_cache, load_daily_data,
    get_trading_days, query_minute_data; print('IMPORT OK')"` -> `IMPORT OK`
- Post-Step 3 regression:
  - `uv run pytest --tb=short -q` -> `97 passed in 1.15s`
- Step 4 TDD cycle:
  - RED: `uv run pytest tests/unit/test_duckdb_connector.py tests/unit/test_cli.py -q` ->
    `4 failed`
  - GREEN: `uv run pytest tests/unit/test_duckdb_connector.py tests/unit/test_cli.py -q` ->
    `21 passed in 0.41s`
- Step 4 CLI verification:
  - `uv run python cli.py setup-data --help` -> shows `--force`
  - dry-run path: `uv run python cli.py setup-data` with a temporary existing
    `data/daily_cache.duckdb` -> `Daily cache already exists at data/daily_cache.duckdb. Use
    --force to rebuild.`
- Post-Step 4 regression:
  - `uv run pytest --tb=short -q` -> `101 passed in 1.16s`
- Step 5 TDD cycle:
  - RED 1: `uv run pytest tests/unit/test_data.py tests/unit/test_legacy_data_cleanup.py -q` ->
    `4 failed`
  - RED 2: `uv run pytest tests/unit/test_data.py tests/unit/test_legacy_data_cleanup.py
    tests/unit/test_cli.py -q` -> `6 failed`
  - GREEN: `uv run pytest tests/unit/test_data.py tests/unit/test_legacy_data_cleanup.py
    tests/unit/test_cli.py -q` -> `19 passed in 0.36s`
- Step 5 cleanup verification:
  - `test ! -f src/data/connector.py && test ! -f src/data/preprocessor.py` -> success
  - `rg -n "data.connector|data.preprocessor|from src.data.connector|from src.data.preprocessor|DataConnector|prepare_data|Preprocessor" src/ cli.py` -> no output
- Post-Step 5 regression:
  - `uv run pytest --tb=short -q` -> `104 passed in 0.89s`
- Step 6 targeted verification:
  - `uv run pytest tests/unit/test_duckdb_connector.py -v` -> `6 passed in 0.06s`

### Blockers / Deviations

- The environment does not expose a global `pytest` binary on `PATH`; `uv run pytest` is the
  working repo-equivalent baseline command here.
- The baseline was initially blocked by logger setup assuming `experiments/logs/` already existed.
  That blocker is now resolved.
- No blocking issues found while adding the DuckDB dependency.
- The planned Step 5 grep command currently searches `src.data.connector` /
  `src.data.preprocessor`, but the live repo imports use `data.connector` / `data.preprocessor`.
  Update that cleanup scan before Step 5 starts so it does not report a false clean state.
- Step 3 stayed additive by design; `cli.py`, `src/core/backtester.py`, and the legacy tests still
  target the old `DataConnector` path until Step 4 / Step 5 migrate them.
- Typer exposes the CLI command as `setup-data`, not `setup_data`. Use the hyphenated form in
  verification commands and docs.
- This environment still does not provide bare `python` / `pytest` on `PATH`; repo-equivalent
  commands remain `uv run python ...` and `uv run pytest ...`.
- Step 5 resolved the stale cleanup scan by switching it from the nonexistent `src.data.*` import
  pattern to the live repo `data.*` import pattern.

### Follow-ups

- Sprint 1 backend execution checklist is complete. Continue with Sprint 1 closeout / integration
  bookkeeping only as needed from the issue-level workflow.
- Sprint 2 remains unchanged: strategy interface (`select_universe`) and minute-level backtester
  integration stay out of scope until Sprint 1 is complete.
