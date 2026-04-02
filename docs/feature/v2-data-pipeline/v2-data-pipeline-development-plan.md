# V2 Data Pipeline -- Development Plan

> Feature branch: `feature/v2-data-pipeline`
> Umbrella issue: #11
> Canonical root: `docs/feature/v2-data-pipeline/`

## Context

The V2 data pipeline replaces the yfinance/CCXT-based data connector with a local-first architecture built on the massive-minute-aggs dataset (US Stocks SIP, 11K+ tickers, minute-level bars, ~5 years). The design uses DuckDB for a pre-computed daily aggregation cache and CLI subprocess calls for per-window minute-level queries during walk-forward backtesting.

The strategy interface gains a new `select_universe(daily_data)` method that allows the strategy to screen 11K+ tickers using daily data before the backtester loads minute-level bars for the selected subset. This two-phase approach balances universe breadth with query performance.

## Source Data

### massive-minute-aggs Dataset

```
Dataset Root: ~/Library/Mobile Documents/com~apple~CloudDocs/massive data/us_stocks_sip/minute_aggs_parquet_v1
CLI Binary:   /Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs
File Count:   1,256 Parquet files
Date Range:   2021-03-30 ~ 2026-03-30 (~5 years)
Tickers:      ~11,274 US stocks
Granularity:  1-minute bars (OHLCV + transactions)
```

### Schema

| Column | Type | Description |
| --- | --- | --- |
| `ticker` | string | Stock symbol |
| `session_date` | date | Trading date |
| `window_start_ns` | int64 | Nanosecond timestamp |
| `open` | float64 | Open price |
| `high` | float64 | High price |
| `low` | float64 | Low price |
| `close` | float64 | Close price |
| `volume` | float64 | Volume |
| `transactions` | int | Transaction count |

## Files to Create

### New modules

| File | Purpose | Est. LOC |
| --- | --- | --- |
| `src/data/duckdb_connector.py` | DuckDB daily cache: create, query, update | ~200 |

### Files to Modify

| File | Changes | Est. Effort |
| --- | --- | --- |
| `src/core/backtester.py` | Add DuckDB daily loading, CLI minute queries, dual-method strategy interface, minute-level walk-forward | Large |
| `src/strategies/active_strategy.py` | Add `select_universe(daily_data)` method, update `generate_signals` for minute data | Medium |
| `cli.py` | Add/rewrite `setup_data` for DuckDB cache build, add `update_data` for incremental, update `fetch` for minute queries, add `backtest` command | Medium |
| `pyproject.toml` | Add `duckdb` dependency | Small |
| `program.md` | Add dataset docs, CLI reference, dual-method strategy interface | Medium |

### Files to Remove

| File | Reason |
| --- | --- |
| `src/data/connector.py` | Replaced by `duckdb_connector.py` |
| `src/data/preprocessor.py` | Replaced by `setup_data` cache build |

## Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 1 -- DuckDB + Daily Cache | Add DuckDB, build daily aggregation cache | `duckdb_connector.py`, updated `setup_data`, working daily queries | pending | start strategy interface |
| Sprint 2 -- Strategy + Backtester | Dual-method strategy, minute-level walk-forward | updated `backtester.py`, updated `active_strategy.py`, per-ticker window queries | pending | start CLI |
| Sprint 3 -- CLI + Tests | CLI commands, integration tests, documentation | updated `cli.py`, new test files, updated docs | pending | merge readiness |

## Task Table

### Sprint 1 Tasks (DuckDB + Daily Cache)

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| DUCK-01 | Create `feature/v2-data-pipeline` branch | Dev | Phase 1 merged | 0.1d | branch exists, tests green |
| DUCK-02 | Add `duckdb` to pyproject.toml | Dev | DUCK-01 | 0.05d | `uv sync` succeeds |
| DUCK-03 | Create `src/data/duckdb_connector.py` with `build_daily_cache()` | Dev | DUCK-02 | 0.5d | DuckDB file created with daily_bars table |
| DUCK-04 | Create `load_daily_data()` query function | Dev | DUCK-03 | 0.2d | Returns filtered DataFrame from DuckDB |
| DUCK-05 | Create `get_trading_days()` utility function | Dev | DUCK-04 | 0.1d | Returns ordered list of trading dates |
| DUCK-06 | Update `cli.py setup_data` to call `build_daily_cache()` | Dev | DUCK-03 | 0.2d | `uv run python cli.py setup_data` creates DuckDB file |
| DUCK-07 | Test daily cache: verify schema, row counts, date range | Dev | DUCK-06 | 0.2d | Unit tests pass |

### Sprint 2 Tasks (Strategy + Backtester)

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| STRAT-01 | Add `select_universe(daily_data)` to strategy interface | Dev | Sprint 1 complete | 0.2d | Method defined in active_strategy.py |
| STRAT-02 | Create `query_minute_data()` CLI subprocess function | Dev | Sprint 1 complete | 0.3d | Returns dict[str, DataFrame] for tickers |
| STRAT-03 | Update `find_strategy_methods()` to detect `select_universe` | Dev | STRAT-01 | 0.1d | Returns (class, has_universe) tuple |
| STRAT-04 | Update `generate_signals` signature for minute data | Dev | STRAT-01 | 0.2d | Accepts dict[str, DataFrame], returns dict[str, Series] |
| STRAT-05 | Implement minute-level walk-forward window calculation | Dev | STRAT-02, DUCK-05 | 0.3d | 5 windows with trading-day boundaries |
| STRAT-06 | Integrate DuckDB + CLI queries into backtester loop | Dev | STRAT-02..05 | 0.5d | Full pipeline: daily -> universe -> minute -> signals -> metrics |
| STRAT-07 | Update `active_strategy.py` with minimal example strategy | Dev | STRAT-01, STRAT-04 | 0.2d | Working dual-method strategy |

### Sprint 3 Tasks (CLI + Tests)

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| CLI-01 | Update `cli.py fetch` for minute-level queries | Dev | Sprint 2 complete | 0.2d | `uv run python cli.py fetch AAPL --start 2025-01-01` works |
| CLI-02 | Update `cli.py backtest` to support minute mode | Dev | Sprint 2 complete | 0.3d | Runs full minute-level backtest |
| CLI-03 | Add `cli.py update_data` for incremental DuckDB refresh | Dev | Sprint 2 complete | 0.3d | Appends new daily bars without rebuild |
| TEST-01 | Write `tests/unit/test_duckdb_connector.py` | Dev | DUCK-07 | 0.3d | Tests for build_daily_cache, load_daily_data, get_trading_days |
| TEST-02 | Write `tests/unit/test_strategy_interface.py` | Dev | STRAT-03 | 0.2d | Tests for select_universe, generate_signals, dynamic loading |
| TEST-03 | Write `tests/integration/test_minute_backtest.py` | Dev | CLI-02 | 0.5d | End-to-end minute-level backtest pipeline |
| TEST-04 | Update `tests/conftest.py` with DuckDB fixtures | Dev | TEST-01 | 0.1d | Fixtures for test DuckDB, sample daily data |
| DOC-01 | Update `program.md` with dataset docs and CLI reference | Dev | CLI-01..03 | 0.2d | Complete data pipeline docs in program.md |
| DOC-02 | Update `CLAUDE.md` to reflect V2 data pipeline | Dev | DOC-01 | 0.1d | Architecture section updated |

## Acceptance Criteria

- [ ] `feature/v2-data-pipeline` branch exists
- [ ] `duckdb` added to pyproject.toml, `uv sync` succeeds
- [ ] `src/data/duckdb_connector.py` created with `build_daily_cache()`, `load_daily_data()`, `get_trading_days()`
- [ ] `uv run python cli.py setup_data` creates `data/daily_cache.duckdb` with correct schema
- [ ] `src/data/connector.py` and `src/data/preprocessor.py` removed
- [ ] Strategy interface has `select_universe(daily_data)` (optional) and `generate_signals(minute_data)` methods
- [ ] Backtester supports minute-level walk-forward with CLI subprocess queries
- [ ] `uv run python cli.py fetch <symbol> --start <date>` returns minute data
- [ ] `uv run python cli.py backtest` runs full minute-level backtest
- [ ] All new unit tests pass
- [ ] Integration test for full pipeline passes
- [ ] No surviving file imports from old `connector.py` or `preprocessor.py`
- [ ] `pytest` passes with 0 failures

## Verification Commands

```bash
# Verify DuckDB cache
uv run python cli.py setup_data
python -c "
import duckdb
con = duckdb.connect('data/daily_cache.duckdb', read_only=True)
print(con.execute('SELECT COUNT(*) FROM daily_bars').fetchone())
print(con.execute('SELECT MIN(session_date), MAX(session_date) FROM daily_bars').fetchone())
con.close()
"

# Verify old files removed
test ! -f src/data/connector.py && echo "connector.py GONE"
test ! -f src/data/preprocessor.py && echo "preprocessor.py GONE"

# Verify no broken imports
grep -rn "from src.data.connector\|from src.data.preprocessor" src/ tests/ cli.py || echo "CLEAN"

# Verify dependencies
uv sync && echo "DEPS OK"
pytest --tb=short && echo "TESTS OK"
```

## Performance Budget

```
Daily cache build:     ~30-60 min (11K tickers x 5 years, CLI queries by month)
Daily cache size:      ~100MB (DuckDB, compressed)
Per-window query:      5-15 sec (30 tickers x 60 days x 390 bars)
Full backtest:         ~2-3 min (5 windows + strategy computation)
```

## Risks

| Risk | Mitigation |
| --- | --- |
| DuckDB cache build is slow (11K tickers) | Batch by month, show progress, resumable |
| CLI subprocess timeout on large queries | Set 300s timeout, batch tickers |
| Old connector.py still imported somewhere | Global grep as verification gate |
| Minute data volume overwhelms memory | Per-ticker queries, streaming CSV parse |
| `openai` dep already removed in v2-cleanup | Verify pyproject.toml is clean from Phase 1 |
