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
- `src/data/connector.py` for data ingestion and cache loading
- `src/strategies/active_strategy.py` for the strategy under iteration

## Core Workflow

1. Prepare cached market data with `setup-data` or `fetch`.
2. Modify `src/strategies/active_strategy.py`.
3. Run `backtest` or call `src/core/backtester.py` directly.
4. Record outcomes in `results.tsv` and `experiments/notes/`.
5. Iterate based on the metrics reported by the backtester.

## Project Structure

```text
├── cli.py
├── program.md
├── src/
│   ├── core/
│   │   ├── backtester.py
│   │   └── research.py
│   ├── data/
│   │   ├── connector.py
│   │   └── preprocessor.py
│   ├── memory/
│   │   └── playbook.py
│   ├── strategies/
│   │   └── active_strategy.py
│   └── utils/
├── data/cache/
├── experiments/notes/
└── tests/
```

Notes:

- `src/core/research.py` is available for academic and web-backed research
  helpers.
- `src/memory/playbook.py` remains available as an optional SQLite-backed memory
  tool.
- The primary validation path is the backtester.

## Quick Start

### 1. Install Dependencies

Requires Python 3.12+ and `uv`.

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

Advanced runtime overrides such as `CACHE_DIR` and `STRATEGY_FILE` are also
supported by current code paths.

### 3. Prepare Data

Download the default dataset:

```bash
uv run python cli.py setup-data
```

Or fetch a specific symbol:

```bash
uv run python cli.py fetch SPY --start 2020-01-01
```

### 4. Run a Backtest

```bash
uv run python cli.py backtest
```

Use a custom strategy path or symbol subset when needed:

```bash
uv run python cli.py backtest --strategy src/strategies/active_strategy.py
uv run python cli.py backtest --symbols SPY,QQQ
```

### 5. Run Tests

```bash
uv run pytest --tb=short -q
uv run pytest tests/unit/test_cli.py -v
uv run pytest tests/unit/test_backtester_v2.py -v
uv run pytest tests/unit/test_strategy_interface.py -v
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
- `src/memory/playbook.py` stores reusable strategy patterns in SQLite.
- `src/utils/telemetry.py` supports optional W&B telemetry.

These modules support the workflow, but they do not replace the
`program.md` + strategy-file + backtester loop.

## License

MIT License. This project is for research use only. Do not deploy generated
strategies to live capital without independent review and validation.
