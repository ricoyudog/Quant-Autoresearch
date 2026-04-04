# V2 Data Pipeline -- Test Plan

> Feature branch: `feature/v2-data-pipeline`
> Umbrella issue: #11
> Last updated: 2026-04-04
> Planning status: verification design complete; execution evidence pending

## Objective

Verify that the DuckDB-based data pipeline works end to end: daily cache creation, minute-level CLI
queries, the dual-method strategy contract, minute-level walk-forward backtesting, and the CLI
commands that expose the runtime model.

## Evidence Expectations

- Record the pre-change baseline before Sprint 1 starts
- Capture any long-running data-path commands separately from unit-test output
- Treat stale-import scans and CLI smoke runs as hard release gates, not optional spot checks
- Store merge-ready evidence in the issue or PR summary with links back to this workspace

## Coverage Matrix

| Phase | Lane | Surface | Commands / Evidence | Exit Criteria |
| --- | --- | --- | --- | --- |
| Phase 0 | QA | Repo baseline | `uv sync --all-extras --dev`, `pytest --tb=short` | Baseline result recorded before branch work starts |
| Sprint 1 | QA + Infra | DuckDB cache build, helper imports, legacy-import cleanup | `pytest tests/unit/test_duckdb_connector.py -v`, `uv run python cli.py setup-data`, runtime-module scan | Cache builds, helper tests pass, no stale data-loader imports |
| Sprint 2 | QA | Strategy contract and backtester behavior | `pytest tests/unit/test_strategy_interface.py -v`, targeted backtester import or behavior checks | Dual-method contract and trading-day windows verified |
| Sprint 3 | QA | CLI surface, integration path, runtime docs | `pytest tests/integration/test_minute_backtest.py -v`, CLI smoke commands | End-to-end pipeline and CLI behavior verified |
| Phase 4 | QA + Infra | Full regression and merge gate | `pytest --tb=short -v`, full CLI smoke set, issue evidence update | Review-ready evidence exists with no unresolved regressions |

## Planned Test Files

### New Coverage

| Test File | Surface | Key Cases |
| --- | --- | --- |
| `tests/unit/test_duckdb_connector.py` | `src/data/duckdb_connector.py` | cache creation, schema, date filtering, trading-day lookup, minute-query error handling |
| `tests/integration/test_minute_backtest.py` | full pipeline | daily -> universe -> minute -> signals -> metrics, window boundaries, output shape |

### Existing Files To Expand

| Test File | Planned Change |
| --- | --- |
| `tests/unit/test_strategy_interface.py` | add `select_universe` detection, minute-data signal shape, and lag enforcement cases |
| `tests/conftest.py` | add DuckDB fixtures, sample daily data, and minute-data fixtures |
| `tests/unit/test_data.py` | remove or rewrite connector-only expectations after old modules are retired |

### Existing Tests To Keep Green

| Test File | Surface |
| --- | --- |
| `tests/unit/test_security.py` | backtester sandbox and security rules |
| `tests/unit/test_playbook_memory.py` | memory/playbook |
| `tests/unit/test_research.py` | research helpers |
| `tests/unit/test_retry_logic.py` | retry helpers |
| `tests/unit/test_runner.py` | runner flow |
| `tests/unit/test_telemetry_wandb.py` | telemetry |
| `tests/unit/test_tracker_metrics.py` | iteration tracking |
| `tests/regression/test_determinism.py` | deterministic behavior |

## Phase Gates

### Phase 0 -- Baseline

```bash
uv sync --all-extras --dev
pytest --tb=short
```

Record total tests, pass/fail count, and any existing skips before feature work starts.

### Sprint 1 -- DuckDB + Daily Cache

```bash
pytest tests/unit/test_duckdb_connector.py -v

uv run python cli.py setup-data
python -c "
import duckdb
con = duckdb.connect('data/daily_cache.duckdb', read_only=True)
r = con.execute('SELECT COUNT(*), COUNT(DISTINCT ticker), MIN(session_date), MAX(session_date) FROM daily_bars').fetchone()
print(f'Rows: {r[0]}, Tickers: {r[1]}, Range: {r[2]} to {r[3]}')
con.close()
"

find src -type d -name '__pycache__' -prune -o -type f -name '*.py' -print0 | \
xargs -0 grep -n "data.connector\|data.preprocessor\|DataConnector\|prepare_data\|Preprocessor" || echo "CLEAN"
```

### Sprint 2 -- Strategy + Backtester

```bash
pytest tests/unit/test_strategy_interface.py -v

python -c "
from src.strategies.active_strategy import *
print('Strategy interface OK')
"

python -c "
from src.core.backtester import *
print('Backtester imports OK')
"
```

If a focused behavior helper is added for trading-day windows, add a direct test for that helper
instead of relying on import-only checks.

### Sprint 3 -- CLI + Integration

```bash
pytest tests/integration/test_minute_backtest.py -v

uv run python cli.py fetch AAPL --start 2025-11-03 --end 2025-11-05
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
uv run python cli.py update_data
```

### Phase 4 -- Full Regression

```bash
pytest --tb=short -v
```

Any failures in surviving tests outside the data pipeline must still block closeout until they are
explained or resolved.

## Merge Gate Checklist

- [ ] Baseline test result recorded before feature work
- [x] `tests/unit/test_duckdb_connector.py` passes
- [ ] `tests/unit/test_strategy_interface.py` passes with the dual-method contract
- [ ] `tests/integration/test_minute_backtest.py` passes or is replaced by an explicitly documented
      guarded smoke path
- [ ] `tests/conftest.py` contains DuckDB and minute-data fixtures
- [ ] Legacy connector/preprocessor expectations are removed or rewritten
- [ ] No surviving test imports reference removed data-loader modules
- [ ] `pytest --tb=short -v` passes
- [x] `uv run python cli.py setup-data` works end to end
- [ ] `uv run python cli.py backtest` works end to end
- [ ] `uv run python cli.py update_data` works without duplicate-row regressions
