# CLAUDE.md

This file provides repository guidance for Claude Code and similar coding agents.

## Project Overview

Quant Autoresearch is an autonomous quantitative strategy discovery framework. The current V2 data
pipeline is local-first: DuckDB stores a daily-bar cache, while minute bars are queried on demand
from the local `massive-minute-aggs` dataset through the `minute-aggs` CLI.

## Commands

### Install And Test

```bash
uv sync
uv sync --all-extras --dev

pytest
pytest tests/unit/
pytest tests/integration/test_minute_backtest.py -v
pytest tests/security/
pytest tests/regression/
```

### V2 CLI Runtime

```bash
# Build the DuckDB daily cache
uv run python cli.py setup-data

# Refresh the cache incrementally
uv run python cli.py update-data

# Query minute bars
uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05

# Run the minute-mode walk-forward backtest
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py backtest --strategy src/strategies/active_strategy.py --universe-size 20
```

Live Typer command names are hyphenated: `setup-data` and `update-data`.

## Architecture

### 6-Phase OPENDEV Loop

The research engine still follows the existing 6-phase OPENDEV loop:

1. Context management
2. Thinking
3. Action selection
4. Doom-loop detection
5. Execution
6. Observation

That engine is separate from the Sprint 3 CLI/data-pipeline work in this branch.

### V2 Data Architecture

The current backtesting path is:

1. Load daily bars from DuckDB via `src/data/duckdb_connector.py`
2. Run `select_universe(daily_data)` on the full daily frame
3. Build 5 walk-forward windows on trading-day boundaries
4. Query minute bars per window through the `minute-aggs` CLI
5. Run `generate_signals(minute_data)` in the RestrictedPython sandbox
6. Apply the enforced 1-bar lag and compute portfolio/per-symbol metrics

## Key Components

- `src/core/engine.py` - autonomous research loop orchestrator
- `src/core/backtester.py` - minute-mode walk-forward validation, sandbox loading, metrics output
- `src/core/research.py` - literature and web research helpers
- `src/data/duckdb_connector.py` - DuckDB cache build/load helpers, trading-day lookup, minute-query bridge, incremental refresh
- `src/strategies/active_strategy.py` - example dual-method strategy surface
- `src/memory/playbook.py` - SQLite-based episodic memory
- `src/models/router.py` - multi-provider model routing
- `program.md` - current repo/runtime constitution for the V2 data pipeline

## Critical Patterns

- Strategy contract:
  - `select_universe(daily_data)` is optional and receives the full daily-bar frame.
  - `generate_signals(minute_data)` receives `dict[str, pd.DataFrame]` and returns `dict[str, pd.Series]`.
- Walk-forward runtime:
  - daily-first universe selection
  - minute queries scoped to selected tickers and test windows
  - 5 trading-day-aware windows
  - enforced 1-bar lag in the backtester, not in the strategy
- Security:
  - RestrictedPython sandbox
  - AST gate blocks forbidden builtins/imports and look-ahead patterns such as `.shift(-1)`
- CLI surface:
  - operator-facing commands are `setup-data`, `update-data`, `fetch`, and `backtest`
  - legacy `run`, `status`, and `report` flows are not part of the V2 CLI contract

## Environment Variables

Common runtime variables:

- `MINUTE_AGGS_CLI` - path to the `minute-aggs` executable
- `MINUTE_AGGS_DATASET_ROOT` - root of the local minute parquet dataset
- `STRATEGY_FILE` - backtest strategy override
- `BACKTEST_START_DATE` / `BACKTEST_END_DATE` - optional backtest date bounds
- `BACKTEST_UNIVERSE_SIZE` - optional ticker cap

Model and telemetry keys from the broader project still apply where those subsystems are in use.

## Data And Cache

- Daily cache path: `data/daily_cache.duckdb`
- Minute dataset root defaults to the local iCloud path configured in `src/data/duckdb_connector.py`
- Cache builds and refreshes use temp CSV exports in `/tmp`
- `update-data` is append-oriented and ignores duplicate primary keys on `(ticker, session_date)`

## CI

GitHub Actions still run the standard Python/uv/pytest pipeline. For this feature branch, the
important merge gate is that the DuckDB/minute-pipeline tests and CLI smoke flows stay green.
