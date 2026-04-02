# V2 Research -- Test Plan

> Feature branch: `feature/v2-research`
> Umbrella issue: #13

## Objective

Verify that SQLite Playbook is cleanly removed, Obsidian vault integration works correctly, research CLI outputs to vault, stock analysis CLI produces valid reports, and all new modules pass tests.

## Pre-removal Baseline

Before any changes, confirm the current state is green:

```bash
uv sync --all-extras --dev
pytest --tb=short
```

Record the test count and result as baseline.

## Test Removal Matrix

### Files to delete (unit tests)
| Test File | Module Under Test | Delete? |
| --- | --- | --- |
| `tests/unit/test_playbook_memory.py` | memory/playbook.py | YES |

### Files to keep (must survive)
| Test File | Module Under Test | Keep? |
| --- | --- | --- |
| `tests/unit/test_data.py` | data/connector.py | YES |
| `tests/unit/test_security.py` | backtester security | YES |
| `tests/unit/test_research.py` | core/research.py | YES -- may need updates |
| `tests/unit/test_retry_logic.py` | utils/retries.py | YES |
| `tests/unit/test_runner.py` | runner | YES |
| `tests/unit/test_telemetry_wandb.py` | utils/telemetry.py | YES |
| `tests/unit/test_tracker_metrics.py` | utils/iteration_tracker.py | YES |
| `tests/regression/test_determinism.py` | determinism | YES |
| `tests/conftest.py` | shared fixtures | CLEAN -- remove Playbook fixtures |

## New Test Files

### Sprint 1 tests
| Test File | Tests |
| --- | --- |
| `tests/unit/test_vault_config.py` | `config/vault.py`: path resolution, dir creation, `ensure_dirs()` |
| `tests/unit/test_vault_writer.py` | Vault write operations: Markdown formatting, frontmatter, file output |

### Sprint 2 tests
| Test File | Tests |
| --- | --- |
| `tests/unit/test_technical.py` | `src/analysis/technical.py`: momentum, volatility, volume, price levels |
| `tests/unit/test_regime.py` | `src/analysis/regime.py`: regime classification, vol percentile |
| `tests/unit/test_market_context.py` | `src/analysis/market_context.py`: SPY correlation, MA distance |
| `tests/unit/test_cli_research.py` | CLI research subcommand: query parsing, output format, vault write |
| `tests/unit/test_cli_analyze.py` | CLI analyze subcommand: ticker parsing, report generation, vault write |
| `tests/unit/test_cli_setup_vault.py` | CLI setup_vault subcommand: dir creation, idempotency |
| `tests/integration/test_research_pipeline.py` | End-to-end: research query -> vault write -> file exists |
| `tests/integration/test_analyze_pipeline.py` | End-to-end: analyze ticker -> vault write -> file exists |

## Test Specifications

### test_vault_config.py

```
test_get_vault_paths_returns_all_keys
  - Assert returns dict with keys: root, experiments, research, knowledge, strategies

test_ensure_dirs_creates_all_directories
  - Call ensure_dirs() with temp dir
  - Assert all 4 subdirectories exist

test_ensure_dirs_idempotent
  - Call ensure_dirs() twice
  - No error on second call
```

### test_technical.py

```
test_calc_momentum_basic
  - Given DataFrame with 60+ rows of close prices
  - Assert returns dict with roc_5d, roc_20d, roc_60d
  - Assert values are correct floats

test_calc_momentum_short_data
  - Given DataFrame with 3 rows
  - Assert roc_5d is None, roc_20d is None

test_calc_volatility
  - Given DataFrame with close prices
  - Assert returns dict with vol_5d, vol_20d, vol_60d (annualized)

test_analyze_volume
  - Given DataFrame with volume column
  - Assert returns relative_volume, volume_trend
```

### test_regime.py

```
test_classify_regime_bull_quiet
  - Construct data with positive returns, low vol
  - Assert regime is 'bull_quiet'

test_classify_regime_bear_volatile
  - Construct data with negative returns, high vol
  - Assert regime is 'bear_volatile'

test_classify_regime_returns_vol_percentile
  - Assert result dict has 'vol_percentile' key
  - Assert value is between 0 and 1
```

### test_market_context.py

```
test_calc_market_context_correlation
  - Given ticker data + SPY data
  - Assert returns correlation float between -1 and 1

test_calc_market_context_ma_distance
  - Assert returns dict with distance from 50d and 200d MA
```

### test_cli_research.py

```
test_research_command_shallow
  - Run: cli.py research "test query" --depth shallow --output stdout
  - Assert output contains "# Research:" header

test_research_command_outputs_yaml_frontmatter
  - Assert output starts with "---"
  - Assert contains note_type: research

test_research_command_writes_to_vault
  - Run with --output vault (or default)
  - Assert file created in vault research/ directory
```

### test_cli_analyze.py

```
test_analyze_command_single_ticker
  - Run: cli.py analyze SPY --output stdout --start 2025-01-01
  - Assert output contains "# Stock Analysis:" header

test_analyze_command_includes_all_sections
  - Assert output contains: Momentum, Volatility, Regime, Price Structure, Market Context

test_analyze_command_writes_to_vault
  - Assert file created in vault research/ directory
```

## Verification Steps

### Step 1: After Playbook removal (Sprint 1)
```bash
# Verify playbook files gone
test ! -f src/memory/playbook.py && echo "playbook.py GONE"
test ! -f tests/unit/test_playbook_memory.py && echo "test_playbook_memory.py GONE"

# No Playbook references
grep -rn "from src.memory.playbook\|import.*Playbook\|Playbook(" src/ tests/ cli.py || echo "CLEAN"

# Existing tests still pass
pytest --tb=short
```

### Step 2: After vault config tests (Sprint 1)
```bash
pytest tests/unit/test_vault_config.py tests/unit/test_vault_writer.py -v
```

### Step 3: After analysis module tests (Sprint 2)
```bash
pytest tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py -v
```

### Step 4: After CLI tests (Sprint 2)
```bash
pytest tests/unit/test_cli_research.py tests/unit/test_cli_analyze.py tests/unit/test_cli_setup_vault.py -v
```

### Step 5: Integration tests (Sprint 2)
```bash
pytest tests/integration/test_research_pipeline.py tests/integration/test_analyze_pipeline.py -v
```

### Step 6: Full test run (final gate)
```bash
pytest --tb=short -v
```
All tests must pass.

### Step 7: CLI smoke tests
```bash
uv run python cli.py setup_vault
uv run python cli.py research "mean reversion" --depth shallow --output stdout
uv run python cli.py analyze SPY --start 2025-01-01 --output stdout
```
All commands must run without error.

## Acceptance Criteria

- [ ] `tests/unit/test_playbook_memory.py` is deleted
- [ ] `tests/conftest.py` has no fixtures for Playbook
- [ ] No remaining test file imports from `src.memory.playbook`
- [ ] All new test files (9 files) exist and pass
- [ ] `pytest` passes with 0 failures
- [ ] `cli.py setup_vault` runs without error
- [ ] `cli.py research` runs without error
- [ ] `cli.py analyze` runs without error
