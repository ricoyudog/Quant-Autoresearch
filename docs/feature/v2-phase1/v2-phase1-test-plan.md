> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Phase 1 — Test Plan

> Feature branch: `feature/v2-phase1`
> Umbrella issue: #8

## Objective

Verify that all backtester upgrades, program.md creation, and EDITABLE REGION removal are correct. Two new test files cover the new functionality.

## Pre-change Baseline

Before any changes, confirm the current state is green:

```bash
uv sync --all-extras --dev
pytest --tb=short -q
```

Record the test count and result as baseline.

## New Test Files

### test_backtester_v2.py

Tests for the 4 new functions in backtester.py.

| Test Function | What It Tests | Approach |
| --- | --- | --- |
| `test_find_strategy_class_found` | Finds a class with `generate_signals` | Create sandbox_locals with a mock class |
| `test_find_strategy_class_not_found` | Returns None when no matching class | Empty sandbox_locals |
| `test_find_strategy_class_multiple` | Finds first matching class among several | Multiple classes, one has generate_signals |
| `test_calculate_metrics_basic` | All 10 metrics computed | Synthetic returns + trades series |
| `test_calculate_metrics_zero_std` | Returns zeros when std is 0 | Constant returns series |
| `test_calculate_metrics_empty` | Handles empty input gracefully | Empty Series |
| `test_calculate_metrics_sortino` | Sortino differs from Sharpe for skewed returns | Returns with large downside |
| `test_calculate_metrics_calmar` | Calmar = annualized_return / abs(max_drawdown) | Known cumulative return path |
| `test_calculate_metrics_profit_factor` | PF = gross_profit / gross_loss | Mixed win/loss trades |
| `test_calculate_metrics_win_rate` | WR = winning_trades / total_trades | Known trade distribution |
| `test_calculate_metrics_avg_win_loss` | Avg of positive and negative trades | Known trade values |
| `test_calculate_metrics_max_dd_days` | Longest drawdown duration | Series with known drawdown period |
| `test_calculate_baseline_sharpe_basic` | Buy&Hold Sharpe computed | Dict of DataFrames with returns |
| `test_calculate_baseline_sharpe_zero_std` | Returns 0.0 when std is 0 | Constant returns across all symbols |
| `test_run_per_symbol_analysis_basic` | Per-symbol dict with correct keys | Multi-symbol data dict |
| `test_run_per_symbol_analysis_signal_lag` | Signals shifted by 1 | Verify shift(1) applied |
| `test_output_format_yaml_like` | Output matches Section 2.1 spec | Capture stdout, parse format |

### test_strategy_interface.py

Tests for dynamic class loading and free-form strategy file.

| Test Function | What It Tests | Approach |
| --- | --- | --- |
| `test_free_form_class_accepted` | Any class with generate_signals works | Custom class name, different logic |
| `test_custom_class_name` | Class named "MomentumStrategy" loads fine | Non-default class name |
| `test_multiple_methods_allowed` | Class with extra methods besides generate_signals | Class with generate_signals + helper |
| `test_no_generate_signals_rejected` | Class without generate_signals is rejected | Class missing the required method |
| `test_editable_region_removed` | No EDITABLE REGION markers in file | Grep active_strategy.py |
| `test_strategy_in_sandbox` | Strategy runs in RestrictedPython sandbox | Load and execute via sandbox |
| `test_strategy_returns_series` | generate_signals returns pd.Series | Verify return type |
| `test_strategy_signal_range` | Signals are in {-1, 0, 1} | Check signal values |

## Verification Steps

### Step 1: After Sprint 1 (backtester changes)

```bash
# Verify new functions are importable
python -c "from src.core.backtester import find_strategy_class, calculate_metrics, calculate_baseline_sharpe, run_per_symbol_analysis; print('IMPORTS OK')"

# Verify monte_carlo removed
python -c "from src.core import backtester; assert not hasattr(backtester, 'monte_carlo_permutation_test'), 'FAIL: still present'; print('REMOVAL OK')"

# Run existing tests to confirm nothing broke
pytest tests/unit/ -v --tb=short
```

### Step 2: After Sprint 2 (program.md + strategy + tests)

```bash
# Verify program.md
test -f program.md && head -5 program.md

# Verify EDITABLE REGION removed
grep "EDITABLE REGION" src/strategies/active_strategy.py && echo "FAIL" || echo "OK"

# Run new tests
pytest tests/unit/test_backtester_v2.py tests/unit/test_strategy_interface.py -v

# Full test suite
pytest --tb=short -v
```

### Step 3: Integration verification

```bash
# Run backtester end-to-end (requires data)
uv run python src/core/backtester.py 2>&1 | head -20

# Verify output format
uv run python src/core/backtester.py 2>&1 | grep "^SCORE:\|^SORTINO:\|^CALMAR:\|^DRAWDOWN:\|^MAX_DD_DAYS:\|^TRADES:\|^P_VALUE:\|^WIN_RATE:\|^PROFIT_FACTOR:\|^AVG_WIN:\|^AVG_LOSS:\|^BASELINE_SHARPE:\|^PER_SYMBOL:"
```

## Acceptance Criteria

- [ ] `tests/unit/test_backtester_v2.py` exists with 18+ test functions
- [ ] `tests/unit/test_strategy_interface.py` exists with 8+ test functions
- [ ] All new tests pass
- [ ] All pre-existing tests still pass
- [ ] Backtester output includes all 12 metrics (SCORE, SORTINO, CALMAR, DRAWDOWN, MAX_DD_DAYS, TRADES, P_VALUE, WIN_RATE, PROFIT_FACTOR, AVG_WIN, AVG_LOSS, BASELINE_SHARPE)
- [ ] Backtester output includes PER_SYMBOL block
- [ ] `program.md` exists at root
- [ ] No EDITABLE REGION markers in `active_strategy.py`
