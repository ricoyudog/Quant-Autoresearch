# V2 Backtest CLI Step 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy `cli.py backtest` flow with the V2 minute-mode CLI interface for Sprint 3 backend Step 2.

**Architecture:** Keep `cli.py` as a thin command adapter and move runtime selection to `src/core/backtester.py` through environment-driven configuration. The CLI validates arguments and invokes the backtester; the backtester owns date scoping, universe-size limiting, and final metric output.

**Tech Stack:** Python 3.12, Typer, pytest, pandas, DuckDB-backed data access, RestrictedPython

---

### Task 1: Lock the CLI contract with failing tests

**Files:**
- Modify: `tests/unit/test_cli.py`
- Modify: `cli.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:
- `backtest --help` shows `--start`, `--end`, and `--universe-size`
- `backtest` sets `STRATEGY_FILE`, `BACKTEST_START_DATE`, `BACKTEST_END_DATE`, and `BACKTEST_UNIVERSE_SIZE`
- `backtest` honors `--strategy` even when `core.backtester` has already been imported
- one-sided date overrides fail with a stable message
- non-positive `--universe-size` fails with a stable message

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_cli.py -k backtest -v`
Expected: FAIL because the current command does not expose or honor the V2 options yet.

- [ ] **Step 3: Write minimal implementation**

Update `cli.py backtest` to:
- accept `--start`, `--end`, and `--universe-size`
- reject one-sided date overrides
- reject `--universe-size <= 0`
- stop importing or using `load_data()`
- set runtime environment variables before calling `walk_forward_validation()`

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_cli.py -k backtest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_cli.py cli.py
git commit -m "feat(cli): switch backtest to v2 minute-mode interface"
```

### Task 2: Lock backtester config behavior with failing tests

**Files:**
- Modify: `tests/unit/test_backtester_v2.py`
- Modify: `src/core/backtester.py`

- [ ] **Step 1: Write the failing tests**

Add focused tests that assert:
- `walk_forward_validation()` limits daily data by `BACKTEST_START_DATE` and `BACKTEST_END_DATE`
- `walk_forward_validation()` caps the selected ticker list to `BACKTEST_UNIVERSE_SIZE`
- invalid env combinations fail deterministically

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_backtester_v2.py -k "env or universe" -v`
Expected: FAIL because the runtime does not yet read the new environment configuration.

- [ ] **Step 3: Write minimal implementation**

Update `src/core/backtester.py` to:
- read `STRATEGY_FILE` at invocation time
- read optional date-range env vars
- read optional universe-size env var
- validate paired dates and integer limits
- pass date filters into `load_daily_data(start_date=..., end_date=...)`
- cap `selected_tickers` after normalization

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_backtester_v2.py -k "env or universe" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_backtester_v2.py src/core/backtester.py
git commit -m "feat(backtester): honor cli backtest range and universe config"
```

### Task 3: Run the Step 2 verification slice and sync docs

**Files:**
- Modify: `docs/feature/v2-data-pipeline/sprint3/sprint3-backend.md`
- Modify: `docs/feature/v2-data-pipeline/README.md`
- Modify: `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md`

- [ ] **Step 1: Run targeted verification**

Run:
- `uv run pytest tests/unit/test_cli.py -k backtest -v`
- `uv run pytest tests/unit/test_backtester_v2.py -v`
- `uv run python cli.py backtest --help`

Expected:
- targeted tests pass
- help output shows the new options

- [ ] **Step 2: Run a command-level smoke**

Run: `uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31`
Expected: standard metrics output including `SCORE`, `SORTINO`, and `PER_SYMBOL`, or a stable runtime error if the local dataset window is unavailable.

- [ ] **Step 3: Update sprint documentation**

Update the Sprint 3 backend doc to:
- mark Step 2 complete
- record verification commands and outputs
- set the next execution target to Step 3

- [ ] **Step 4: Sync workspace status**

Update:
- `docs/feature/v2-data-pipeline/README.md`
- `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md`

Record that Sprint 3 backend Step 2 is complete and Step 3 is next.

- [ ] **Step 5: Commit**

```bash
git add docs/feature/v2-data-pipeline/sprint3/sprint3-backend.md docs/feature/v2-data-pipeline/README.md docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md
git commit -m "docs: close out sprint 3 backtest cli step"
```
