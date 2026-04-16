> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Data Pipeline -- Infra Lane Plan

> Feature branch: `feature/v2-data-pipeline`
> Role: Infra / Runtime
> Historical workspace: `docs/feature/v2-data-pipeline/`
> Last updated: 2026-04-04

## Mission

Lock the external runtime assumptions that make the backend plan executable: dataset location, CLI
binary behavior, DuckDB output path, temp-file handling, and the smoke commands needed to prove the
system works outside unit tests.

## Environment Contracts

| Item | Current Value | Why It Matters |
| --- | --- | --- |
| Dataset root | `~/Library/Mobile Documents/com~apple~CloudDocs/massive data/us_stocks_sip/minute_aggs_parquet_v1` | Primary local dataset path referenced during the historical planning pass |
| CLI binary | `/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs` | Required for minute-bar reads and batched SQL aggregation |
| DuckDB output | `data/daily_cache.duckdb` | Stable local cache path for daily bars |
| Temp workspace | `/tmp/` CSV outputs during cache build and minute queries | Needed for batched CLI exports without loading the full dataset in memory |
| Dependency tool | `uv` | Standard env sync and command runner for the repo |

## Infra Tasks

| Task ID | Task | Dependency | Acceptance |
| --- | --- | --- | --- |
| INFRA-01 | Validate dataset root, CLI binary, DuckDB output path, and temp-file budget before coding starts | Phase 0 complete | commands confirm all paths exist and are writable/readable as expected |
| INFRA-02 | Define cache-build batching, timeout, and progress-reporting expectations | INFRA-01 | Sprint 1 has explicit operational behavior for long-running cache builds |
| INFRA-03 | Define refresh semantics for `update-data` to avoid duplicate rows or full rebuilds by default | Sprint 2 complete | Sprint 3 CLI design includes clear append or rebuild rules |
| INFRA-04 | Capture smoke evidence for `setup-data`, `fetch`, `backtest`, and `update-data` | Phase 4 | issue or PR links prove the runtime path works beyond unit tests |

## Operational Checks

```bash
# Validate CLI visibility
/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs stats
/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs schema

# Validate repo environment
uv sync --all-extras --dev

# Validate DuckDB artifact path after Sprint 1
uv run python cli.py setup-data
test -f data/daily_cache.duckdb

# Validate CLI runtime after Sprint 3
uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py update-data
```

## Runtime Notes

- Cache build time is expected to be long enough that progress output is required.
- The feature should prefer batched month-level aggregation over one monolithic query.
- Temp CSV cleanup is part of the runtime contract, not an optional polish item.
- Any path drift from the values above must be reflected in this doc and in the implementation
  before the sprint can be called complete.

## Infra Risks

| Risk | Mitigation |
| --- | --- |
| Dataset path or binary path drifts on the local machine | Validate paths in INFRA-01 and update docs before writing the consuming code |
| Temp CSV workflow leaves partial files or fills disk | Batch by month, clean up after each import, and add visible progress or failure reporting |
| Incremental refresh duplicates rows in DuckDB | Make primary-key semantics explicit and test `update-data` before closeout |
