# V2 Data Pipeline -- Development Plan

> Feature branch: `feature/v2-data-pipeline`
> Umbrella issue: #11
> Canonical root: `docs/feature/v2-data-pipeline/`
> Last updated: 2026-04-05
> Planning status: Sprint 3 execution, verification, and post-review correction completed; issue #11 is ready for review

## 1. Context

The V2 data pipeline replaces the yfinance/CCXT-era data flow with a local-first architecture built
on the `massive-minute-aggs` dataset (US Stocks SIP, 11K+ tickers, minute bars, about 5 years). The
design uses DuckDB for a pre-computed daily cache and CLI subprocess calls for per-window minute
queries during walk-forward backtesting.

The strategy contract expands to a two-step flow:

1. `select_universe(daily_data)` screens the full daily universe
2. `generate_signals(minute_data)` emits minute-level signals for the selected tickers

This keeps the searchable universe broad while limiting the minute-bar load to the tickers the
strategy actually wants to trade.

## 2. Root And Branch Decision

- Active docs root: `docs/`
- Canonical workspace: `docs/feature/v2-data-pipeline/`
- Canonical branch: `feature/v2-data-pipeline`

Repo drift note: the generic skill reference expects `docs/beta/` and `docs/dev/` planning roots,
but the current repository snapshot does not have those trees. Planning granularity therefore
follows the live V2 workspace precedents under `docs/feature/` plus the governing specs in
`docs/data-pipeline-v2.md` and `docs/upgrade-plan-v2.md`.

`docs/feature/v2-data-pipeline/` is the right root instead of `docs/issue/11/` because this work is
a persistent feature-scoped V2 session, not a one-off issue-local hotfix. The branch name keeps the
repo's existing V2 naming convention instead of introducing an issue-number-only variant.

## 3. Scope

- Integrate DuckDB as the daily-cache layer for the local minute-bar dataset
- Add a strategy-driven universe-selection step before minute-bar loading
- Update the backtester to run minute-level walk-forward evaluation on trading-day windows
- Update CLI workflows for setup, fetch, backtest, and incremental cache refresh
- Add the test coverage and documentation needed to make the new runtime model reviewable

## 4. Out Of Scope

- Phase 1 / issue #8 backtester foundation work
- Session 3 overfit-defense design and implementation
- Session 4 research-capability expansion
- Performance tuning beyond what is needed to make the first version reliable and measurable

## 5. Lane Ownership

| Lane | Responsibility | Primary Docs | Runtime Surface |
| --- | --- | --- | --- |
| Planning | Keep the umbrella issue and feature workspace aligned | this plan, README | issue #11, docs workspace |
| Backend | Deliver DuckDB connector, strategy contract, backtester, and CLI changes | `v2-data-pipeline-backend.md`, sprint docs | `src/data/`, `src/core/`, `src/strategies/`, `cli.py` |
| Infra | Validate dataset paths, CLI binary behavior, DuckDB storage, temp-file handling, and smoke commands | `v2-data-pipeline-infra.md` | local dataset, `minute-aggs`, DuckDB file, temp CSVs |
| QA | Define baseline, unit, integration, and merge gates | `v2-data-pipeline-test-plan.md` | `tests/`, CLI smoke runs, final issue evidence |

## 6. Delivery Surface

### Files To Create

| File | Lane | Purpose |
| --- | --- | --- |
| `src/data/duckdb_connector.py` | Backend | Daily-cache build/load helpers plus minute-query bridge |
| `tests/unit/test_duckdb_connector.py` | QA | Unit coverage for DuckDB cache creation and query helpers |
| `tests/integration/test_minute_backtest.py` | QA | End-to-end regression for the daily-to-minute pipeline |

### Files To Modify

| File | Lane | Change |
| --- | --- | --- |
| `src/core/backtester.py` | Backend | Daily-cache loading, universe selection, trading-day windows, minute-level walk-forward |
| `src/strategies/active_strategy.py` | Backend | `select_universe(daily_data)` and minute-data `generate_signals()` example |
| `cli.py` | Backend | `setup-data`, `fetch`, `backtest`, and `update-data` runtime changes |
| `pyproject.toml` | Backend | Add `duckdb` dependency |
| `program.md` | Planning | Update runtime docs to the DuckDB/minute-data model |
| `CLAUDE.md` | Planning | Update repo architecture notes after Sprint 3 lands |
| `tests/conftest.py` | QA | Add DuckDB/minute fixtures |
| `tests/unit/test_strategy_interface.py` | QA | Expand to the dual-method strategy contract |
| `tests/unit/test_data.py` | QA | Remove or refactor legacy connector-only expectations |

### Files To Remove

| File | Lane | Reason |
| --- | --- | --- |
| `src/data/connector.py` | Backend | Replaced by `duckdb_connector.py` and the new cache/query flow |
| `src/data/preprocessor.py` | Backend | Replaced by `setup-data` DuckDB cache build logic |

## 7. Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Phase 0 -- Spec Alignment + Baseline | Confirm docs root, branch convention, dependency gate, and umbrella references | rewritten issue card, updated workspace index, lane docs, verification baseline | completed | start Sprint 1 once issue #8 closes |
| Sprint 1 -- DuckDB + Daily Cache | Add DuckDB, create the daily cache, and replace the old data-loader entrypoint | `duckdb_connector.py`, updated `setup-data`, clean import graph, unit coverage | completed | begin Sprint 2 backend execution |
| Sprint 2 -- Strategy + Backtester | Add the dual-method strategy interface and minute-level walk-forward pipeline | updated `backtester.py`, updated `active_strategy.py`, trading-day windows | completed | begin Sprint 3 backend + infra execution |
| Sprint 3 -- CLI + Docs + Tests | Finish CLI behavior, integration coverage, and runtime docs | updated `cli.py`, integration tests, updated `program.md` and `CLAUDE.md` | completed | move to Phase 4 verification and review sync |
| Phase 4 -- Verification + Closeout | Run the full gate and prepare review-ready evidence | green dependency sync, green test suite, smoke commands, review-fix evidence sync, issue evidence update | completed | move issue #11 to `workflow::review` |

## 8. Task Tables

### Phase 0 -- Planning And Spec Alignment

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| PLAN-01 | Confirm the live docs root and choose a single canonical workspace | Planning | none | 0.1d | completed | `docs/feature/v2-data-pipeline/` is the only planning root for this feature |
| PLAN-02 | Preserve the repo's V2 branch convention and record the dependency gate on issue #8 | Planning | PLAN-01 | 0.05d | completed | branch name and dependency note appear in the README, plan, and issue |
| PLAN-03 | Expand the workspace with backend, infra, and QA planning surfaces | Planning | PLAN-01 | 0.1d | completed | lane docs and updated test plan are linked from the workspace index |
| PLAN-04 | Rewrite issue #11 as the umbrella index card | Planning | PLAN-02, PLAN-03 | 0.1d | completed | issue contains required sections, a phase table with status, and workspace references |

### Sprint 1 -- DuckDB + Daily Cache

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| INFRA-01 | Validate dataset root, CLI binary, DuckDB output path, and temp-file budget | Infra | Phase 0 complete | 0.1d | completed | commands prove that paths, disk targets, and binary invocation are usable |
| DUCK-01 | Create or switch to `feature/v2-data-pipeline` and capture the pre-change baseline | Backend | Phase 0 complete, issue #8 complete | 0.1d | completed | branch is active and baseline `pytest --tb=short` evidence is recorded |
| DUCK-02 | Add `duckdb` dependency and implement `src/data/duckdb_connector.py` | Backend | DUCK-01, INFRA-01 | 0.6d | completed | daily-cache build/load helpers and minute-query bridge import cleanly |
| DUCK-03 | Replace `cli.py setup-data`, remove legacy data modules, and clean imports | Backend | DUCK-02 | 0.4d | completed | `setup-data` builds the DuckDB cache and no surviving imports reference removed modules |
| QA-01 | Add unit coverage for DuckDB helpers and capture the first data-path smoke result | QA | DUCK-02, DUCK-03 | 0.3d | completed | dedicated unit tests pass and smoke evidence is logged |

### Sprint 2 -- Strategy + Backtester

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| STRAT-01 | Extend the strategy contract with `select_universe(daily_data)` and minute-data `generate_signals()` | Backend | Sprint 1 complete | 0.3d | completed | the dual-method contract is documented and callable |
| STRAT-02 | Update strategy discovery and trading-day window calculation in the backtester | Backend | STRAT-01, QA-01 | 0.4d | completed | the backtester detects optional universe selection and produces 5 valid windows |
| STRAT-03 | Integrate the daily -> universe -> minute -> signals pipeline in `src/core/backtester.py` | Backend | STRAT-02 | 0.6d | completed | minute-level walk-forward runs through the full evaluation loop |
| QA-02 | Expand strategy-interface tests and add focused backtester coverage | QA | STRAT-01, STRAT-02, STRAT-03 | 0.3d | completed | unit tests cover the dual-method contract, signal lag, and window behavior |

### Sprint 3 -- CLI + Docs + Tests

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| CLI-01 | Update `fetch`, `backtest`, and `update-data` CLI flows to the DuckDB/minute-data model | Backend | Sprint 2 complete | 0.6d | completed | the CLI exposes the intended runtime behavior with stable arguments |
| QA-03 | Add DuckDB/minute fixtures and `tests/integration/test_minute_backtest.py` | QA | CLI-01 | 0.4d | completed | the end-to-end pipeline has fixture-backed integration coverage |
| DOC-01 | Update `program.md`, `CLAUDE.md`, and feature docs to the final runtime contracts | Planning | CLI-01, QA-03 | 0.2d | completed | docs match the implemented behavior and verification commands |

### Phase 4 -- Verification + Closeout

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| VER-01 | Run `uv sync --all-extras --dev`, targeted suites, and the full `pytest` gate | QA | Sprint 3 complete | 0.2d | completed | dependency sync and tests pass without unresolved skips or failures, including reopened review-fix regressions |
| VER-02 | Run CLI smoke tests for `setup-data`, `fetch`, `backtest`, and `update-data` | Infra | VER-01 | 0.2d | completed | smoke commands succeed and the outputs are captured as review evidence |
| VER-03 | Update the umbrella issue or PR with evidence, remaining risks, and review notes | Planning | VER-01, VER-02 | 0.1d | completed | review-ready summary links to docs, commands, and residual risks |

## 9. Execution Handoff

This document is the planning-layer summary. Execution must move through the sprint docs instead of
inventing new phase-specific work queues:

- `sprint1/sprint1-backend.md` for DuckDB dependency, cache build, and legacy module replacement
- `sprint1/sprint1-infra.md` for dataset-path validation, CLI binary checks, and cache-build smoke evidence
- `sprint2/sprint2-backend.md` for the strategy contract and backtester integration
- `sprint3/sprint3-backend.md` for CLI completion, integration tests, and runtime docs
- `sprint3/sprint3-infra.md` for final CLI smoke evidence and cache-refresh verification

The backend and infra lane docs define cross-sprint boundaries. The test plan defines the evidence
expected before a sprint can be considered complete.

## 10. Acceptance Criteria

- [x] The live docs root is confirmed as `docs/` and reused consistently
- [x] The canonical workspace choice is explicit: `docs/feature/v2-data-pipeline/`
- [x] The feature branch is explicitly named as `feature/v2-data-pipeline`
- [x] The workspace has a local index, a main development plan, backend lane doc, infra lane doc,
      test plan, and sprint execution docs
- [x] Issue #11 is defined as the umbrella index rather than the execution queue
- [x] `duckdb` is added to `pyproject.toml` and `uv sync` succeeds
- [x] `src/data/duckdb_connector.py` is created with daily-cache build/load helpers
- [x] `src/data/connector.py` and `src/data/preprocessor.py` are removed with no stale imports
- [x] The strategy interface supports `select_universe(daily_data)` plus minute-data
      `generate_signals()`
- [x] The backtester supports minute-level walk-forward via CLI minute-data queries
- [x] `fetch`, `backtest`, and `update-data` expose the new runtime model
- [x] Unit, integration, and full regression gates pass with recorded evidence

## 11. Verification And Evidence Expectations

The detailed gate list lives in `v2-data-pipeline-test-plan.md`. The minimum verification families
are:

```bash
# Baseline / dependency sync
uv sync --all-extras --dev
pytest --tb=short

# Data-path / cache build
uv run python cli.py setup-data
python -c "
import duckdb
con = duckdb.connect('data/daily_cache.duckdb', read_only=True)
r = con.execute('SELECT COUNT(*), COUNT(DISTINCT ticker), MIN(session_date), MAX(session_date) FROM daily_bars').fetchone()
print(f'Rows: {r[0]}, Tickers: {r[1]}, Range: {r[2]} to {r[3]}')
con.close()
"

# Import cleanliness
find src -type d -name '__pycache__' -prune -o -type f -name '*.py' -print0 | \
xargs -0 grep -n "data.connector\|data.preprocessor\|DataConnector\|prepare_data\|Preprocessor" || echo "CLEAN"

# Feature-specific tests
pytest tests/unit/test_duckdb_connector.py -v
pytest tests/unit/test_strategy_interface.py -v
PYTHONPATH=src pytest tests/unit/test_backtester_v2.py -v
pytest tests/integration/test_minute_backtest.py -v
```

## 12. Performance Budget

```text
Daily cache build:     ~30-60 min (11K tickers x 5 years, CLI SQL batched by month)
Daily cache size:      ~100 MB (DuckDB, compressed)
Per-window minute load: 5-15 sec (about 30 tickers x 60 days x 390 bars)
Full backtest:         ~2-3 min (5 windows + strategy computation)
```

## 13. Dependencies / Risks

| Risk | Mitigation |
| --- | --- |
| Issue #8 changes the surviving backtester contract late | Do not start Sprint 1 implementation until Phase 1 is functionally complete |
| DuckDB cache build is slow across the full dataset | Batch by month, log progress, and support resumable or append-only refresh |
| CLI subprocess queries time out or emit unexpected CSV schema | Validate binary behavior in INFRA-01 and keep parsing logic defensive |
| Legacy `connector.py` imports survive after module removal | Treat the global grep and targeted tests as a hard verification gate |
| Minute-bar volume overwhelms memory during walk-forward | Keep universe selection daily-first and query minute data per window only |
