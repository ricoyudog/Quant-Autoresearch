# Sprint 1 — Backend Plan

> Feature: `v2-overfit-defense`
> Role: Backend
> Derived from: #12 (Umbrella: Session 3 Overfit Defense) — Layer 1 built-in defense
> Last Updated: 2026-04-05 (Sprint 1 closeout)

## 0) Governing Specs

1. `docs/overfit-defense-v2.md` — Overfit defense design (Sections 1-2, 5-6)
2. `docs/upgrade-plan-v2.md` — V2 upgrade design (Section 2: backtester output format)
3. `docs/feature/v2-overfit-defense/v2-overfit-defense-development-plan.md` — Task table: NW-01 through NW-10

## 1) Sprint Mission

Replace the backtester's raw Sharpe Ratio with Newey-West adjusted Sharpe (correcting minute-bar serial correlation), add Deflated Sharpe Ratio as an output metric (adjusting for multiple testing), and remove the Monte Carlo permutation test. Update the output format to include NAIVE_SHARPE, DEFLATED_SR, and NW_SHARPE_BIAS. Update program.md with overfitting defense guidance.

## 2) Scope / Out of Scope

**Scope**
- Create `src/validation/__init__.py` and `src/validation/newey_west.py` with `newey_west_sharpe()` function
- Create `src/validation/deflated_sr.py` with `deflated_sharpe_ratio()` function
- Replace raw Sharpe calculation in `src/core/backtester.py` with `newey_west_sharpe()`
- Add Deflated SR calculation to backtester output
- Remove `monte_carlo_permutation_test` function from `src/core/backtester.py`
- Remove P_VALUE from output format and results.tsv
- Add NAIVE_SHARPE, DEFLATED_SR, NW_SHARPE_BIAS to output format and results.tsv
- Update hard constraints: remove P_VALUE constraint, retain SCORE < BASELINE_SHARPE
- Add overfitting defense guidance section to program.md
- Write unit tests: test_newey_west.py, test_deflated_sr.py, test_backtester_overfit.py

**Out of Scope**
- CPCV validation CLI — Sprint 2
- Regime check CLI — Sprint 2
- Parameter stability CLI — Sprint 2
- CLI validate sub-command — Sprint 2
- Knowledge base notes — Sprint 2

## 3) Step-by-Step Plan

### Step 1 — Create feature branch + verify Phase 1 dependency
- [x] `git checkout -b feature/v2-overfit-defense main` (or from Phase 1 branch)
- [x] Verify Phase 1 (issue #8) is complete: backtester has dynamic loading, multi-metric output, walk-forward 5 windows
- [x] Run `pytest --tb=short -q` and record test count as baseline
- [x] Verify `src/core/backtester.py` has `calculate_metrics()`, `calculate_baseline_sharpe()`, `run_per_symbol_analysis()` functions

### Step 2 — Create validation module with Newey-West Sharpe (NW-02)
- [x] Create `src/validation/__init__.py`
- [x] Create `src/validation/newey_west.py` implementing `newey_west_sharpe(returns, max_lag=None)`
  - Use Bartlett kernel weights: `w_j = 1 - j / (max_lag + 1)`
  - Default lag: `floor(T^(1/3))`
  - Annualization: `sqrt(252 * 390)` for minute bars
  - Floor variance at `1e-10` to prevent negative values
- [x] Write `tests/unit/test_newey_west.py` with test cases from test plan
- [x] Verify: `pytest tests/unit/test_newey_west.py -v`

### Step 3 — Create Deflated Sharpe Ratio module (NW-03)
- [x] Create `src/validation/deflated_sr.py` implementing `deflated_sharpe_ratio(returns, n_trials, skew=None, kurtosis=None)`
  - Use `scipy.stats.norm` for CDF computation
  - Gumbel approximation for expected maximum Sharpe under null
  - Return DSR in [0, 1] range
- [x] Write `tests/unit/test_deflated_sr.py` with test cases from test plan
- [x] Verify: `pytest tests/unit/test_deflated_sr.py -v`
- [x] Ensure `scipy` is in pyproject.toml dependencies; add if missing

### Step 4 — Replace raw Sharpe in backtester with Newey-West (NW-04)
- [x] Open `src/core/backtester.py`, locate the Sharpe calculation in `calculate_metrics()` (or equivalent)
- [x] Add import: `from src.validation.newey_west import newey_west_sharpe`
- [x] Replace raw Sharpe calculation with `newey_west_sharpe(returns)`
- [x] Store raw Sharpe separately as `naive_sharpe` for output comparison
- [x] Update the SCORE output to report Newey-West Sharpe
- [x] Add NAIVE_SHARPE to output format
- [x] Compute NW_SHARPE_BIAS = NAIVE_SHARPE - SCORE (showing adjustment magnitude)

### Step 5 — Integrate Deflated SR into backtester output (NW-05)
- [x] Add import: `from src.validation.deflated_sr import deflated_sharpe_ratio`
- [x] Count `n_trials` from results.tsv (number of existing rows + 1 for current experiment)
- [x] If results.tsv does not exist or is empty, default `n_trials = 1`
- [x] Add DEFLATED_SR to output format after SCORE/NAIVE_SHARPE/NW_SHARPE_BIAS lines
- [x] Pass strategy returns and n_trials to `deflated_sharpe_ratio()`

### Step 6 — Remove Monte Carlo permutation test (NW-06)
- [x] Locate `monte_carlo_permutation_test` function in `src/core/backtester.py`
- [x] Delete the entire function
- [x] Remove P_VALUE from output format
- [x] Remove P_VALUE from results.tsv columns
- [x] Remove P_VALUE from decision logic (hard constraints)
- [x] Search for all references: `grep -rn "monte_carlo\|p_value\|P_VALUE\|permutation" src/core/backtester.py`
- [x] Clean any remaining references in cli.py or other files
- [x] Verify: `grep -rn "monte_carlo_permutation_test" src/ cli.py` returns 0 hits

### Step 7 — Update results.tsv format (NW-07)
- [x] Update results.tsv header to: `commit	score	naive_sharpe	deflated_sr	sortino	calmar	drawdown	max_dd_days	trades	win_rate	profit_factor	avg_win	avg_loss	baseline_sharpe	nw_bias	status	description`
- [x] Update the backtester's TSV writing logic to output new columns
- [x] Remove p_value column from TSV output

### Step 8 — Update hard constraints in program.md (NW-08, NW-09)
- [x] Remove P_VALUE constraint from decision rules
- [x] Retain: `if SCORE < BASELINE_SHARPE → DISCARD`
- [x] Add advisory: `if DEFLATED_SR < 0.5 → strategy may not be significant, proceed with caution`
- [x] Add advisory: `if NW_SHARPE_BIAS > 0.3 → serial correlation bias is large, investigate`
- [x] Add overfitting defense guidance section:
  - SCORE interpretation (NW-adjusted, usually lower than naive)
  - NW_SHARPE_BIAS meaning
  - When to use advanced validation (SCORE improvement > 0.05, parameter changes, every 5-10 experiments)
  - Red flags (NW_SHARPE_BIAS > 0.3, DSR < 0.5, CPCV % Positive < 50%, stability < 0.5)

### Step 9 — Write Sprint 1 tests (NW-10)
- [x] Write `tests/unit/test_backtester_overfit.py`:
  - `test_output_contains_naive_sharpe`
  - `test_output_contains_deflated_sr`
  - `test_output_contains_nw_bias`
  - `test_score_is_newey_west`
  - `test_no_p_value_in_output`
  - `test_no_monte_carlo_function`
  - `test_results_tsv_new_columns`
  - `test_nw_bias_calculation`
  - `test_baseline_constraint_retained`
- [x] Verify: `pytest tests/unit/test_backtester_overfit.py -v`

### Step 10 — Commit sprint 1 changes
- [x] `git add src/validation/ tests/unit/test_newey_west.py tests/unit/test_deflated_sr.py tests/unit/test_backtester_overfit.py`
- [x] `git add src/core/backtester.py cli.py` (if modified)
- [x] `git add program.md` (or `src/prompts/program.md` if that is the location)
- [x] `git commit -m "feat(overfit): add Newey-West Sharpe, Deflated SR, remove Monte Carlo"`

## 4) Test Plan

- [x] After Step 2: `pytest tests/unit/test_newey_west.py -v` — all NW Sharpe tests pass
- [x] After Step 3: `pytest tests/unit/test_deflated_sr.py -v` — all DSR tests pass
- [x] After Step 6: verify Monte Carlo fully removed:
  ```bash
  grep -rn "monte_carlo_permutation_test\|P_VALUE" src/core/backtester.py || echo "CLEAN"
  ```
- [x] After Step 9: `pytest tests/unit/test_newey_west.py tests/unit/test_deflated_sr.py tests/unit/test_backtester_overfit.py -v`
- [x] Full test suite: `pytest --tb=short -v`

## 5) Verification Commands

```bash
# Confirm validation module exists
test -f src/validation/__init__.py && echo "__init__.py OK"
test -f src/validation/newey_west.py && echo "newey_west.py OK"
test -f src/validation/deflated_sr.py && echo "deflated_sr.py OK"

# Confirm Monte Carlo removed
grep -rn "monte_carlo_permutation_test\|P_VALUE" src/core/backtester.py || echo "MONTE CARLO REMOVED"

# Confirm new output fields
grep -n "NAIVE_SHARPE\|DEFLATED_SR\|NW_SHARPE_BIAS" src/core/backtester.py

# Confirm test files exist
test -f tests/unit/test_newey_west.py && echo "test_newey_west.py OK"
test -f tests/unit/test_deflated_sr.py && echo "test_deflated_sr.py OK"
test -f tests/unit/test_backtester_overfit.py && echo "test_backtester_overfit.py OK"

# Run all tests
pytest --tb=short -v
```

## 6) Implementation Update Space

### Completed Work

- Added `src/validation/newey_west.py` with `newey_west_sharpe()` and `src/validation/deflated_sr.py` with `deflated_sharpe_ratio()`
- Migrated `src/core/backtester.py` to report Newey-West `SCORE`, `NAIVE_SHARPE`, `NW_SHARPE_BIAS`, and `DEFLATED_SR`
- Removed the Monte Carlo placeholder output and any `P_VALUE` / permutation references from the backtester contract
- Added `experiments/results.tsv` initialization and append logic with the Sprint 1 column layout
- Updated `program.md` to reflect the new decision rules, advisories, and experiment-output paths
- Added Sprint 1 QA coverage in `tests/unit/test_newey_west.py`, `tests/unit/test_deflated_sr.py`, `tests/unit/test_backtester_overfit.py`, and the logger/worktree regression in `tests/unit/test_logger_setup.py`
- Adjusted existing backtester expectations in `tests/unit/test_backtester_v2.py` to the new Sharpe contract

### Command Results

- `uv run pytest tests/unit/test_newey_west.py tests/unit/test_deflated_sr.py tests/unit/test_backtester_overfit.py -q` -> `23 passed in 0.69s`
- `uv run pytest --tb=short -q` -> `115 passed in 1.35s`
- `grep -rn "monte_carlo_permutation_test\\|P_VALUE" src/core/backtester.py || echo CLEAN` -> `CLEAN`
- `grep -n "NAIVE_SHARPE\\|DEFLATED_SR\\|NW_SHARPE_BIAS" src/core/backtester.py` -> lines `507-509`
- `ls src/validation/__init__.py src/validation/newey_west.py src/validation/deflated_sr.py` -> all expected Sprint 1 validation files present
- Implementation commit: `b910ac2`
- Sprint checklist sync commit: `ae58d3c`

### Blockers / Deviations

- `utils.logger` originally failed in clean worktrees because `experiments/logs/` was not created before `RotatingFileHandler` initialization; fixed in Sprint 1 because it blocked all QA collection
- `results.tsv` pathing was inconsistent across older docs (`results.tsv`) and the current runtime layout (`experiments/results.tsv`); Sprint 1 standardized on `experiments/results.tsv`
- Live issue-body / note / board updates are blocked in this workspace because `glab` is unavailable and the configured remotes do not expose issue `#12`

### Follow-ups

- Sprint 2: CPCV validation, regime check, parameter stability CLI commands, knowledge base notes
