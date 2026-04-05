# Sprint 2 — Backend Plan

> Feature: `v2-overfit-defense`
> Role: Backend
> Derived from: #12 (Umbrella: Session 3 Overfit Defense) — Layer 2 advanced validation
> Last Updated: 2026-04-05 (Sprint 2 implementation complete; commit pending)

## 0) Governing Specs

1. `docs/overfit-defense-v2.md` — Overfit defense design (Sections 3-4, 6-8)
2. `docs/feature/v2-overfit-defense/v2-overfit-defense-development-plan.md` — Task table: CLI-01 through CLI-10

## 1) Sprint Mission

Build the Layer 2 advanced validation tools as CLI commands: CPCV combinatorial cross-validation (final validation step), regime robustness analysis (check strategy performance across market environments), and parameter stability testing (detect overfit to specific parameter values). Add the `validate` sub-command to cli.py. Write comprehensive tests and knowledge base notes documenting the overfit defense methods.

## 2) Scope / Out of Scope

**Scope**
- Create `src/validation/cpcv.py` with `run_cpcv()` function
- Create `src/validation/regime.py` with `regime_analysis()` function
- Create `src/validation/stability.py` with `parameter_stability_test()` function
- Add `validate` sub-command to `cli.py` with `--method` flag (cpcv, regime, stability)
- Add method-specific flags: `--groups`, `--test-groups` (cpcv), `--perturbation`, `--steps` (stability)
- Write unit tests: test_cpcv.py, test_regime.py, test_stability.py
- Write integration test: test_validate_cli.py
- Write knowledge base notes on overfit defense (in experiments/notes/ or docs/)

**Out of Scope**
- Newey-West Sharpe implementation — Sprint 1
- Deflated SR implementation — Sprint 1
- Monte Carlo removal — Sprint 1
- Backtester output format changes — Sprint 1
- program.md updates — Sprint 1

## 3) Step-by-Step Plan

### Step 1 — Verify Sprint 1 complete
- [x] `pytest tests/unit/test_newey_west.py tests/unit/test_deflated_sr.py tests/unit/test_backtester_overfit.py -v`
- [x] Verify `src/validation/newey_west.py` and `src/validation/deflated_sr.py` exist
- [x] Verify backtester output includes SCORE (NW), NAIVE_SHARPE, DEFLATED_SR, NW_SHARPE_BIAS
- [x] Verify Monte Carlo removed from backtester

### Step 2 — Create CPCV validation module (CLI-01)
- [x] Create `src/validation/cpcv.py` implementing `run_cpcv(strategy_class, data_config, n_groups=8, n_test=2)`
  - Split time axis into N consecutive groups
  - Generate all C(N,k) combinations for test groups
  - For each combination: train on remaining groups with purging, test on selected groups
  - Purging: remove training samples within `purge_bars` (default 390) of test boundary
  - Compute Sharpe per path using `newey_west_sharpe()`
  - Return dict: sharpe_distribution, mean_sharpe, std_sharpe, pct_positive, worst_sharpe, best_sharpe
- [x] Default: C(8,2) = 28 paths for thorough validation
- [x] Fast mode: C(6,1) = 6 paths for quick checks

### Step 3 — Create regime analysis module (CLI-02)
- [x] Create `src/validation/regime.py` implementing `regime_analysis(strategy_returns, market_data)`
  - Classify into 4 regimes based on rolling 20-day metrics:
    - Bull Quiet: 20d return > 0, 20d vol < median
    - Bull Volatile: 20d return > 0, 20d vol >= median
    - Bear Quiet: 20d return <= 0, 20d vol < median
    - Bear Volatile: 20d return <= 0, 20d vol >= median
  - Compute per-regime metrics: Sharpe (Newey-West), total return, bar count, win rate
  - Return dict keyed by regime name
  - Print verdict: CONCENTRATED if >70% profit from one regime type, BALANCED if distributed

### Step 4 — Create parameter stability module (CLI-03)
- [x] Create `src/validation/stability.py` implementing `parameter_stability_test(strategy_class, data_config, perturbation=0.2, steps=5)`
  - Extract numeric `__init__` parameters via `inspect.signature`
  - For each parameter: sweep from `default * (1 - perturbation)` to `default * (1 + perturbation)` in `steps` values
  - Run backtest for each perturbed parameter value
  - Compute stability score: fraction of values achieving >50% of peak Sharpe
  - Return per-parameter stability + overall stability (mean)
  - Print verdict: GOOD if overall >= 0.7, MODERATE if 0.5-0.7, POOR if < 0.5
  - Handle edge case: strategy with no numeric params → return stability=1.0, message "no tuneable parameters"

### Step 5 — Add validate sub-command to cli.py (CLI-04)
- [x] Add `validate` sub-command with `--method` flag
  - `--method cpcv`: run CPCV validation
    - Optional: `--groups N` (default 8), `--test-groups K` (default 2)
  - `--method regime`: run regime analysis
  - `--method stability`: run parameter stability test
    - Optional: `--perturbation P` (default 0.2), `--steps S` (default 5)
- [x] Load active strategy from `src/strategies/active_strategy.py`
- [x] Load data from `data/cache/`
- [x] Print formatted output to stdout
- [x] Exit 0 on success, 1 on error with informative message

### Step 6 — Write CPCV tests (CLI-05)
- [x] Create `tests/unit/test_cpcv.py`:
  - `test_cpcv_path_count_6_1`: C(6,1) = 6 paths
  - `test_cpcv_path_count_8_2`: C(8,2) = 28 paths
  - `test_cpcv_purging`: train data has purge bars removed at boundary
  - `test_cpcv_embargo`: test data has embargo buffer applied
  - `test_cpcv_no_overlap`: train and test groups never share time index
  - `test_cpcv_output_format`: output dict has required keys
  - `test_cpcv_pct_positive_range`: pct_positive in [0, 1]
  - `test_cpcv_with_constant_strategy`: zero-signal strategy, Sharpe near 0
- [x] Verify: `pytest tests/unit/test_cpcv.py -v`

### Step 7 — Write regime tests (CLI-06)
- [x] Create `tests/unit/test_regime.py`:
  - `test_regime_four_classifications`: all 4 regimes classified
  - `test_regime_bull_quiet_criteria`: correct classification logic
  - `test_regime_bear_volatile_criteria`: correct classification logic
  - `test_regime_per_regime_sharpe`: Newey-West Sharpe per regime
  - `test_regime_all_bull`: only bull regimes in bull market data
  - `test_regime_empty_strategy_returns`: graceful handling
  - `test_regime_output_keys`: correct dict keys
- [x] Verify: `pytest tests/unit/test_regime.py -v`

### Step 8 — Write parameter stability tests (CLI-07)
- [x] Create `tests/unit/test_stability.py`:
  - `test_param_extraction`: numeric params correctly extracted
  - `test_param_extraction_no_params`: no numeric params → empty dict
  - `test_perturbation_range`: values span correct range
  - `test_perturbation_steps`: correct number of test values
  - `test_stability_score_range`: each score in [0, 1]
  - `test_stability_high_stability`: flat Sharpe → near 1.0
  - `test_stability_low_stability`: sharp peak → near 0.0
  - `test_overall_stability_is_mean`: overall = mean of individual scores
- [x] Verify: `pytest tests/unit/test_stability.py -v`

### Step 9 — Write CLI integration tests (CLI-08)
- [x] Create `tests/integration/test_validate_cli.py`:
  - `test_cli_validate_cpcv`: `--method cpcv` exits 0
  - `test_cli_validate_regime`: `--method regime` exits 0
  - `test_cli_validate_stability`: `--method stability` exits 0
  - `test_cli_validate_invalid_method`: `--method invalid` exits non-zero
  - `test_cli_validate_cpcv_custom_groups`: `--groups 6 --test-groups 1` works
  - `test_cli_validate_stability_custom_perturbation`: `--perturbation 0.3 --steps 7` works
  - `test_cli_validate_no_data`: missing data → informative error
- [x] Verify: `pytest tests/integration/test_validate_cli.py -v`

### Step 10 — Write knowledge base notes on overfit defense (CLI-09)
- [x] Create overfit defense knowledge base document covering:
  - Newey-West Sharpe: why serial correlation matters for minute bars, Bartlett kernel, interpretation
  - Deflated Sharpe Ratio: multiple testing problem, PSR, Gumbel approximation, when DSR < 0.95
  - CPCV: combinatorial cross-validation vs walk-forward, purging/embargo, path interpretation
  - Regime analysis: 4-regime classification, concentrated vs balanced profits, regime adaptation
  - Parameter stability: perturbation testing, stability score interpretation, sharp optima detection
  - Academic references: Lopez de Prado (2018), Bailey & Lopez de Prado (2014), Harvey et al. (2016)

### Step 11 — Sprint 2 full integration test (CLI-10)
- [x] Run full test suite: `pytest --tb=short -v`
- [x] Manual smoke test each CLI command:
  ```bash
  uv run python cli.py validate --method cpcv --groups 6 --test-groups 1
  uv run python cli.py validate --method regime
  uv run python cli.py validate --method stability --perturbation 0.2 --steps 5
  ```
- [x] Verify all commands produce formatted output with verdict

### Step 12 — Commit sprint 2 changes
- [x] `git add src/validation/cpcv.py src/validation/regime.py src/validation/stability.py`
- [x] `git add tests/unit/test_cpcv.py tests/unit/test_regime.py tests/unit/test_stability.py`
- [x] `git add tests/integration/test_validate_cli.py`
- [x] `git add cli.py`
- [x] `git add` knowledge base notes file
- [x] `git commit -m "feat(overfit): add CPCV, regime check, and parameter stability CLI commands"`

## 4) Test Plan

- [ ] After Step 6: `pytest tests/unit/test_cpcv.py -v`
- [ ] After Step 7: `pytest tests/unit/test_regime.py -v`
- [ ] After Step 8: `pytest tests/unit/test_stability.py -v`
- [ ] After Step 9: `pytest tests/integration/test_validate_cli.py -v`
- [ ] After Step 11: `pytest --tb=short -v` — full suite green

## 5) Verification Commands

```bash
# Confirm validation modules exist
test -f src/validation/cpcv.py && echo "cpcv.py OK"
test -f src/validation/regime.py && echo "regime.py OK"
test -f src/validation/stability.py && echo "stability.py OK"

# Confirm test files exist
test -f tests/unit/test_cpcv.py && echo "test_cpcv.py OK"
test -f tests/unit/test_regime.py && echo "test_regime.py OK"
test -f tests/unit/test_stability.py && echo "test_stability.py OK"
test -f tests/integration/test_validate_cli.py && echo "test_validate_cli.py OK"

# Confirm CLI sub-command exists
grep -n "validate" cli.py

# Run CLI smoke tests
uv run python cli.py validate --method cpcv --groups 6 --test-groups 1
uv run python cli.py validate --method regime
uv run python cli.py validate --method stability --perturbation 0.2 --steps 5

# Full test suite
pytest --tb=short -v
```

## 6) Implementation Update Space

### Completed Work

- Added `src/validation/cpcv.py` with path generation, purge/embargo handling, and runner-level purge-aware evaluation.
- Added `src/validation/regime.py` with 4-quadrant regime classification and per-regime Newey-West metrics.
- Added `src/validation/stability.py` with numeric parameter extraction, perturbation sweeps, and stability verdicts.
- Added `validate` command to `cli.py` for `cpcv`, `regime`, and `stability`, plus reusable strategy loading and combined-return helpers.
- Added Sprint 2 test coverage in `tests/unit/test_cpcv.py`, `tests/unit/test_regime.py`, `tests/unit/test_stability.py`, `tests/integration/test_validate_cli.py`, and CLI registration coverage in `tests/unit/test_cli.py`.
- Added `docs/feature/v2-overfit-defense/overfit-defense-knowledge-base.md` and linked it from the feature README.

### Command Results

- `uv run pytest tests/unit/test_cpcv.py tests/unit/test_regime.py tests/unit/test_stability.py tests/integration/test_validate_cli.py -v` -> `31 passed in 0.65s`
- `uv run pytest --tb=short -q` -> `148 passed in 1.36s`
- `CACHE_DIR=/tmp/quant-smoke-cache uv run python cli.py validate --method cpcv --groups 6 --test-groups 1` -> exited `0`, printed `VERDICT: STRONG`
- `CACHE_DIR=/tmp/quant-smoke-cache uv run python cli.py validate --method regime` -> exited `0`, printed `VERDICT: CONCENTRATED`
- `CACHE_DIR=/tmp/quant-smoke-cache uv run python cli.py validate --method stability --perturbation 0.2 --steps 5` -> exited `0`, printed `VERDICT: GOOD`

### Blockers / Deviations

- The repo does not currently ship seeded `data/cache/` data in this worktree, so manual CLI smoke verification used a temporary synthetic cache at `/tmp/quant-smoke-cache`.
- The umbrella issue body on GitHub still reports Sprint 1 / Sprint 2 status as pending; local sprint docs now reflect the implemented state and should be synced during closeout.
- An untracked root-level `strategy.py` file was present in the worktree during implementation and was left untouched.

### Follow-ups

- Step 12 commit is still pending in this worktree.
- After merge: update CLAUDE.md to reflect overfit defense architecture
