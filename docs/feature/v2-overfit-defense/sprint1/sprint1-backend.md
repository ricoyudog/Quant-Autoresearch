# Sprint 1 — Backend Plan

> Feature: `v2-overfit-defense`
> Role: Backend
> Derived from: #12 (Umbrella: Session 3 Overfit Defense) — Layer 1 built-in defense
> Last Updated: 2026-04-02

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
- [ ] `git checkout -b feature/v2-overfit-defense main` (or from Phase 1 branch)
- [ ] Verify Phase 1 (issue #8) is complete: backtester has dynamic loading, multi-metric output, walk-forward 5 windows
- [ ] Run `pytest --tb=short -q` and record test count as baseline
- [ ] Verify `src/core/backtester.py` has `calculate_metrics()`, `calculate_baseline_sharpe()`, `run_per_symbol_analysis()` functions

### Step 2 — Create validation module with Newey-West Sharpe (NW-02)
- [ ] Create `src/validation/__init__.py`
- [ ] Create `src/validation/newey_west.py` implementing `newey_west_sharpe(returns, max_lag=None)`
  - Use Bartlett kernel weights: `w_j = 1 - j / (max_lag + 1)`
  - Default lag: `floor(T^(1/3))`
  - Annualization: `sqrt(252 * 390)` for minute bars
  - Floor variance at `1e-10` to prevent negative values
- [ ] Write `tests/unit/test_newey_west.py` with test cases from test plan
- [ ] Verify: `pytest tests/unit/test_newey_west.py -v`

### Step 3 — Create Deflated Sharpe Ratio module (NW-03)
- [ ] Create `src/validation/deflated_sr.py` implementing `deflated_sharpe_ratio(returns, n_trials, skew=None, kurtosis=None)`
  - Use `scipy.stats.norm` for CDF computation
  - Gumbel approximation for expected maximum Sharpe under null
  - Return DSR in [0, 1] range
- [ ] Write `tests/unit/test_deflated_sr.py` with test cases from test plan
- [ ] Verify: `pytest tests/unit/test_deflated_sr.py -v`
- [ ] Ensure `scipy` is in pyproject.toml dependencies; add if missing

### Step 4 — Replace raw Sharpe in backtester with Newey-West (NW-04)
- [ ] Open `src/core/backtester.py`, locate the Sharpe calculation in `calculate_metrics()` (or equivalent)
- [ ] Add import: `from src.validation.newey_west import newey_west_sharpe`
- [ ] Replace raw Sharpe calculation with `newey_west_sharpe(returns)`
- [ ] Store raw Sharpe separately as `naive_sharpe` for output comparison
- [ ] Update the SCORE output to report Newey-West Sharpe
- [ ] Add NAIVE_SHARPE to output format
- [ ] Compute NW_SHARPE_BIAS = NAIVE_SHARPE - SCORE (showing adjustment magnitude)

### Step 5 — Integrate Deflated SR into backtester output (NW-05)
- [ ] Add import: `from src.validation.deflated_sr import deflated_sharpe_ratio`
- [ ] Count `n_trials` from results.tsv (number of existing rows + 1 for current experiment)
- [ ] If results.tsv does not exist or is empty, default `n_trials = 1`
- [ ] Add DEFLATED_SR to output format after SCORE/NAIVE_SHARPE/NW_SHARPE_BIAS lines
- [ ] Pass strategy returns and n_trials to `deflated_sharpe_ratio()`

### Step 6 — Remove Monte Carlo permutation test (NW-06)
- [ ] Locate `monte_carlo_permutation_test` function in `src/core/backtester.py`
- [ ] Delete the entire function
- [ ] Remove P_VALUE from output format
- [ ] Remove P_VALUE from results.tsv columns
- [ ] Remove P_VALUE from decision logic (hard constraints)
- [ ] Search for all references: `grep -rn "monte_carlo\|p_value\|P_VALUE\|permutation" src/core/backtester.py`
- [ ] Clean any remaining references in cli.py or other files
- [ ] Verify: `grep -rn "monte_carlo_permutation_test" src/ cli.py` returns 0 hits

### Step 7 — Update results.tsv format (NW-07)
- [ ] Update results.tsv header to: `commit	score	naive_sharpe	deflated_sr	sortino	calmar	drawdown	max_dd_days	trades	win_rate	profit_factor	avg_win	avg_loss	baseline_sharpe	nw_bias	status	description`
- [ ] Update the backtester's TSV writing logic to output new columns
- [ ] Remove p_value column from TSV output

### Step 8 — Update hard constraints in program.md (NW-08, NW-09)
- [ ] Remove P_VALUE constraint from decision rules
- [ ] Retain: `if SCORE < BASELINE_SHARPE → DISCARD`
- [ ] Add advisory: `if DEFLATED_SR < 0.5 → strategy may not be significant, proceed with caution`
- [ ] Add advisory: `if NW_SHARPE_BIAS > 0.3 → serial correlation bias is large, investigate`
- [ ] Add overfitting defense guidance section:
  - SCORE interpretation (NW-adjusted, usually lower than naive)
  - NW_SHARPE_BIAS meaning
  - When to use advanced validation (SCORE improvement > 0.05, parameter changes, every 5-10 experiments)
  - Red flags (NW_SHARPE_BIAS > 0.3, DSR < 0.5, CPCV % Positive < 50%, stability < 0.5)

### Step 9 — Write Sprint 1 tests (NW-10)
- [ ] Write `tests/unit/test_backtester_overfit.py`:
  - `test_output_contains_naive_sharpe`
  - `test_output_contains_deflated_sr`
  - `test_output_contains_nw_bias`
  - `test_score_is_newey_west`
  - `test_no_p_value_in_output`
  - `test_no_monte_carlo_function`
  - `test_results_tsv_new_columns`
  - `test_nw_bias_calculation`
  - `test_baseline_constraint_retained`
- [ ] Verify: `pytest tests/unit/test_backtester_overfit.py -v`

### Step 10 — Commit sprint 1 changes
- [ ] `git add src/validation/ tests/unit/test_newey_west.py tests/unit/test_deflated_sr.py tests/unit/test_backtester_overfit.py`
- [ ] `git add src/core/backtester.py cli.py` (if modified)
- [ ] `git add program.md` (or `src/prompts/program.md` if that is the location)
- [ ] `git commit -m "feat(overfit): add Newey-West Sharpe, Deflated SR, remove Monte Carlo"`

## 4) Test Plan

- [ ] After Step 2: `pytest tests/unit/test_newey_west.py -v` — all NW Sharpe tests pass
- [ ] After Step 3: `pytest tests/unit/test_deflated_sr.py -v` — all DSR tests pass
- [ ] After Step 6: verify Monte Carlo fully removed:
  ```bash
  grep -rn "monte_carlo_permutation_test\|P_VALUE" src/core/backtester.py || echo "CLEAN"
  ```
- [ ] After Step 9: `pytest tests/unit/test_newey_west.py tests/unit/test_deflated_sr.py tests/unit/test_backtester_overfit.py -v`
- [ ] Full test suite: `pytest --tb=short -v`

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

*(To be filled during implementation)*

### Command Results

*(To be filled during implementation)*

### Blockers / Deviations

*(To be filled during implementation)*

### Follow-ups

- Sprint 2: CPCV validation, regime check, parameter stability CLI commands, knowledge base notes
