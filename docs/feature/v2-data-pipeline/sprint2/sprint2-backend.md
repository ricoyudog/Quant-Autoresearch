# Sprint 2 -- Backend Plan

> Feature: `v2-data-pipeline`
> Role: Backend
> Scope: Strategy interface + backtester minute-level integration
> Last Updated: 2026-04-04

## 0) Governing Specs

1. `docs/data-pipeline-v2.md` -- Section 4 (backtester data flow), Section 5 (strategy interface), Section 6 (walk-forward design)
2. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md` -- Sprint 2 task table (STRAT-01 through STRAT-07)
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-backend.md` -- cross-sprint backend contract

## 1) Sprint Mission

Extend the strategy interface with `select_universe(daily_data)` for strategy-driven ticker screening from the 11K+ universe, and update the backtester to support minute-level walk-forward validation. The backtester will load daily data from DuckDB, call `select_universe()` to narrow the universe, then query minute-level bars via CLI subprocess for each walk-forward window before invoking `generate_signals()`.

## 2) Scope / Out of Scope

**Scope**
- Add `select_universe(daily_data) -> list[str]` to strategy interface (optional method)
- Update `generate_signals(data: dict[str, pd.DataFrame]) -> dict[str, pd.Series]` for minute data
- Update `find_strategy_methods()` to detect `select_universe` presence
- Implement minute-level walk-forward window calculation using `get_trading_days()`
- Integrate DuckDB daily loading + CLI minute queries into backtester pipeline
- Update `src/strategies/active_strategy.py` with a working dual-method example
- Write `tests/unit/test_strategy_interface.py`

**Out of Scope**
- CLI commands (`fetch`, `backtest`, `update_data`) -- Sprint 3
- Integration tests -- Sprint 3
- `program.md` documentation update -- Sprint 3
- Monte Carlo permutation test performance tuning -- future work

## 3) Step-by-Step Plan

### Step 1 -- Add select_universe to strategy interface (STRAT-01)
- [x] Define `select_universe(self, daily_data: pd.DataFrame) -> list[str]` in strategy docs/interface
- [x] Update `src/strategies/active_strategy.py`:
  - Add `select_universe()` method (with default: return top volume tickers)
  - Document that it receives full daily_data DataFrame from DuckDB
  - Document return format: list of ticker strings
- [x] Verify: `python -c "from src.strategies.active_strategy import *; print('IMPORT OK')"`

### Step 2 -- Create query_minute_data function (STRAT-02)
- [x] Verify `query_minute_data()` in `duckdb_connector.py` works (from Sprint 1)
- [x] If not yet implemented, implement CLI subprocess call:
  - `minute-aggs bars --symbols <tickers> --start <date> --end <date> --output <csv>`
  - Parse CSV, group by ticker, return dict[str, pd.DataFrame]
- [x] Test with a small query: AAPL for 1 week
- [x] Verify: returns correct schema and data

### Step 3 -- Update find_strategy_methods (STRAT-03)
- [x] Locate `find_strategy_methods()` or `find_strategy_class()` in `src/core/backtester.py`
- [x] Update return value: `(class, has_universe)` tuple
- [x] `has_universe = hasattr(obj, 'select_universe')`
- [x] If no method found, return `(None, False)`
- [x] Verify: test with a class that has both methods, one method, and no methods

### Step 4 -- Update generate_signals for minute data (STRAT-04)
- [ ] Update `generate_signals()` signature in strategy to accept `dict[str, pd.DataFrame]`
- [ ] Each key = ticker, each value = minute DataFrame with OHLCV
- [ ] Return `dict[str, pd.Series]` with signal values in {-1, 0, 1}
- [ ] Update signal lag enforcement: `shift(1)` applied per ticker
- [ ] Verify: signals index aligns with minute data index

### Step 5 -- Implement minute-level walk-forward (STRAT-05)
- [ ] Implement `calculate_walk_forward_windows(start_date, end_date, n_windows=5)`:
  - Call `get_trading_days()` to get ordered trading date list
  - Divide into n_windows equal-sized chunks
  - For each window: train = [0 .. train_end], test = [test_start .. test_end]
  - Return list of window dicts with train/test boundaries
- [ ] Each window boundary is a trading date (not calendar date)
- [ ] Each test window contains full trading sessions (390 bars/day)
- [ ] Verify: 5 windows, no date gaps, no overlap

### Step 6 -- Integrate into backtester (STRAT-06)
- [ ] Update `src/core/backtester.py` walk_forward_validation():
  - Phase A: Load daily data from DuckDB via `load_daily_data()`
  - Phase B: Call `strategy.select_universe(daily_data)` if available
    - If no `select_universe`: use default tickers or all tickers
  - Phase C: For each walk-forward window:
    - Query minute data via `query_minute_data(selected_tickers, test_start, test_end)`
    - Call `strategy.generate_signals(minute_data_dict)`
    - Apply signal lag (shift 1 per ticker)
    - Calculate returns, Sharpe, Sortino, Calmar, etc.
  - Phase D: Aggregate across windows
  - Phase E: Per-symbol analysis
  - Phase F: Output metrics in standard format
- [ ] Preserve RestrictedPython sandbox for strategy execution
- [ ] Preserve AST security checks (shift(-N), forbidden builtins)
- [ ] Verify: `python -c "from src.core.backtester import *; print('IMPORT OK')"`

### Step 7 -- Update active_strategy.py example (STRAT-07)
- [ ] Write a working dual-method strategy example:
  - `select_universe()`: top 30 by 20-day average volume
  - `generate_signals()`: simple 20-bar momentum on minute data
- [ ] Verify: strategy loads and methods are callable
- [ ] Verify: `find_strategy_methods()` returns `(class, True)`

### Step 8 -- Write strategy interface tests (STRAT-01..04 tests)
- [ ] Create `tests/unit/test_strategy_interface.py`
- [ ] Test `find_strategy_methods()` with both methods present
- [ ] Test `find_strategy_methods()` with only `generate_signals`
- [ ] Test `find_strategy_methods()` with no valid strategy class
- [ ] Test `select_universe()` returns list of strings
- [ ] Test `generate_signals()` returns dict of Series with values in {-1, 0, 1}
- [ ] Test signal lag enforcement in minute mode
- [ ] Run: `pytest tests/unit/test_strategy_interface.py -v`

### Step 9 -- Commit sprint 2 changes
- [ ] `git add src/core/backtester.py src/strategies/active_strategy.py tests/unit/test_strategy_interface.py`
- [ ] `git commit -m "feat(backtest): add select_universe strategy interface and minute-level walk-forward"`

## 4) Test Plan

- [x] After Step 1: `from src.strategies.active_strategy import *` works
- [x] After Step 3: `find_strategy_methods()` correctly detects both methods
- [ ] After Step 5: walk-forward windows have correct trading-day boundaries
- [ ] After Step 6: backtester pipeline runs end-to-end (manual test with small date range)
- [ ] After Step 8: all strategy interface tests pass
- [ ] Verify: `pytest --tb=short -q` all tests pass

## 5) Verification Commands

```bash
# Strategy interface
python -c "
from src.strategies.active_strategy import *
print('Strategy import OK')
"

# Backtester import
python -c "
from src.core.backtester import *
print('Backtester import OK')
"

# Walk-forward windows (manual check)
python -c "
from src.data.duckdb_connector import get_trading_days, calculate_walk_forward_windows
# Requires DuckDB cache built in Sprint 1
windows = calculate_walk_forward_windows('2024-01-01', '2024-12-31', n_windows=5)
for i, w in enumerate(windows):
    print(f'Window {i}: train={w[\"train_start\"]}..{w[\"train_end\"]} test={w[\"test_start\"]}..{w[\"test_end\"]}')
"

# Tests
pytest tests/unit/test_strategy_interface.py -v
pytest --tb=short -q
```

## 6) Implementation Update Space

### Completed Work

- Added `select_universe()` to `TradingStrategy` with a safe default that ranks the top 30 ticker
  symbols by average daily volume across the provided daily-data frame.
- Documented the DuckDB daily-data contract directly in `active_strategy.py` without changing the
  existing `generate_signals()` path yet.
- Extended `tests/unit/test_strategy_interface.py` to cover the new `select_universe` interface and
  its ranked ticker output.
- Re-verified `query_minute_data()` from Sprint 1 against both the unit suite and the live
  `minute-aggs bars` runtime path, so Sprint 2 can depend on the bridge without adding new code.
- Updated `find_strategy_class()` in `src/core/backtester.py` to return
  `(strategy_class, has_universe)` and detect `select_universe` without changing the broader
  backtester flow yet.
- Synced the `walk_forward_validation()` strategy-loading call site to unpack the new tuple contract.
- Extended both `tests/unit/test_strategy_interface.py` and `tests/unit/test_backtester_v2.py` to
  cover the three required Step 3 cases: both methods present, `generate_signals` only, and no valid
  strategy class.

### Command Results

- `uv run pytest tests/unit/test_strategy_interface.py -v` -> 19 passed
- `uv run python -c "from src.strategies.active_strategy import *; print('IMPORT OK')"` -> `IMPORT OK`
- `uv run pytest tests/unit/test_duckdb_connector.py -v` -> 6 passed
- `uv run python -c "from src.data.duckdb_connector import query_minute_data; result = query_minute_data(['AAPL'], '2025-11-03', '2025-11-07'); frame = result.get('AAPL'); print('tickers=', sorted(result.keys())); print('rows=', 0 if frame is None else len(frame)); print('columns=', [] if frame is None else list(frame.columns)); print('first_session=', None if frame is None or frame.empty else frame['session_date'].min()); print('last_session=', None if frame is None or frame.empty else frame['session_date'].max()); print('first_close=', None if frame is None or frame.empty else frame.iloc[0]['close'])"` -> `tickers=['AAPL']`, `rows=3612`, schema `['ticker', 'session_date', 'window_start_ns', 'open', 'high', 'low', 'close', 'volume', 'transactions']`, date range `2025-11-03` to `2025-11-07`
- `PYTHONPATH=src uv run python -c "from core.backtester import find_strategy_class; print('IMPORT OK', find_strategy_class({}))"` -> `IMPORT OK (None, False)`
- `PYTHONPATH=src uv run pytest tests/unit/test_strategy_interface.py tests/unit/test_backtester_v2.py -q` -> `44 passed in 0.31s`

### Blockers / Deviations

- Kept the Step 1 default universe rule tied to average daily volume across the provided frame.
- `query_minute_data()` was already implemented in Sprint 1, so Step 2 closed as a verification gate
  rather than a new code-change step.
- Deferred the more opinionated `20-day average volume` example to Step 7, where the sprint plan
  explicitly calls for the dual-method example strategy.

### Follow-ups

- Next execution target: Step 4 in this sprint doc (`generate_signals()` minute-data contract)
