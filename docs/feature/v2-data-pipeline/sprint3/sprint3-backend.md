# Sprint 3 -- Backend Plan

> Feature: `v2-data-pipeline`
> Role: Backend
> Scope: CLI commands + integration tests + documentation
> Last Updated: 2026-04-04

## 0) Governing Specs

1. `docs/data-pipeline-v2.md` -- Section 7 (CLI commands), Section 8 (file changes)
2. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md` -- Sprint 3 task table (CLI-01 through DOC-02)
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-test-plan.md` -- Full test plan
4. `docs/feature/v2-data-pipeline/v2-data-pipeline-backend.md` -- cross-sprint backend contract
5. `docs/feature/v2-data-pipeline/v2-data-pipeline-infra.md` -- runtime smoke-command and refresh expectations

## 1) Sprint Mission

Update CLI commands for the new data pipeline (`fetch` for minute queries, `backtest` for minute mode, `update_data` for incremental cache refresh), write integration tests for the full minute-level backtest pipeline, and update project documentation (`program.md`, `CLAUDE.md`) to reflect the V2 data pipeline architecture.

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
- [ ] Update `cli.py fetch <symbol>` command:
  - Accept `--start` and `--end` date arguments
  - Call `query_minute_data([symbol], start, end)`
  - Output results to stdout or `--output` file
  - Default: last 5 trading days if no dates specified
- [ ] Verify: `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05`
- [ ] Verify: output contains minute-level OHLCV data

### Step 2 -- Update CLI backtest (CLI-02)
- [ ] Update `cli.py backtest` command:
  - Accept `--start` and `--end` for backtest period
  - Accept `--universe-size` to limit ticker count
  - Call backtester walk_forward_validation with minute mode
  - Output standard metrics format (SCORE, SORTINO, etc.)
- [ ] Verify: `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31`
- [ ] Verify: output includes all expected metrics + PER_SYMBOL section

### Step 3 -- Add CLI update_data (CLI-03)
- [ ] Add `cli.py update_data` command:
  - Query latest date in DuckDB daily_bars
  - If cache exists: only aggregate months after latest date
  - If cache missing: run full build_daily_cache()
  - Append new daily bars to existing DuckDB file
- [ ] Verify: `uv run python cli.py update_data`
- [ ] Verify: new bars appended without duplicate rows

### Step 4 -- Write integration tests (TEST-03)
- [ ] Create `tests/integration/test_minute_backtest.py`
- [ ] Test: full minute backtest pipeline (daily -> universe -> minute -> signals -> metrics)
- [ ] Test: walk-forward window boundaries (5 windows, correct trading days)
- [ ] Test: per-ticker window queries (only selected tickers queried)
- [ ] Test: signal lag enforcement in minute mode (shift(1))
- [ ] Test: output format (SCORE, SORTINO, etc. present)
- [ ] Note: integration tests may require DuckDB cache to exist; use test fixture or skip if unavailable
- [ ] Run: `pytest tests/integration/test_minute_backtest.py -v`

### Step 5 -- Update conftest.py (TEST-04)
- [ ] Add DuckDB test fixtures to `tests/conftest.py`:
  - `test_duckdb_path` -- temp DuckDB file path fixture
  - `test_duckdb` -- in-memory or temp DuckDB with sample daily_bars
  - `sample_daily_data` -- DataFrame with a few tickers x few dates
- [ ] Update any existing fixtures that reference old `connector.py`
- [ ] Verify: fixtures work with new test files

### Step 6 -- Update program.md (DOC-01)
- [ ] Add dataset documentation section:
  - massive-minute-aggs location, schema, CLI commands
  - DuckDB daily cache: schema, setup, update
- [ ] Add CLI reference:
  - `setup_data`, `update_data`, `fetch`, `backtest`
  - Example commands with expected output
- [ ] Update strategy interface section:
  - `select_universe(daily_data)` -- optional, receives full daily DataFrame
  - `generate_signals(minute_data)` -- receives dict[str, DataFrame]
  - Example dual-method strategy
- [ ] Update data flow description:
  - Phase A: load daily from DuckDB
  - Phase B: select_universe
  - Phase C: query minute via CLI
  - Phase D: generate_signals
  - Phase E: walk-forward evaluation

### Step 7 -- Update CLAUDE.md (DOC-02)
- [ ] Update Architecture section:
  - Data source: massive-minute-aggs via DuckDB + CLI
  - Remove references to yfinance/CCXT
- [ ] Update Commands section:
  - `setup_data` now builds DuckDB daily cache
  - `fetch` queries minute-level data
  - `backtest` supports minute mode
  - Remove old commands (run, status, report)
- [ ] Update Key Components section:
  - Add `src/data/duckdb_connector.py`
  - Remove `src/data/connector.py`
- [ ] Update Critical Patterns:
  - Strategy interface: dual-method (select_universe + generate_signals)
  - Walk-forward: minute-level with CLI subprocess queries

### Step 8 -- Final verification
- [ ] `uv sync --all-extras --dev` succeeds
- [ ] `pytest --tb=short -v` -- all tests pass, 0 failures
- [ ] `uv run python cli.py setup_data --help` works
- [ ] `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05` works
- [ ] `uv run python cli.py backtest` works
- [ ] `uv run python cli.py update_data` works
- [ ] Global import scan: no references to old connector/preprocessor
- [ ] `grep -rn "from src.data.connector\|from src.data.preprocessor" src/ tests/ cli.py` returns 0 hits

### Step 9 -- Commit sprint 3 changes
- [ ] `git add cli.py tests/integration/test_minute_backtest.py tests/conftest.py program.md CLAUDE.md`
- [ ] `git commit -m "feat(cli): add minute-level fetch/backtest/update_data commands, integration tests, docs"`

### Step 10 -- Push feature branch
- [ ] `git push origin feature/v2-data-pipeline` (or fork)

## 4) Test Plan

- [ ] After Step 1: `uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05` returns minute data
- [ ] After Step 2: `uv run python cli.py backtest` runs full pipeline and outputs metrics
- [ ] After Step 3: `uv run python cli.py update_data` appends new bars
- [ ] After Step 4: integration tests pass
- [ ] After Step 8: full test suite passes, all CLI commands work, no stale imports

## 5) Verification Commands (Final Gate)

```bash
# Dependency sync
uv sync --all-extras --dev && echo "DEPS OK"

# All imports
python -c "
from src.data.duckdb_connector import build_daily_cache, load_daily_data, get_trading_days, query_minute_data
from src.core.backtester import *
from src.strategies.active_strategy import *
from src.utils.logger import logger
print('ALL IMPORTS OK')
"

# Full test suite
pytest --tb=short -v

# CLI commands
uv run python cli.py setup_data --help
uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py update_data

# No removed module references
grep -rn "from src.data.connector\|from src.data.preprocessor\|DataConnector\|Preprocessor" src/ tests/ cli.py || echo "ZERO REFERENCES TO REMOVED MODULES"
```

## 6) Implementation Update Space

### Completed Work

(To be filled during implementation)

### Command Results

(To be filled during implementation)

### Blockers / Deviations

(To be filled during implementation)

### Follow-ups

- All sprints complete -- issue ready for review
- Future: overfit defense design, Monte Carlo minute-level tuning, parallel CLI queries
