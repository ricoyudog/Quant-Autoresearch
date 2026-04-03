# CLAUDE.md

This file gives coding-agent guidance for working in this repository.

## Project Overview

Quant Autoresearch is a V2 strategy-research workflow centered on:

- `program.md` as the experiment instruction contract
- `src/strategies/active_strategy.py` as the strategy under iteration
- `src/core/backtester.py` as the fixed evaluation harness
- `src/data/connector.py` as the market-data ingestion and cache interface
- `cli.py` as the supported command entrypoint

Treat the repository as execution-first. Run experiments through the backtester,
keep the strategy compatible with the sandbox, and keep docs aligned with the
current CLI and output surfaces.

## Supported Commands

### Setup and Data

```bash
uv sync
uv sync --all-extras --dev
uv run python cli.py --help
uv run python cli.py setup-data
uv run python cli.py fetch SPY --start 2020-01-01
```

### Backtesting

```bash
uv run python cli.py backtest
uv run python cli.py backtest --strategy src/strategies/active_strategy.py
uv run python src/core/backtester.py > run.log 2>&1
```

### Testing

```bash
uv run pytest
uv run pytest --tb=short -q
uv run pytest tests/unit/test_cli.py -v
uv run pytest tests/unit/test_backtester_v2.py -v
uv run pytest tests/unit/test_strategy_interface.py -v
uv run pytest tests/security/test_adversarial.py -v
```

The current suite also includes coverage for data, playbook memory, research,
retry logic, telemetry, tracker metrics, determinism, and integration flows
under `tests/`.

## Current Architecture Surfaces

### `program.md`

Defines the operating contract for autonomous experimentation, including:

- setup sequence
- keep/discard rules
- output schema expectations
- notes workflow under `experiments/notes/`

When code and `program.md` disagree, align changes to the current repository
behavior and keep the contract internally consistent.

### `src/core/backtester.py`

Backtester responsibilities:

- load cached data
- run strategy code with RestrictedPython protections
- enforce AST checks, including look-ahead bias blocking
- perform walk-forward validation
- print the score and risk metrics used by decision rules

Treat this file as the evaluation truth surface.

### `src/strategies/active_strategy.py`

Strategy requirements:

- define at least one class with `generate_signals(self, data)`
- return signals compatible with backtester expectations
- keep logic vectorized with pandas and numpy
- avoid look-ahead behavior such as negative shifts

The full file is editable in V2 as long as sandbox and interface constraints
hold.

### `src/data/connector.py`

Data responsibilities:

- fetch equity and crypto data
- enrich data with required features such as `returns`, `volatility`, and `atr`
- cache datasets under `data/cache/`
- load cached datasets for backtesting

Prefer connector interfaces over ad-hoc data-path logic.

### `cli.py`

Supported commands are:

- `setup-data`
- `fetch`
- `backtest`

Keep docs and examples aligned with this surface.

### `src/core/research.py`

This module is still present for research helpers and optional web-backed
context gathering. It is not the primary runtime loop and should not be
documented as if it replaces the backtester-driven V2 workflow.

## Environment Variables

Use `.env` for runtime configuration. Common active variables include:

- `WANDB_API_KEY`, `WANDB_PROJECT`, `WANDB_ENTITY` for telemetry
- `EXA_API_KEY` or `SERPAPI_KEY` for research-related integrations
- `CACHE_DIR` to override cache location used by the backtester
- `STRATEGY_FILE` to override the strategy path for backtest runs

Only document variables that are actively used by current code paths.

## Engineering Guidelines

- Python target: 3.12+
- Keep lines under 120 chars and use 4-space indentation
- Import order: stdlib, third-party, local
- Add type hints and concise docstrings where meaningful
- Keep strategy and backtester interfaces stable
- Prefer small, auditable changes with explicit verification commands

## Data and Output Hygiene

- `data/cache/` holds cached market-data artifacts
- `results.tsv` and `run.log` are local experiment outputs and should not be
  committed
- `experiments/notes/` holds markdown experiment notes and is intended to
  remain tracked

## CI

CI runs dependency install and tests via `uv` and `pytest`. Keep command
examples and verification steps CI-compatible.
