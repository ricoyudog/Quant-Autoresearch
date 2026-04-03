# Sprint 1 -- Infra Plan

> Feature: `v2-data-pipeline`
> Role: Infra / Runtime
> Scope: dataset path validation, CLI binary checks, and DuckDB cache prerequisites
> Last Updated: 2026-04-04

## 0) Governing Specs

1. `docs/data-pipeline-v2.md` -- Section 1 (data source) and Section 3 (daily cache / DuckDB)
2. `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md` -- Sprint 1 tasks
3. `docs/feature/v2-data-pipeline/v2-data-pipeline-infra.md` -- feature-level runtime contract
4. `docs/feature/v2-data-pipeline/v2-data-pipeline-test-plan.md` -- verification gates and evidence expectations

## 1) Sprint Mission

Confirm that the local runtime environment is ready for the DuckDB cache build before backend coding
depends on it. This sprint owns the dataset path, CLI binary, temp-file strategy, DuckDB artifact
path, and the first smoke evidence for `setup_data`.

## 2) Scope / Out Of Scope

**Scope**
- Validate the `massive-minute-aggs` dataset path and CLI binary
- Confirm the intended DuckDB output path and temp-file workflow
- Define batching, timeout, cleanup, and progress-reporting expectations for cache build
- Run or prepare the first `setup_data` smoke checks once the backend step lands

**Out of Scope**
- Implementing DuckDB helpers in Python
- Strategy interface or backtester changes
- CLI surface changes beyond Sprint 1 cache-build prerequisites

## 3) Step-By-Step Plan

### Step 1 -- Validate dataset and CLI assumptions
- [x] Confirm the dataset root exists and is readable
- [x] Run `minute-aggs stats` and confirm the CLI can see the dataset
- [x] Run `minute-aggs schema` and confirm the minute-bar schema matches the spec
- [x] Record any path or schema drift before backend implementation starts

### Step 2 -- Validate artifact and temp-file behavior
- [ ] Confirm `data/daily_cache.duckdb` is the intended cache artifact path
- [ ] Confirm `/tmp/` is acceptable for month-batch CSV exports during cache build
- [ ] Define cleanup expectations so temp CSVs do not accumulate between batches
- [ ] Define timeout and progress-reporting expectations for long-running monthly aggregation

### Step 3 -- Prepare and run the Sprint 1 smoke gate
- [ ] Confirm `uv run python cli.py setup_data --help` exposes the intended cache-build command
- [ ] After backend implementation lands, run `uv run python cli.py setup_data`
- [ ] Confirm `data/daily_cache.duckdb` exists after the run
- [ ] Inspect row count and date range in DuckDB and record the result

### Step 4 -- Feed evidence back into the workspace
- [ ] Record command outcomes in the update area below
- [ ] Record any runtime blockers or deviations for Sprint 1 follow-up
- [ ] Link relevant evidence back to the umbrella issue or PR summary

## 4) Test Plan

- [x] `minute-aggs stats` runs successfully
- [x] `minute-aggs schema` matches the expected minute-bar columns
- [ ] `uv run python cli.py setup_data --help` works before the cache build smoke run
- [ ] `uv run python cli.py setup_data` creates `data/daily_cache.duckdb`
- [ ] DuckDB inspection confirms a plausible row count and session-date range

## 5) Verification Commands

```bash
/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs stats
/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs schema

uv run python cli.py setup_data --help
uv run python cli.py setup_data

python -c "
import duckdb
con = duckdb.connect('data/daily_cache.duckdb', read_only=True)
print(con.execute('SELECT COUNT(*) FROM daily_bars').fetchone())
print(con.execute('SELECT MIN(session_date), MAX(session_date) FROM daily_bars').fetchone())
con.close()
"
```

## 6) Implementation Update Space

### Completed Work

- Verified the local `massive-minute-aggs` dataset root exists and is readable.
- Ran `minute-aggs stats` successfully and confirmed the CLI sees the expected dataset path,
  file count, and date range.
- Ran `minute-aggs schema` successfully and confirmed the sprint-required logical columns are
  present.
- Compared the CLI schema output against `docs/data-pipeline-v2.md` Section 1.2 and recorded the
  non-blocking drift below.

### Command Results

- Dataset path check:
  - `DATASET_DIR_EXISTS`
  - `DATASET_DIR_READABLE`
- `minute-aggs stats` returned:
  - `dataset_root=/Users/chunsingyu/Library/Mobile Documents/com~apple~CloudDocs/massive data/us_stocks_sip/minute_aggs_parquet_v1`
  - `file_count=1256`
  - `first_session_date=2021-03-30`
  - `last_session_date=2026-03-30`
- `minute-aggs schema` returned the expected core logical columns:
  - `ticker`
  - `session_date`
  - `window_start_ns`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
  - `transactions`

### Blockers / Deviations

- No blocking path or permission drift found.
- `minute-aggs schema` currently exposes two extra logical columns, `schema_version` and
  `source_file`, beyond the nine fields documented in the sprint/spec. These are non-blocking for
  Step 1 but should remain ignored unless downstream cache logic explicitly needs them.

### Follow-Ups

- Proceed to Step 2 in this infra doc: validate the DuckDB artifact path and temp-file behavior.
- Hand off the confirmed dataset path and the non-blocking schema extras to Sprint 1 backend work.
