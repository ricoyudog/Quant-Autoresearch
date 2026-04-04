# Quant Autoresearch Program

Autonomous quantitative strategy discovery on the V2 local-first data pipeline.

## Data Pipeline V2

The project now uses the local `massive-minute-aggs` US equities dataset as the primary data source.
Daily bars are materialized into DuckDB at `data/daily_cache.duckdb`, and minute bars are queried on
demand through the external `minute-aggs` CLI.

Key runtime surfaces:

- Dataset root: `~/Library/Mobile Documents/com~apple~CloudDocs/massive data/us_stocks_sip/minute_aggs_parquet_v1`
- Minute query CLI: `/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs`
- Daily cache: `data/daily_cache.duckdb`

If the daily cache is missing, build it first:

```bash
uv run python cli.py setup-data
```

Refresh it later without rebuilding from scratch:

```bash
uv run python cli.py update-data
```

## CLI Reference

```bash
# Build the DuckDB daily cache
uv run python cli.py setup-data

# Incrementally refresh the cache
uv run python cli.py update-data

# Query minute bars for one symbol
uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05

# Run a minute-mode walk-forward backtest
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py backtest --strategy src/strategies/active_strategy.py --universe-size 20
```

Notes:

- `fetch` requires both `--start` and `--end`, or neither.
- `backtest` accepts `--strategy`, `--start`, `--end`, and `--universe-size`.
- `setup-data` and `update-data` are the live Typer command names; underscored spellings are not valid CLI commands.

## Strategy Interface

The V2 backtester uses a dual-method contract.

```python
class TradingStrategy:
    def select_universe(self, daily_data: pd.DataFrame) -> list[str]:
        ...

    def generate_signals(self, minute_data: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
        ...
```

Contract details:

- `select_universe(daily_data)` is optional and receives the full DuckDB `daily_bars` frame.
- `generate_signals(minute_data)` receives a dictionary keyed by ticker.
- Each signal series must align to the source minute-frame index for that ticker.
- The backtester applies the enforced 1-bar lag. Strategies should emit raw signals and not self-lag.

The default example strategy in `src/strategies/active_strategy.py` currently:

- ranks the top 30 tickers by latest 20-session average volume
- computes a simple 20-bar momentum signal per ticker
- returns minute-mode signals as `dict[str, pd.Series]`

## Backtest Data Flow

The minute-mode walk-forward runtime is:

1. Phase A: load daily bars from `data/daily_cache.duckdb`
2. Phase B: run `select_universe(daily_data)` or fall back to the safe ranked universe
3. Phase C: query minute bars for the selected tickers and current test window through `minute-aggs`
4. Phase D: run `generate_signals(minute_data)`
5. Phase E: apply the enforced 1-bar lag and evaluate walk-forward metrics

The backtester builds 5 trading-day-aware walk-forward windows from the cached daily sessions.

## Output Format

Minute-mode backtests print the standard metrics block plus `PER_SYMBOL`:

```text
---
SCORE: 0.5432
SORTINO: 0.8100
CALMAR: 1.2300
DRAWDOWN: -0.1200
MAX_DD_DAYS: 45
TRADES: 120
P_VALUE: 0.0000
WIN_RATE: 0.5500
PROFIT_FACTOR: 1.8500
AVG_WIN: 0.0120
AVG_LOSS: -0.0080
BASELINE_SHARPE: 0.4500
---
PER_SYMBOL:
  AAA: sharpe=0.62 sortino=0.90 dd=-0.10 pf=2.10 trades=35 wr=0.57
```

## Operational Notes

- The daily cache build is month-batched and can take significant time on the full dataset.
- `update-data` is append-oriented by default and skips duplicate `(ticker, session_date)` rows.
- Minute queries are window-scoped to keep memory use bounded.
- The security gate still blocks dangerous imports, forbidden builtins, and look-ahead patterns such as `.shift(-1)`.
