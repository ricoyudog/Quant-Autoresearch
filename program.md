# Quant Autoresearch Program

Autonomous quantitative strategy discovery on the V2 local-first data pipeline with overfit-defense validation.

## Data Pipeline V2

The project uses the local `massive-minute-aggs` US equities dataset as the primary source.
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

# Run overfit-defense validation
uv run python cli.py validate --method cpcv
uv run python cli.py validate --method regime
uv run python cli.py validate --method stability
```

Notes:

- `fetch` requires both `--start` and `--end`, or neither.
- `backtest` accepts `--strategy`, `--start`, `--end`, and `--universe-size`.
- `validate` accepts `--method cpcv|regime|stability` plus method-specific flags.
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
- For validation helpers, `generate_signals(pd.DataFrame)` compatibility is still supported.

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
SCORE: 0.4521
NAIVE_SHARPE: 0.6832
NW_SHARPE_BIAS: 0.2311
DEFLATED_SR: 0.9200
SORTINO: 0.8100
CALMAR: 1.2300
DRAWDOWN: -0.1200
MAX_DD_DAYS: 45
TRADES: 120
WIN_RATE: 0.5500
PROFIT_FACTOR: 1.8500
AVG_WIN: 0.0120
AVG_LOSS: -0.0080
BASELINE_SHARPE: 0.4500
---
PER_SYMBOL:
  AAA: sharpe=0.62 sortino=0.90 dd=-0.10 pf=2.10 trades=35 wr=0.57
```

## Decision Rules

**KEEP if:**

- `SCORE > previous best`
- `SCORE > BASELINE_SHARPE`

**DISCARD if:**

- `SCORE <= previous best`
- `SCORE <= BASELINE_SHARPE`

**Advisories:**

- If `DEFLATED_SR < 0.5`, treat the result as not robust yet and run deeper validation before trusting it.
- If `NW_SHARPE_BIAS > 0.3`, serial correlation is materially inflating the naive estimate.

## Overfit Defense Guidance

- `SCORE` is the Newey-West adjusted Sharpe Ratio, not the naive Sharpe.
- `NAIVE_SHARPE` is retained only as a comparison point.
- `NW_SHARPE_BIAS = NAIVE_SHARPE - SCORE`; larger values indicate more serial-correlation inflation.
- Use `validate --method cpcv` after material score improvements, major parameter changes, or before merge.
- Use `validate --method regime` to check whether profit concentration is regime-dependent.
- Use `validate --method stability` to detect narrow parameter optima before trusting a change.

Red flags:

- `NW_SHARPE_BIAS > 0.3`
- `DEFLATED_SR < 0.5`
- CPCV percent-positive below `0.5`
- stability score below `0.5`

## Operational Notes

- The daily cache build is month-batched and can take significant time on the full dataset.
- `update-data` is append-oriented by default and skips duplicate `(ticker, session_date)` rows.
- Minute queries are window-scoped to keep memory use bounded.
- The security gate still blocks dangerous imports, forbidden builtins, and look-ahead patterns such as `.shift(-1)`.

## Experiment Logging

Log experiment outcomes to `experiments/results.tsv` with the header:

```text
commit	score	naive_sharpe	deflated_sr	sortino	calmar	drawdown	max_dd_days	trades	win_rate	profit_factor	avg_win	avg_loss	baseline_sharpe	nw_bias	status	description
```

## Research Capabilities

Use the vault-native research CLI when you need external context before changing a strategy.

- `uv run python cli.py setup_vault` prepares `quant-autoresearch/{experiments,research,knowledge}/` inside the configured Obsidian vault.
- `uv run python cli.py research "<query>" --depth shallow --output stdout|vault` searches ArXiv first and can reuse or write vault-native research notes.
- `uv run python cli.py analyze <ticker> --start <date> --output stdout|vault` builds a deterministic stock-analysis report from cached local market data.
- `research --depth shallow` stays usable without `EXA_API_KEY` or `SERPAPI_KEY`; deep mode should clearly report when web search is skipped.
- `analyze` reads daily bars from `data/daily_cache.duckdb` when available and can also use legacy `data/cache` symbol files; run `uv run python cli.py setup-data` before analyzing on a fresh machine.

## Memory Access Patterns

Use the four memory layers consistently during research and experimentation:

1. **Session context** — current Codex conversation, active branch state, and the immediate task.
2. **Working memory** — recent experiment notes, `run.log`, and in-flight observations from the current research loop.
3. **Persistent vault knowledge** — `quant-autoresearch/research/`, `quant-autoresearch/knowledge/`, and existing Obsidian strategy notes that can inform new hypotheses. Experiment notes live in a separate continuation lane and should only be loaded when the run is explicitly continuing a branch.
4. **Long-term score tracking** — `results.tsv`, which remains the cross-session ledger of the best validated outcomes.

When using the research surface:
- read vault idea notes before self-searching for new ideas
- self-search only after vault notes are checked, and only when recent research notes are missing or stale, or every 10 completed experiments to refresh idea flow
- read existing strategy and knowledge notes before inventing a new hypothesis
- reuse existing shallow research notes when appropriate, but allow deep runs to refresh them
- write new experiment notes after each validated run
- keep `results.tsv` aligned with any experiment that beats the baseline and passes the statistical gates

Strategy knowledge loop rules:
- Follow `.omx/specs/strategy-knowledge-loop-artifact-contract.md` as the canonical contract for experiment memory.
- Treat `quant-autoresearch/experiments/` as raw evidence, not disposable output.
- Preserve failed experiments, rejected hypotheses, and fee / turnover lessons as first-class knowledge.
- The canonical automation source for continuation is `experiments/continuation/current_research_base.json`.
- Derived summaries such as `experiment-index.md` and kickoff notes may be auto-refreshed, but they must link back to raw notes and never replace them.
- A single improved backtest is follow-up evidence, not proof, and it must not automatically stop exploration of other branches.
- Generic intake stays anchored to `research/` + `knowledge/`; experiment memory is only loaded through an explicit continuation mode.

Before proposing strategy changes:
- consume a minimum structured context bundle before proposing strategy changes
- require one vault idea note with a stable path, source, title, and metadata seed such as `query`, `topic`, or `tickers`
- require the latest deterministic `analyze` report or equivalent local market-context note
- require the current strategy baseline from `program.md`, `src/strategies/active_strategy.py`, and recent `results.tsv` entries
- if any element is missing, keep researching or summarizing the gap; do not propose strategy changes until that bundle exists
