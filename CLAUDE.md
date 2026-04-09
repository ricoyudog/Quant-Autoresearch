# CLAUDE.md

This file provides repository guidance for Claude Code and similar coding agents.

## Project Overview

Quant Autoresearch is a V2 strategy-research repository. The current workflow is driven by
`program.md` plus the supported `cli.py` commands. Agents iterate on strategy and research work
while validating through the fixed backtesting and analysis surfaces.

## Supported Commands

### Environment and tests

```bash
uv sync
uv sync --all-extras --dev
uv run pytest -q
```

### Data and research surfaces

```bash
# Build / refresh the DuckDB daily cache used by the minute-data pipeline
uv run python cli.py setup-data
uv run python cli.py update-data

# Query minute bars for a bounded window
uv run python cli.py fetch SPY --start 2025-01-01 --end 2025-03-31

# Prepare the vault-native research workspace
uv run python cli.py setup_vault

# Produce research / analysis notes
uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output vault
uv run python cli.py analyze SPY --start 2025-01-01 --end 2025-03-31 --output vault

# Run the minute-mode backtest surface
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
```

Notes:
- Live Typer command names are hyphenated (`setup-data`, `update-data`).
- `analyze` can read from `data/daily_cache.duckdb`; legacy `data/cache` symbol files are optional.
- `research --depth shallow` must stay usable without `EXA_API_KEY` / `SERPAPI_KEY`.

## Architecture

### Primary truth surfaces

- `program.md` — agent operating contract
- `cli.py` — supported operator/runtime commands
- `src/core/backtester.py` — evaluation and sandbox rules
- `src/data/duckdb_connector.py` — DuckDB daily-cache build/load + minute-data queries
- `src/core/research.py` — vault-native research helpers
- `src/analysis/` — deterministic stock-analysis report helpers
- `src/strategies/active_strategy.py` — strategy file under iteration

### Runtime model

1. Build or refresh the DuckDB daily cache with `setup-data` / `update-data`.
2. Query minute data on demand with `fetch`.
3. Use `setup_vault`, `research`, and `analyze` for the vault-native research workflow.
4. Validate strategies with the minute-mode backtester.

There is no active Python-side legacy orchestration loop in the current `main_dev` closeout target.
Historical docs may still discuss older runtime phases, but current operator guidance should follow
`program.md` and the CLI/runtime surfaces above.

## Environment Variables

Common runtime variables:

- `OBSIDIAN_VAULT_PATH` — override the vault root used by `setup_vault`, `research`, and `analyze`
- `EXA_API_KEY` / `SERPAPI_KEY` — optional deep-research web search providers
- `MINUTE_AGGS_CLI` — path to the `minute-aggs` executable
- `MINUTE_AGGS_DATASET_ROOT` — root of the local minute parquet dataset
- `STRATEGY_FILE` — optional strategy override for backtests
- `BACKTEST_START_DATE` / `BACKTEST_END_DATE` / `BACKTEST_UNIVERSE_SIZE` — optional backtest runtime bounds

## Verification Expectations

When changing product behavior or closeout surfaces, collect fresh evidence with the relevant mix of:

- `uv run pytest -q`
- `uv run python cli.py --help`
- `uv run python cli.py setup_vault`
- `uv run python cli.py setup-data`
- `uv run python cli.py research ...`
- `uv run python cli.py analyze ...`
- `uv run python cli.py backtest ...`

Do not claim completion from historical comments alone when fresh current-session verification is required.
