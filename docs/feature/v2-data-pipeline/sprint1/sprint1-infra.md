> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

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
path, and the first smoke evidence for `setup-data`.

## 2) Scope / Out Of Scope

**Scope**
- Validate the `massive-minute-aggs` dataset path and CLI binary
- Confirm the intended DuckDB output path and temp-file workflow
- Define batching, timeout, cleanup, and progress-reporting expectations for cache build
- Run or prepare the first `setup-data` smoke checks once the backend step lands

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
- [x] Confirm `data/daily_cache.duckdb` is the intended cache artifact path
- [x] Confirm `/tmp/` is acceptable for month-batch CSV exports during cache build
- [x] Define cleanup expectations so temp CSVs do not accumulate between batches
- [x] Define timeout and progress-reporting expectations for long-running monthly aggregation

### Step 3 -- Prepare and run the Sprint 1 smoke gate
- [x] Confirm `uv run python cli.py setup-data --help` exposes the intended cache-build command
- [x] After backend implementation lands, run `uv run python cli.py setup-data`
- [ ] Confirm `data/daily_cache.duckdb` exists after the run
- [x] Confirm `data/daily_cache.duckdb` exists after the run
- [x] Inspect row count, distinct tickers, and date range in DuckDB and record the result

### Step 4 -- Feed evidence back into the workspace
- [x] Record command outcomes in the update area below
- [x] Record any runtime blockers or deviations for Sprint 1 follow-up
- [x] Link relevant evidence back to the umbrella issue or PR summary

## 4) Test Plan

- [x] `minute-aggs stats` runs successfully
- [x] `minute-aggs schema` matches the expected minute-bar columns
- [x] `uv run python cli.py setup-data --help` works before the cache build smoke run
- [x] `uv run python cli.py setup-data` creates `data/daily_cache.duckdb`
- [x] DuckDB inspection confirms a plausible row count, ticker count, and session-date range

## 5) Verification Commands

```bash
/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs stats
/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs schema

uv run python cli.py setup-data --help
uv run python cli.py setup-data

python -c "
import duckdb
con = duckdb.connect('data/daily_cache.duckdb', read_only=True)
r = con.execute('SELECT COUNT(*), COUNT(DISTINCT ticker), MIN(session_date), MAX(session_date) FROM daily_bars').fetchone()
print(f'Rows: {r[0]}, Tickers: {r[1]}, Range: {r[2]} to {r[3]}')
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
- Confirmed the intended cache artifact path remains `data/daily_cache.duckdb` across the spec,
  feature infra plan, and Sprint 1 backend plan.
- Verified the repo-local `data/` parent path is writable and that `/tmp/` is writable and usable
  for create/delete cycles.
- Defined operational expectations for Sprint 1 cache build:
  - delete each month-batch CSV immediately after DuckDB ingest
  - use a 300-second timeout per CLI batch
  - emit visible per-month progress output during cache build
- Added `*.duckdb` to `.gitignore` so the planned cache artifact does not pollute git status.
- Confirmed the canonical Typer command name is `setup-data` and aligned the Sprint 1 infra
  verification docs to use the hyphenated runtime form.
- Ran the Sprint 1 smoke gate with `uv run python cli.py setup-data --help` and
  `uv run python cli.py setup-data`.
- Verified the cache artifact exists at `data/daily_cache.duckdb` and recorded the DuckDB row
  count, ticker count, and session-date range after the build completed.
- Re-ran the targeted Sprint 1 verification commands:
  - `uv run pytest tests/unit/test_duckdb_connector.py -v`
  - `uv run pytest tests/unit/test_cli.py -v`
  - runtime-module stale-import scan under `src/`
- Linked the merge-ready smoke evidence back to issue #11:
  `https://github.com/ricoyudog/Quant-Autoresearch/issues/11#issuecomment-4186599914`

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
- Artifact path references:
  - `docs/data-pipeline-v2.md` uses `data/daily_cache.duckdb` in build and read examples
  - `docs/feature/v2-data-pipeline/v2-data-pipeline-infra.md` defines `data/daily_cache.duckdb`
    as the stable DuckDB output path
  - `docs/feature/v2-data-pipeline/sprint1/sprint1-backend.md` uses
    `data/daily_cache.duckdb` as the default `output_path`
- Parent-path and temp-path checks:
  - `DATA_DIR_WRITABLE`
  - `ARTIFACT_PARENT_WRITE_OK`
  - `DATA_DIR_CLEANED`
  - `TMP_WRITABLE`
  - `CREATED:/tmp/quant-autoresearch-step2.hl5bbH`
  - `TMP_CLEANED`
  - `/tmp` free space: `67Gi` available at verification time
- Repo hygiene:
  - before the fix: `DUCKDB_NOT_IGNORED`
  - after the fix, `.gitignore` now includes `*.duckdb`
- Sprint 1 smoke gate:
  - `uv run python cli.py setup-data --help` -> success; help shows `--force`
  - `uv run python cli.py setup-data` -> success; processed month batches from `2021-03`
    through `2026-04` and finished with `Daily cache ready at data/daily_cache.duckdb`
  - `ls -lh data/daily_cache.duckdb` -> `342M`
  - DuckDB inspection -> `Rows: 13273623, Tickers: 19928, Range: 2021-03-30 to 2026-03-30`
  - `uv run pytest tests/unit/test_duckdb_connector.py -v` -> `6 passed in 0.06s`
  - `uv run pytest tests/unit/test_cli.py -v` -> `16 passed in 0.37s`
  - runtime-module stale-import scan -> `CLEAN`

### Blockers / Deviations

- No blocking path or permission drift found.
- `minute-aggs schema` currently exposes two extra logical columns, `schema_version` and
  `source_file`, beyond the nine fields documented in the sprint/spec. These are non-blocking for
  Step 1 but should remain ignored unless downstream cache logic explicitly needs them.
- The planned cache artifact path was not originally ignored by git because `.gitignore` covered
  `*.db` but not `*.duckdb`; this was fixed during Step 2.
- The original Sprint 1 infra and QA docs used `setup_data`, but the Typer runtime exposes the
  command as `setup-data`; the directly affected docs were normalized during Step 4 evidence
  closeout instead of widening the CLI surface with a second alias.
- The broad stale-import grep from the test plan can match `__pycache__` artifacts or literal test
  strings, so the recorded closeout evidence uses a runtime-module scan limited to Python files
  under `src/`.

### Follow-Ups

- Sprint 1 infra is complete; hand off the verified cache path, `/tmp` behavior, 300-second timeout
  target, and progress requirements to Sprint 2 backend work.
- Reuse the issue evidence comment above when Sprint 3 / Phase 4 closeout needs the Sprint 1 smoke
  provenance.
