# V2 Backtest CLI Step 2 Design

**Date:** 2026-04-04
**Issue:** #11
**Sprint Step:** `docs/feature/v2-data-pipeline/sprint3/sprint3-backend.md` Step 2
**Branch:** `feature/v2-data-pipeline`

## Goal

Replace the legacy `cli.py backtest` command surface with the V2 minute-mode interface so the CLI matches the DuckDB daily-cache + minute-query pipeline already implemented in Sprint 2.

## Current Problem

`cli.py backtest` still uses the old cache-driven flow:

- imports `load_data()` from `src/core/backtester.py`
- filters a preloaded symbol cache through `--symbols`
- calls `walk_forward_validation()` only after monkey-patching `load_data()`

That behavior conflicts with the current V2 runtime contract, where `walk_forward_validation()` already:

- loads daily data from DuckDB via `load_daily_data()`
- selects a universe through `select_universe(daily_data)` or a fallback rule
- queries minute bars per window via `query_minute_data()`
- prints the standard metrics block including `PER_SYMBOL`

## Approved Direction

Use a direct V2 command surface and remove the legacy `--symbols` runtime path.

### Command interface

Keep:

- `--strategy`

Add:

- `--start`
- `--end`
- `--universe-size`

Remove from the normal path:

- `--symbols`
- the CLI-side `load_data()` check and monkey-patching flow

## Responsibilities

### `cli.py`

`cli.py backtest` should only:

- validate CLI arguments
- validate the strategy path
- run the AST security check
- pass runtime settings to the backtester through per-invocation configuration
- invoke `walk_forward_validation()`
- own command-syntax failures such as missing files, one-sided date flags, and invalid `--universe-size`

### `src/core/backtester.py`

The backtester remains the runtime owner for:

- resolving `STRATEGY_FILE` and `BACKTEST_*` overrides at call time rather than import time
- date-range selection
- universe-size enforcement
- loading DuckDB daily data
- minute-bar querying
- metrics output
- runtime/data validation messages produced during `walk_forward_validation()`

This keeps Step 2 scoped to the CLI-to-runtime boundary instead of mixing in Step 3 or Step 4 work.

## Runtime contract

The CLI will set runtime configuration before calling `walk_forward_validation()`:

- `STRATEGY_FILE`
- `BACKTEST_START_DATE` when `--start` is provided
- `BACKTEST_END_DATE` when `--end` is provided
- `BACKTEST_UNIVERSE_SIZE` when `--universe-size` is provided

The backtester will read these settings at invocation time and:

- validate paired date overrides
- limit the daily-data range when a range is supplied
- cap the selected universe after normalization

## Error handling

The command should fail with explicit messages for:

- missing strategy file
- failed security check
- one-sided date overrides
- invalid universe size
- missing DuckDB daily data inside the requested range
- runtime/data failures surfaced by `walk_forward_validation()`

Ownership split:

- CLI owns flag-shape validation and import failures.
- Backtester owns runtime/data validation after execution starts.

## Test strategy

Use TDD and keep Step 2 focused on unit coverage:

1. Add CLI tests for the new `backtest` flags and environment handoff.
2. Add a regression test proving `--strategy` and other overrides are honored even when the backtester module has already been imported.
3. Add failing tests for invalid date/universe-size inputs.
4. Add focused backtester tests for environment-driven date-range and universe-size behavior if the CLI cannot cover those paths alone.
5. Run the new targeted tests before and after implementation.

## Non-goals

- No `update_data` command work yet.
- No integration-test file creation yet.
- No docs refresh in `program.md` or `CLAUDE.md` yet.
- No attempt to preserve the old cache-symbol workflow.

## Success criteria

- `cli.py backtest` exposes the V2 minute-mode options.
- The command no longer depends on `load_data()` or CLI-side symbol filtering.
- `walk_forward_validation()` resolves runtime overrides at call time instead of relying on import-time snapshots.
- `walk_forward_validation()` respects optional CLI date and universe-size limits.
- Targeted unit tests fail first, then pass.
