# Sprint 3 -- Backend Plan

> Feature: `v2-data-pipeline`
> Role: Backend
> Scope: CLI commands + integration tests + documentation
> Last Updated: 2026-04-05

## 0) Governing Specs

1. `docs/data-pipeline-v2.md` -- Section 7 (CLI commands), Section 8 (file changes)
2. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md` -- Sprint 3 task table (CLI-01 through DOC-02)
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-test-plan.md` -- Full test plan
4. `docs/feature/v2-data-pipeline/v2-data-pipeline-backend.md` -- cross-sprint backend contract
5. `docs/feature/v2-data-pipeline/v2-data-pipeline-infra.md` -- runtime smoke-command and refresh expectations

## 1) Sprint Mission

Update CLI commands for the new data pipeline (`fetch` for minute queries, `backtest` for minute mode, `update-data` for incremental cache refresh), write integration tests for the full minute-level backtest pipeline, and update project documentation (`program.md`, `CLAUDE.md`) to reflect the V2 data pipeline architecture.

## 2) Scope / Out of Scope

**Scope**
- Update `cli.py fetch <symbol>` to query minute-level data via CLI subprocess
- Update `cli.py backtest` to run minute-level walk-forward backtest
- Add `cli.py update_data` for incremental DuckDB daily cache refresh
- Write `tests/integration/test_minute_backtest.py` (end-to-end pipeline)
- Update `tests/conftest.py` with DuckDB fixtures
- Update `program.md` with dataset documentation, CLI reference, strategy interface
- Update `CLAUDE.md` to reflect V2 data pipeline architecture
- Final verification: all tests pass, all CLI commands work

**Out of Scope**
- New strategy logic development
- Performance optimization (parallel queries, window caching)
- Overfit defense design (future session)
- Monte Carlo minute-level performance tuning

## 3) Step-by-Step Plan

### Step 1 -- Update CLI fetch (CLI-01)
- [x] Update `cli.py fetch <symbol>` command:
  - Accept `--start` and `--end` date arguments
  - Call `query_minute_data([symbol], start, end)`
  - Output results to stdout or `--output` file
  - Default: last 5 trading days if no dates specified
- [x] Verify: `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05`
- [x] Verify: output contains minute-level OHLCV data

### Step 2 -- Update CLI backtest (CLI-02)
- [x] Update `cli.py backtest` command:
  - Accept `--start` and `--end` for backtest period
  - Accept `--universe-size` to limit ticker count
  - Call backtester walk_forward_validation with minute mode
  - Output standard metrics format (SCORE, SORTINO, etc.)
- [x] Verify: `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31`
- [x] Verify: output includes all expected metrics + PER_SYMBOL section

### Step 3 -- Add CLI update_data (CLI-03)
- [x] Add `cli.py update_data` command:
  - Query latest date in DuckDB daily_bars
  - If cache exists: only aggregate months after latest date
  - If cache missing: run full build_daily_cache()
  - Append new daily bars to existing DuckDB file
- [x] Verify: `uv run python cli.py update-data`
- [x] Verify: new bars appended without duplicate rows

### Step 4 -- Write integration tests (TEST-03)
- [x] Create `tests/integration/test_minute_backtest.py`
- [x] Test: full minute backtest pipeline (daily -> universe -> minute -> signals -> metrics)
- [x] Test: walk-forward window boundaries (5 windows, correct trading days)
- [x] Test: per-ticker window queries (only selected tickers queried)
- [x] Test: signal lag enforcement in minute mode (shift(1))
- [x] Test: output format (SCORE, SORTINO, etc. present)
- [x] Note: integration tests use a fixture-backed temp DuckDB cache instead of relying on a pre-existing local cache
- [x] Run: `uv run pytest tests/integration/test_minute_backtest.py -v`

### Step 5 -- Update conftest.py (TEST-04)
- [x] Add DuckDB test fixtures to `tests/conftest.py`:
  - `test_duckdb_path` -- temp DuckDB file path fixture
  - `test_duckdb` -- temp DuckDB seeded with sample `daily_bars`
  - `sample_daily_data` -- DataFrame with a few tickers x few dates
- [x] Add a minute-mode strategy fixture for the restricted runtime contract
- [x] Verify: fixtures work with the new integration test file

### Step 6 -- Update program.md (DOC-01)
- [x] Add dataset documentation section:
  - massive-minute-aggs location, cache path, and CLI commands
  - DuckDB daily cache setup and incremental refresh semantics
- [x] Add CLI reference:
  - `setup-data`, `update-data`, `fetch`, `backtest`
  - Example commands with expected runtime shape
- [x] Update strategy interface section:
  - `select_universe(daily_data)` -- optional, receives full daily DataFrame
  - `generate_signals(minute_data)` -- receives `dict[str, pd.DataFrame]`
  - Document the default example strategy contract
- [x] Update data flow description:
  - Phase A: load daily from DuckDB
  - Phase B: select_universe
  - Phase C: query minute via CLI
  - Phase D: generate_signals
  - Phase E: walk-forward evaluation

### Step 7 -- Update CLAUDE.md (DOC-02)
- [x] Update Architecture section:
  - Data source: massive-minute-aggs via DuckDB + CLI
  - Remove references to yfinance/CCXT/Binance and parquet-cache workflow
- [x] Update Commands section:
  - `setup-data` builds the DuckDB daily cache
  - `update-data` refreshes the cache incrementally
  - `fetch` queries minute-level data
  - `backtest` supports minute mode
  - Remove old commands (`run`, `status`, `report`)
- [x] Update Key Components section:
  - Add `src/data/duckdb_connector.py`
  - Remove `src/data/connector.py`
- [x] Update Critical Patterns:
  - Strategy interface: dual-method (`select_universe` + `generate_signals`)
  - Walk-forward: minute-level with CLI subprocess queries

### Step 8 -- Final verification
- [x] `uv sync --all-extras --dev` succeeds
- [x] `pytest --tb=short -v` -- all tests pass, 0 failures
- [x] `uv run python cli.py setup-data --help` works
- [x] `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05` works
- [x] `uv run python cli.py backtest` works
- [x] `uv run python cli.py update-data` works
- [x] Global import scan: no references to old connector/preprocessor
- [x] runtime-module scan for `data.connector|data.preprocessor|DataConnector|prepare_data|Preprocessor` returns `CLEAN`

### Step 9 -- Commit sprint 3 changes
- [x] `git add cli.py tests/integration/test_minute_backtest.py tests/conftest.py program.md CLAUDE.md`
- [x] `git commit -m "feat(cli): finish sprint 3 minute-pipeline surface and verification"`

### Step 10 -- Push feature branch
- [x] `git push fork feature/v2-data-pipeline`

## 4) Test Plan

- [x] After Step 1: `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05` returns minute data
- [x] After Step 2: `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31` runs full pipeline and outputs metrics
- [x] After Step 3: `uv run python cli.py update-data` completes without duplicate-row regressions
- [x] After Step 4: integration tests pass
- [x] After Step 8: full test suite passes, all CLI commands work, no stale imports

## 5) Verification Commands (Final Gate)

```bash
# Dependency sync
uv sync --all-extras --dev

# Full test suite
uv run pytest --tb=short -v

# CLI command surface
uv run python cli.py setup-data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
uv run python cli.py update-data --help

# CLI smoke
uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py backtest
uv run python cli.py update-data

# Duplicate-row / stale-import checks
uv run python -c "import duckdb; con = duckdb.connect('data/daily_cache.duckdb', read_only=True); row = con.execute(\"SELECT COUNT(*), COUNT(DISTINCT ticker || ':' || CAST(session_date AS VARCHAR)), MAX(session_date) FROM daily_bars\").fetchone(); print(row); con.close()"
find src -type d -name '__pycache__' -prune -o -type f -name '*.py' -print0 | xargs -0 grep -n "data.connector\|data.preprocessor\|DataConnector\|prepare_data\|Preprocessor" || echo CLEAN
```

## 6) Implementation Update Space

### Completed Work

- Closed out Sprint 3 backend Step 3 in `cli.py` and `src/data/duckdb_connector.py`
- Added `refresh_daily_cache()` so the DuckDB daily cache now supports rebuild-on-miss, append-oriented refresh, and idempotent duplicate avoidance on `(ticker, session_date)`
- Added the `update-data` CLI command with stable output for rebuild, refresh, and already-current cases
- Added focused Step 3 coverage in `tests/unit/test_cli.py` and `tests/unit/test_duckdb_connector.py`
- Closed out Sprint 3 backend Step 4 by adding `tests/integration/test_minute_backtest.py`
- Added fixture-backed end-to-end coverage for the daily -> universe -> minute -> signals -> metrics pipeline, live walk-forward window boundaries, selected-ticker queries, signal lag enforcement, and output format
- Closed out Sprint 3 backend Step 5 by expanding `tests/conftest.py` with `test_duckdb_path`, `sample_daily_data`, `test_duckdb`, and `minute_strategy_file`
- Closed out Sprint 3 backend Step 6 by rewriting `program.md` to the V2 DuckDB/minute-data runtime contract
- Closed out Sprint 3 backend Step 7 by rewriting `CLAUDE.md` to the live CLI surface and V2 architecture
- Closed out Sprint 3 backend Step 8 by re-running the full regression gate plus CLI smoke commands on the feature worktree

### Command Results

- `uv run pytest tests/unit/test_cli.py -k update_data -v` -> `3 passed`
- `uv run pytest tests/unit/test_duckdb_connector.py -k refresh_daily_cache -v` -> `3 passed`
- `uv run pytest tests/integration/test_minute_backtest.py -v` -> `5 passed`
- `uv sync --all-extras --dev` -> succeeded (`Resolved 135 packages`, `Checked 118 packages`)
- `uv run pytest --tb=short -v` -> `143 passed in 1.64s`
- `uv run python cli.py setup-data --help` -> succeeded and exposed `--force`
- `uv run python cli.py fetch --help` -> succeeded and exposed `SYMBOL`, `--start`, `--end`, and `--output`
- `uv run python cli.py backtest --help` -> succeeded and exposed `--strategy`, `--start`, `--end`, and `--universe-size`
- `uv run python cli.py update-data --help` -> succeeded
- `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05` -> succeeded and printed minute-level OHLCV rows with CSV header
- `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31` -> succeeded and printed the standard metrics block plus `PER_SYMBOL`
- `uv run python cli.py backtest` -> succeeded and printed the standard metrics block plus `PER_SYMBOL`
- `uv run python cli.py update-data` -> succeeded; processed `2026-03` and `2026-04`, and reported `latest session date: 2026-03-30`
- Pre-refresh DuckDB check -> `rows=13273623 distinct_rows=13273623 latest=2026-03-30`
- Post-refresh DuckDB check -> `rows=13273623 distinct_rows=13273623 latest=2026-03-30 duplicates=0`
- Runtime-module stale-import scan -> `CLEAN`

### Blockers / Deviations

- `update-data` correctly took the incremental refresh path, but the local dataset did not expose sessions newer than `2026-03-30` at verification time, so the refresh completed as an idempotent no-op after checking partial March and April batches
- Typer command names are hyphenated (`setup-data`, `update-data`); Sprint 3 documentation was normalized away from older underscored spellings during closeout

### Follow-Ups

- Sprint 3 backend is complete
- Issue #11 can hand off to the final issue closeout / review decision with the Phase 4 verification evidence already collected in this sprint closeout
