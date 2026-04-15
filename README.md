# Quant Autoresearch: V2 Strategy Research Workflow

<img width="2752" height="1536" alt="Quant Autoresearch Header" src="https://github.com/user-attachments/assets/5e84b668-c81f-4c41-bd0a-f4db95846b0d" />

Quant Autoresearch is a repository for iterative quantitative-strategy
research. In the current V2 architecture, an external coding agent follows
`program.md`, edits `src/strategies/active_strategy.py`, and validates changes
through the fixed backtesting harness in `src/core/backtester.py`.

The active truth surfaces are:

- `program.md` for the experiment contract
- `cli.py` for supported commands
- `src/core/backtester.py` for evaluation and sandbox rules
- `src/data/duckdb_connector.py` for DuckDB daily-cache and minute-data access
- `src/core/research.py` and `src/analysis/` for the vault-native research surface
- `src/strategies/active_strategy.py` for the strategy under iteration
- `scripts/autoresearch_runner.py` for the current dry-run iteration-artifact runner

## Core Workflow

1. Build the DuckDB daily cache with `setup-data`; use `fetch` only when you need a bounded minute-bar inspection slice.
2. Modify `src/strategies/active_strategy.py`.
3. Run `backtest` or call `src/core/backtester.py` directly.
4. Record outcomes in `results.tsv` and `experiments/notes/`.
5. Iterate based on the metrics reported by the backtester.

## Claude Code Autoresearch Runner

The current 003 branch exposes a **dry-run audit-bundle** surface for the
outer-loop runner. It does not yet ship the full live multi-round execution
loop, but it can already materialize one auditable iteration bundle while
keeping the evaluator as the future acceptance authority.

```bash
uv run python scripts/autoresearch_runner.py \
  --iterations 1 \
  --dry-run \
  --claude-wrapper scripts/run_claude_iteration.sh
```

Current grounded behavior:

- `--dry-run` writes a machine-first artifact bundle under `experiments/iterations/<run_id>/iteration-0001/`.
- The bundle includes `context.json`, `context.md`, `decision.json`, `iteration_record.json`, and `experiment_note_draft.md`.
- `experiment_note_draft.md` is a **derived draft**, not a finalized raw experiment note.
- Full live multi-round execution and richer resume semantics remain follow-up work.

## Project Structure

```text
├── cli.py
├── program.md
├── src/
│   ├── core/
│   │   ├── backtester.py
│   │   └── research.py
│   ├── analysis/
│   ├── data/
│   │   ├── cache_connector.py
│   │   └── duckdb_connector.py
│   ├── memory/
│   │   └── __init__.py
│   ├── strategies/
│   │   └── active_strategy.py
│   └── utils/
├── data/cache/
├── experiments/notes/
└── tests/
```

Notes:

- `src/core/research.py` and `src/analysis/` provide the current vault-native
  research and deterministic analysis surfaces.
- `setup_vault`, `research`, and `analyze` are first-class CLI commands on the
  current V2 surface.
- The primary validation path is still the backtester.

## Quick Start

### 1. Install Dependencies

Requires Python 3.10+ and `uv`.

```bash
git clone https://github.com/ricoyudog/Quant-Autoresearch.git
cd Quant-Autoresearch
uv sync
```

For the full development environment:

```bash
uv sync --all-extras --dev
```

### 2. Optional Configuration

Create a `.env` file only for integrations you actually use:

```env
WANDB_API_KEY=your_key_here
WANDB_PROJECT=quant-autoresearch
WANDB_ENTITY=your_entity
EXA_API_KEY=your_key_here
# or
SERPAPI_KEY=your_key_here
```

For direct `src/core/backtester.py` runs, `CACHE_DIR` can override the cache
location and `STRATEGY_FILE` can override the strategy path. The CLI surfaces
continue to use their explicit options and default cache path.

### 3. Prepare Data And Vault

Build the DuckDB daily cache used by the V2 pipeline:

```bash
uv run python cli.py setup-data
```

Prepare a vault root for research notes (override `OBSIDIAN_VAULT_PATH` when needed):

```bash
uv run python cli.py setup_vault
```

Query bounded minute bars when you need an inspection slice:

```bash
uv run python cli.py fetch SPY --start 2025-01-01 --end 2025-03-31
```

### 4. Run Research / Analysis

```bash
uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output vault
uv run python cli.py analyze SPY --start 2025-01-01 --end 2025-03-31 --output vault
```

### 5. Run a Backtest

```bash
uv run python cli.py backtest
```

Use a custom strategy path or a different universe size when needed:

```bash
uv run python cli.py backtest --strategy src/strategies/active_strategy.py
uv run python cli.py backtest --universe-size 20
```

### 6. Run Tests

```bash
uv run pytest --tb=short -q
uv run pytest tests/unit/test_cli.py -v
uv run pytest tests/unit/test_backtester_v2.py -v
uv run pytest tests/unit/test_strategy_interface.py -v
uv run pytest tests/unit/test_autoresearch_runner.py tests/integration/test_autoresearch_runner_artifacts.py -v
```

## Evaluation and Safety

The backtester is the evaluation truth surface. Current safeguards include:

- walk-forward validation
- forced signal lag
- volatility-aware trading-cost modeling
- RestrictedPython sandboxing
- AST-based look-ahead checks

If a strategy cannot pass the backtester, it should not be treated as a valid
result regardless of how plausible the logic looks.

## Supporting Modules

- `src/core/research.py` can gather academic and web research context.
- `src/analysis/` renders deterministic stock-analysis reports from cached data.
- `config/vault.py` and the vault helpers support the Obsidian-native research workspace.
- `src/utils/telemetry.py` supports optional W&B telemetry.

These modules support the workflow, but they do not replace the
`program.md` + CLI + backtester loop.

## License

MIT License. This project is for research use only. Do not deploy generated
strategies to live capital without independent review and validation.
