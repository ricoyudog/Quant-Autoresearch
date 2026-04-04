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
- [ ] Create `src/data/duckdb_connector.py`
- [ ] Implement `build_daily_cache(output_path)`:
  - Connect to DuckDB at `output_path` (default: `data/daily_cache.duckdb`)
  - Create `daily_bars` table with schema from spec
  - Loop year/month from 2021-03 to current date
  - For each month: call `minute-aggs sql` with aggregation query, output to CSV, load CSV into DuckDB
  - Clean up temp CSVs
  - Create PRIMARY KEY index on (ticker, session_date)
- [ ] Implement `load_daily_data(start_date, end_date)`:
  - Open DuckDB read-only
  - Query with optional date range filter
  - Return pd.DataFrame
- [ ] Implement `get_trading_days(start_date, end_date)`:
  - Query DISTINCT session_date from daily_bars
  - Return ordered list of date strings
- [ ] Implement `query_minute_data(tickers, start_date, end_date)`:
  - Build CLI subprocess command: `minute-aggs bars --symbols ... --start ... --end ... --output /tmp/...`
  - Run subprocess with 300s timeout
  - Parse CSV output, group by ticker
  - Return dict[str, pd.DataFrame]
  - Handle errors: CLI failure, missing output, timeout
- [ ] Verify: `python -c "from src.data.duckdb_connector import build_daily_cache, load_daily_data, get_trading_days, query_minute_data; print('IMPORT OK')"`

### Step 4 -- Update cli.py setup_data (DUCK-06)
- [ ] Update `cli.py setup_data` command to call `build_daily_cache()`
- [ ] Add progress output (year/month being processed)
- [ ] Add `--force` flag to rebuild from scratch
- [ ] Verify: `uv run python cli.py setup_data` (dry-run or short test)

### Step 5 -- Remove old data modules
- [ ] `git rm src/data/connector.py`
- [ ] `git rm src/data/preprocessor.py`
- [ ] Search for references: `grep -rn "from src.data.connector\|from src.data.preprocessor\|DataConnector\|Preprocessor" src/ tests/ cli.py`
- [ ] Clean any imports found in surviving files
- [ ] Verify: `grep -rn "DataConnector\|Preprocessor" src/ cli.py` returns 0 hits

### Step 6 -- Write unit tests (DUCK-07)
- [ ] Create `tests/unit/test_duckdb_connector.py`
- [ ] Test `build_daily_cache`: creates file, correct schema, primary key
- [ ] Test `load_daily_data`: returns DataFrame, date filtering, all tickers
- [ ] Test `get_trading_days`: ordered list, date range
- [ ] Test `query_minute_data`: returns dict, per-ticker split, timeout handling
- [ ] Use test fixtures: in-memory DuckDB or temp file
- [ ] Run: `pytest tests/unit/test_duckdb_connector.py -v`

### Step 7 -- Commit sprint 1 changes
- [ ] `git add src/data/duckdb_connector.py tests/unit/test_duckdb_connector.py pyproject.toml cli.py`
- [ ] `git rm src/data/connector.py src/data/preprocessor.py` (if not already staged)
- [ ] `git commit -m "feat(data): add DuckDB connector for daily cache, remove old connector"`

## 4) Test Plan

- [ ] After Step 2: `uv sync` succeeds, `import duckdb` works
- [ ] After Step 3: `from src.data.duckdb_connector import *` works
- [ ] After Step 4: `uv run python cli.py setup_data --help` shows new flags
- [ ] After Step 5: no imports of old connector/preprocessor in surviving files
- [ ] After Step 6: all new unit tests pass
- [ ] Verify surviving tests still pass: `pytest --tb=short -q`

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
grep -rn "from src.data.connector\|from src.data.preprocessor\|DataConnector\|Preprocessor" src/ tests/ cli.py || echo "ALL CLEAN"

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

### Blockers / Deviations

- The environment does not expose a global `pytest` binary on `PATH`; `uv run pytest` is the
  working repo-equivalent baseline command here.
- The baseline was initially blocked by logger setup assuming `experiments/logs/` already existed.
  That blocker is now resolved.
- No blocking issues found while adding the DuckDB dependency.

### Follow-ups

- Sprint 2: strategy interface (`select_universe`), backtester minute-level integration
- Proceed to Sprint 1 Step 3 with TDD discipline before changing DuckDB-related production code.
