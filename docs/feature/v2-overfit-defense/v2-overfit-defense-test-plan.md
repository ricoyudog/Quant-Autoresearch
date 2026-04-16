> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Overfit Defense — Test Plan

> Feature branch: `feature/v2-overfit-defense`
> Umbrella issue: #12

## Objective

Verify that all overfit defense components work correctly: Newey-West Sharpe replaces raw Sharpe accurately, Deflated Sharpe Ratio adjusts for multiple testing, Monte Carlo is cleanly removed, and CLI validation commands produce correct results.

## Pre-implementation Baseline

Before any changes, confirm the current state is green:

```bash
uv sync --all-extras --dev
pytest --tb=short
```

Record the test count and result as baseline.

## Test File Structure

```
tests/
├── unit/
│   ├── test_newey_west.py           ← Sprint 1: Newey-West Sharpe calculation
│   ├── test_deflated_sr.py          ← Sprint 1: Deflated Sharpe Ratio calculation
│   ├── test_backtester_overfit.py   ← Sprint 1: Backtester integration with NW + DSR
│   ├── test_cpcv.py                 ← Sprint 2: CPCV validation logic
│   ├── test_regime.py               ← Sprint 2: Regime analysis logic
│   └── test_stability.py            ← Sprint 2: Parameter stability logic
├── integration/
│   └── test_validate_cli.py         ← Sprint 2: CLI validate command integration
└── conftest.py                      ← Updated with validation test fixtures
```

## Sprint 1 Test Cases

### test_newey_west.py

| Test | What it verifies |
| --- | --- |
| `test_nw_sharpe_basic` | Simple uncorrelated returns produce Sharpe close to raw Sharpe |
| `test_nw_sharpe_serial_correlation` | Returns with positive autocorrelation: NW Sharpe < raw Sharpe |
| `test_nw_sharpe_negative_autocorrelation` | Bid-ask bounce pattern: NW Sharpe > raw Sharpe |
| `test_nw_sharpe_empty_series` | Empty or constant returns return 0.0 |
| `test_nw_sharpe_single_value` | Single return value returns 0.0 |
| `test_nw_sharpe_max_lag_override` | Custom max_lag parameter respected |
| `test_nw_sharpe_annualization` | Output matches expected annualized value for known input |
| `test_nw_sharpe_bartlett_weights` | Verify Bartlett kernel weighting is applied correctly |

### test_deflated_sr.py

| Test | What it verifies |
| --- | --- |
| `test_dsr_single_trial` | With n_trials=1, DSR reduces to PSR (no multiple testing penalty) |
| `test_dsr_multiple_trials` | With many trials, DSR is lower than single-trial PSR |
| `test_dsr_high_sharpe` | Very high Sharpe with few trials: DSR close to 1.0 |
| `test_dsr_low_sharpe` | Low Sharpe with many trials: DSR close to 0.0 |
| `test_dsr_zero_returns` | Zero returns: DSR returns 0.5 (indeterminate) |
| `test_dsr_skew_kurtosis` | Non-normal returns (high skew/kurtosis) reduce DSR |
| `test_dsr_auto_compute_stats` | Skew and kurtosis computed automatically when not provided |
| `test_dsr_range` | DSR always in [0, 1] range |

### test_backtester_overfit.py

| Test | What it verifies |
| --- | --- |
| `test_output_contains_naive_sharpe` | Backtester output includes NAIVE_SHARPE line |
| `test_output_contains_deflated_sr` | Backtester output includes DEFLATED_SR line |
| `test_output_contains_nw_bias` | Backtester output includes NW_SHARPE_BIAS line |
| `test_score_is_newey_west` | SCORE value matches Newey-West Sharpe (not raw Sharpe) |
| `test_no_p_value_in_output` | P_VALUE does not appear in backtester output |
| `test_no_monte_carlo_function` | `monte_carlo_permutation_test` does not exist in backtester module |
| `test_results_tsv_new_columns` | results.tsv header includes naive_sharpe, deflated_sr, nw_bias |
| `test_nw_bias_calculation` | NW_SHARPE_BIAS = NAIVE_SHARPE - SCORE |
| `test_baseline_constraint_retained` | SCORE < BASELINE_SHARPE still triggers DISCARD |

## Sprint 2 Test Cases

### test_cpcv.py

| Test | What it verifies |
| --- | --- |
| `test_cpcv_path_count_6_1` | C(6,1) = 6 paths generated |
| `test_cpcv_path_count_8_2` | C(8,2) = 28 paths generated |
| `test_cpcv_purging` | Train data has purge bars removed at boundary |
| `test_cpcv_embargo` | Test data has embargo buffer applied |
| `test_cpcv_no_overlap` | Train and test groups never share the same time index |
| `test_cpcv_output_format` | Output dict has sharpe_distribution, mean_sharpe, std_sharpe, pct_positive |
| `test_cpcv_pct_positive_range` | pct_positive is in [0, 1] |
| `test_cpcv_with_constant_strategy` | Zero-signal strategy: all Sharpe values near 0 |

### test_regime.py

| Test | What it verifies |
| --- | --- |
| `test_regime_four_classifications` | All 4 regimes classified: bull_quiet, bull_volatile, bear_quiet, bear_volatile |
| `test_regime_bull_quiet_criteria` | 20d return > 0 and 20d vol < median |
| `test_regime_bear_volatile_criteria` | 20d return <= 0 and 20d vol >= median |
| `test_regime_per_regime_sharpe` | Each regime gets its own Newey-West Sharpe |
| `test_regime_all_bull` | All bull market: only bull regimes appear |
| `test_regime_empty_strategy_returns` | Empty returns: graceful handling |
| `test_regime_output_keys` | Output dict has correct keys per regime |

### test_stability.py

| Test | What it verifies |
| --- | --- |
| `test_param_extraction` | Numeric __init__ params correctly extracted |
| `test_param_extraction_no_params` | Strategy with no numeric params: returns empty dict |
| `test_perturbation_range` | Values span default_val * (1 - perturbation) to default_val * (1 + perturbation) |
| `test_perturbation_steps` | Number of test values equals `steps` parameter |
| `test_stability_score_range` | Each param stability score in [0, 1] |
| `test_stability_high_stability` | Flat Sharpe surface: stability near 1.0 |
| `test_stability_low_stability` | Sharp peak Sharpe surface: stability near 0.0 |
| `test_overall_stability_is_mean` | Overall stability is mean of individual param stabilities |

### test_validate_cli.py

| Test | What it verifies |
| --- | --- |
| `test_cli_validate_cpcv` | `uv run python cli.py validate --method cpcv` exits 0 |
| `test_cli_validate_regime` | `uv run python cli.py validate --method regime` exits 0 |
| `test_cli_validate_stability` | `uv run python cli.py validate --method stability` exits 0 |
| `test_cli_validate_invalid_method` | `uv run python cli.py validate --method invalid` exits non-zero |
| `test_cli_validate_cpcv_custom_groups` | `--groups 6 --test-groups 1` works |
| `test_cli_validate_stability_custom_perturbation` | `--perturbation 0.3 --steps 7` works |
| `test_cli_validate_no_data` | Missing data directory: informative error message |

## Verification Steps

### Step 1: After Sprint 1 implementation

```bash
# Unit tests for new validation functions
pytest tests/unit/test_newey_west.py tests/unit/test_deflated_sr.py tests/unit/test_backtester_overfit.py -v

# Verify Monte Carlo removed
grep -rn "monte_carlo_permutation_test" src/core/backtester.py || echo "MONTE CARLO REMOVED"
grep -rn "P_VALUE" src/core/backtester.py || echo "P_VALUE REMOVED"

# Verify new output fields present
grep -n "NAIVE_SHARPE\|DEFLATED_SR\|NW_SHARPE_BIAS" src/core/backtester.py
```

### Step 2: After Sprint 2 implementation

```bash
# Unit tests for CLI validation
pytest tests/unit/test_cpcv.py tests/unit/test_regime.py tests/unit/test_stability.py -v

# Integration tests
pytest tests/integration/test_validate_cli.py -v

# Full test suite
pytest --tb=short -v
```

### Step 3: Manual smoke test

```bash
# Run backtester and verify output format
uv run python src/core/backtester.py 2>&1 | head -30

# Run CLI validation commands
uv run python cli.py validate --method cpcv --groups 6 --test-groups 1
uv run python cli.py validate --method regime
uv run python cli.py validate --method stability --perturbation 0.2 --steps 5
```

## Acceptance Criteria

- [ ] All Sprint 1 unit tests pass (test_newey_west.py, test_deflated_sr.py, test_backtester_overfit.py)
- [ ] All Sprint 2 unit tests pass (test_cpcv.py, test_regime.py, test_stability.py)
- [ ] CLI integration tests pass (test_validate_cli.py)
- [ ] No reference to `monte_carlo_permutation_test` or `P_VALUE` in backtester.py
- [ ] `pytest` full suite passes with 0 failures
- [ ] Manual backtester run shows SCORE (NW), NAIVE_SHARPE, DEFLATED_SR, NW_SHARPE_BIAS
- [ ] All 3 CLI validate commands execute without error
