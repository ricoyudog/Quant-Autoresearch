# V2 Data Pipeline -- Test Plan

> Feature branch: `feature/v2-data-pipeline`
> Umbrella issue: #11

## Objective

Verify that the new DuckDB-based data pipeline works correctly: daily cache creation, minute-level CLI queries, dual-method strategy interface, minute-level walk-forward backtesting, and CLI commands.

## Pre-Work Baseline

Before starting, confirm the codebase is green from Phase 1:

```bash
uv sync --all-extras --dev
pytest --tb=short
```

Record the test count and result as baseline.

## Test Coverage Matrix

### New Test Files

| Test File | Module Under Test | Key Tests |
| --- | --- | --- |
| `tests/unit/test_duckdb_connector.py` | `data/duckdb_connector.py` | build_daily_cache, load_daily_data, get_trading_days, date filtering |
| `tests/unit/test_strategy_interface.py` | strategy interface | select_universe detection, generate_signals minute mode, dynamic class loading |
| `tests/integration/test_minute_backtest.py` | full pipeline | end-to-end minute backtest, walk-forward windows, CLI subprocess |

### Existing Tests to Update

| Test File | Change |
| --- | --- |
| `tests/conftest.py` | Add DuckDB fixtures (test DB, sample daily data), update data fixtures |
| `tests/unit/test_data.py` | Update or remove tests for old connector.py (if still exists) |

### Existing Tests to Keep (No Changes)

| Test File | Module Under Test |
| --- | --- |
| `tests/unit/test_security.py` | backtester sandbox security |
| `tests/unit/test_playbook_memory.py` | memory/playbook.py |
| `tests/unit/test_research.py` | core/research.py |
| `tests/unit/test_retry_logic.py` | utils/retries.py |
| `tests/unit/test_runner.py` | runner |
| `tests/unit/test_telemetry_wandb.py` | utils/telemetry.py |
| `tests/unit/test_tracker_metrics.py` | utils/iteration_tracker.py |
| `tests/regression/test_determinism.py` | determinism |

### Tests to Remove (Replaced Modules)

| Test File | Reason |
| --- | --- |
| `tests/unit/test_data.py` (if tests old connector) | connector.py removed |

## Test Details

### tests/unit/test_duckdb_connector.py

```python
# Test cases:

def test_build_daily_cache_creates_file():
    """build_daily_cache() creates data/daily_cache.duckdb with daily_bars table"""

def test_build_daily_cache_schema():
    """daily_bars table has correct columns: ticker, session_date, open, high, low, close, volume, transactions, vwap"""

def test_build_daily_cache_primary_key():
    """daily_bars has PRIMARY KEY (ticker, session_date)"""

def test_load_daily_data_returns_dataframe():
    """load_daily_data() returns a pd.DataFrame"""

def test_load_daily_data_date_filter():
    """load_daily_data(start, end) filters by date range"""

def test_load_daily_data_all_tickers():
    """load_daily_data() without filters returns all 11K+ tickers"""

def test_get_trading_days_ordered():
    """get_trading_days() returns chronologically ordered list"""

def test_get_trading_days_date_range():
    """get_trading_days(start, end) respects date boundaries"""

def test_query_minute_data_returns_dict():
    """query_minute_data() returns dict[str, pd.DataFrame]"""

def test_query_minute_data_per_ticker():
    """query_minute_data() correctly splits results by ticker"""

def test_query_minute_data_timeout():
    """query_minute_data() handles CLI timeout gracefully"""
```

### tests/unit/test_strategy_interface.py

```python
# Test cases:

def test_strategy_with_select_universe():
    """find_strategy_methods() detects select_universe and returns has_universe=True"""

def test_strategy_without_select_universe():
    """find_strategy_methods() returns has_universe=False when no select_universe"""

def test_generate_signals_minute_mode():
    """generate_signals() accepts dict[str, DataFrame] and returns dict[str, Series]"""

def test_generate_signals_signal_values():
    """Signals are in {-1, 0, 1}"""

def test_select_universe_returns_list():
    """select_universe() returns list[str] of ticker symbols"""

def test_no_generate_signals_rejected():
    """Strategy without generate_signals is rejected by find_strategy_methods"""

def test_sandbox_restrictions_minute():
    """Minute strategy still runs in RestrictedPython sandbox with only pd/np"""
```

### tests/integration/test_minute_backtest.py

```python
# Test cases:

def test_full_minute_backtest_pipeline():
    """End-to-end: load daily -> select universe -> query minute -> signals -> metrics"""

def test_walk_forward_windows():
    """5 walk-forward windows have correct trading-day boundaries"""

def test_per_ticker_window_query():
    """Each window queries minute data only for selected tickers"""

def test_signal_lag_enforcement():
    """Signals are shift(1) enforced even in minute mode"""

def test_backtest_output_format():
    """Output includes SCORE, SORTINO, CALMAR, DRAWDOWN, P_VALUE, BASELINE_SHARPE, PER_SYMBOL"""
```

## Verification Steps

### Step 1: After Sprint 1 (DuckDB + Daily Cache)

```bash
# Unit tests for duckdb_connector
pytest tests/unit/test_duckdb_connector.py -v

# Manual verification
uv run python cli.py setup_data
python -c "
import duckdb
con = duckdb.connect('data/daily_cache.duckdb', read_only=True)
r = con.execute('SELECT COUNT(*), COUNT(DISTINCT ticker), MIN(session_date), MAX(session_date) FROM daily_bars').fetchone()
print(f'Rows: {r[0]}, Tickers: {r[1]}, Range: {r[2]} to {r[3]}')
con.close()
"
```

### Step 2: After Sprint 2 (Strategy + Backtester)

```bash
# Unit tests for strategy interface
pytest tests/unit/test_strategy_interface.py -v

# Verify strategy loading
python -c "
from src.strategies.active_strategy import *
# Check for select_universe and generate_signals
print('Strategy interface OK')
"

# Verify backtester imports
python -c "
from src.core.backtester import *
print('Backtester imports OK')
"
```

### Step 3: After Sprint 3 (CLI + Integration Tests)

```bash
# Full test suite
pytest --tb=short -v

# CLI commands
uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05
uv run python cli.py backtest
```

### Step 4: Global Import Cleanliness

```bash
# No references to removed modules
grep -rn "from src.data.connector\|from src.data.preprocessor\|DataConnector\|Preprocessor" src/ tests/ cli.py || echo "CLEAN"
```

### Step 5: Full Regression

```bash
pytest --tb=short
```

All tests must pass.

## Acceptance Criteria

- [ ] `tests/unit/test_duckdb_connector.py` passes (10+ test cases)
- [ ] `tests/unit/test_strategy_interface.py` passes (7+ test cases)
- [ ] `tests/integration/test_minute_backtest.py` passes (5+ test cases)
- [ ] `tests/conftest.py` has DuckDB and minute data fixtures
- [ ] Old connector/preprocessor tests removed or updated
- [ ] No test file imports from removed `connector.py` or `preprocessor.py`
- [ ] `pytest` passes with 0 failures
- [ ] `uv run python cli.py setup_data` works end-to-end
- [ ] `uv run python cli.py backtest` works end-to-end
