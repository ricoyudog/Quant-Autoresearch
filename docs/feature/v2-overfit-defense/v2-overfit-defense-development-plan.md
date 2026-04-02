# V2 Overfit Defense — Development Plan

> Feature branch: `feature/v2-overfit-defense`
> Umbrella issue: #12
> Canonical root: `docs/feature/v2-overfit-defense/`
> Dependency: Phase 1 (issue #8) must be complete

## Context

The V2 overfit defense architecture replaces naive statistical tests with academically rigorous methods from Lopez de Prado, Bailey, and Harvey et al. The defense operates in three layers:

- **Layer 1 — Built-in (every backtest):** Newey-West Sharpe replaces raw Sharpe to correct for minute-bar serial correlation. Deflated Sharpe Ratio adjusts for multiple testing. Monte Carlo permutation test is removed (replaced by DSR). Walk-forward 5 windows, forced 1-bar lag, volatility-adjusted slippage, and AST safety checks are retained.
- **Layer 2 — On-demand (CLI commands):** CPCV combinatorial cross-validation, regime robustness analysis, and parameter stability testing. The agent invokes these when conditions warrant deeper validation.
- **Layer 3 — Guidance (program.md):** Simplicity criterion, red flags, and usage instructions for advanced tools.

## Files to Create

### Validation module
| File | Purpose |
| --- | --- |
| `src/validation/__init__.py` | Validation module exports |
| `src/validation/newey_west.py` | Newey-West adjusted Sharpe Ratio calculation |
| `src/validation/deflated_sr.py` | Deflated Sharpe Ratio calculation |

### CLI validation commands (Sprint 2)
| File | Purpose |
| --- | --- |
| `src/validation/cpcv.py` | Combinatorial Purged Cross-Validation |
| `src/validation/regime.py` | Regime robustness analysis |
| `src/validation/stability.py` | Parameter stability testing |

## Files to Modify

### Backtester (Sprint 1)
| File | Changes |
| --- | --- |
| `src/core/backtester.py` | Replace raw Sharpe with Newey-West; add Deflated SR output; remove `monte_carlo_permutation_test`; update output format with NAIVE_SHARPE, DEFLATED_SR, NW_SHARPE_BIAS; update results.tsv columns |

### CLI (Sprint 2)
| File | Changes |
| --- | --- |
| `cli.py` | Add `validate` sub-command with `--method` flag (cpcv, regime, stability) |

### Prompts (Sprint 1)
| File | Changes |
| --- | --- |
| `src/prompts/program.md` (or root `program.md`) | Add overfitting defense guidance section: SCORE interpretation, when to use advanced validation, red flags |

## Files to Keep Unchanged

- `src/data/connector.py` — data loading
- `src/data/preprocessor.py` — data preprocessing
- `src/strategies/active_strategy.py` — strategy file
- All surviving utility files (logger, telemetry, iteration_tracker, retries)

## Sprint Plan

| Sprint | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 1 — Built-in Defense | Newey-West Sharpe + Deflated SR + remove Monte Carlo | backtester.py updated, validation/newey_west.py, validation/deflated_sr.py, output format updated, program.md guidance added | pending | proceed to Sprint 2 |
| Sprint 2 — Advanced Validation CLI | CPCV + Regime check + Parameter stability CLI commands | validation/cpcv.py, validation/regime.py, validation/stability.py, cli.py validate command, tests for all CLI commands, knowledge base notes | pending | merge readiness |

## Task Table

### Sprint 1 Tasks

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| NW-01 | Create `feature/v2-overfit-defense` branch from Phase 1 complete state | Dev | Phase 1 done | 0.1d | branch exists, tests green |
| NW-02 | Create `src/validation/__init__.py` and `src/validation/newey_west.py` | Dev | NW-01 | 0.2d | `newey_west_sharpe()` function works, unit test passes |
| NW-03 | Create `src/validation/deflated_sr.py` | Dev | NW-01 | 0.2d | `deflated_sharpe_ratio()` function works, unit test passes |
| NW-04 | Replace raw Sharpe in `backtester.py` with `newey_west_sharpe()` | Dev | NW-02 | 0.2d | SCORE now reports Newey-West Sharpe; NAIVE_SHARPE shows raw value |
| NW-05 | Integrate Deflated SR into backtester output | Dev | NW-03, NW-04 | 0.1d | DEFLATED_SR and NW_SHARPE_BIAS appear in output; n_trials read from results.tsv |
| NW-06 | Remove `monte_carlo_permutation_test` from `backtester.py` | Dev | NW-04 | 0.1d | function removed, no P_VALUE in output, no references remain |
| NW-07 | Update results.tsv format to include new columns | Dev | NW-05, NW-06 | 0.1d | Header: commit, score, naive_sharpe, deflated_sr, sortino, calmar, drawdown, max_dd_days, trades, win_rate, profit_factor, avg_win, avg_loss, baseline_sharpe, nw_bias, status, description |
| NW-08 | Update hard constraints in program.md | Dev | NW-06 | 0.1d | P_VALUE constraint removed; SCORE < BASELINE_SHARPE constraint retained; DSR advisory guidance added |
| NW-09 | Add overfitting defense guidance to program.md | Dev | NW-08 | 0.1d | Section on SCORE interpretation, when to use advanced tools, red flags |
| NW-10 | Sprint 1 tests: Newey-West, Deflated SR, updated backtester output | Dev | NW-07 | 0.3d | all new tests pass |

### Sprint 2 Tasks

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| CLI-01 | Create `src/validation/cpcv.py` | Dev | NW-04 | 0.3d | `run_cpcv()` function works; C(N,k) path generation correct |
| CLI-02 | Create `src/validation/regime.py` | Dev | NW-02 | 0.2d | `regime_analysis()` classifies 4 regimes; uses Newey-West Sharpe per regime |
| CLI-03 | Create `src/validation/stability.py` | Dev | NW-01 | 0.3d | `parameter_stability_test()` extracts params from strategy class; perturbation sweep works |
| CLI-04 | Add `validate` sub-command to `cli.py` | Dev | CLI-01, CLI-02, CLI-03 | 0.2d | `uv run python cli.py validate --method cpcv\|regime\|stability` works |
| CLI-05 | Write tests for CPCV validation | Dev | CLI-01 | 0.2d | test C(8,2)=28 paths; test purging; test output format |
| CLI-06 | Write tests for regime check | Dev | CLI-02 | 0.2d | test 4 regime classification; test per-regime Sharpe; test edge cases |
| CLI-07 | Write tests for parameter stability | Dev | CLI-03 | 0.2d | test param extraction; test perturbation range; test stability score |
| CLI-08 | Write tests for CLI validate command | Dev | CLI-04 | 0.1d | test each method flag; test invalid method; test missing data |
| CLI-09 | Write knowledge base notes on overfit defense | Dev | CLI-01, CLI-02, CLI-03 | 0.2d | notes cover NW Sharpe, DSR, CPCV, regime, stability with references |
| CLI-10 | Sprint 2 full integration test | Dev | CLI-04 through CLI-09 | 0.1d | `pytest` green; manual CLI smoke test passes |

## Acceptance Criteria

- [ ] `feature/v2-overfit-defense` branch exists
- [ ] `src/validation/` module created with 5 files (__init__, newey_west, deflated_sr, cpcv, regime, stability)
- [ ] Backtester SCORE reports Newey-West adjusted Sharpe (not raw Sharpe)
- [ ] Backtester output includes NAIVE_SHARPE, DEFLATED_SR, NW_SHARPE_BIAS
- [ ] `monte_carlo_permutation_test` removed from backtester.py
- [ ] P_VALUE removed from output format
- [ ] `uv run python cli.py validate --method cpcv` works
- [ ] `uv run python cli.py validate --method regime` works
- [ ] `uv run python cli.py validate --method stability` works
- [ ] `pytest` passes with 0 failures
- [ ] program.md contains overfitting defense guidance section

## Verification Commands

```bash
# Verify new module exists
ls src/validation/__init__.py src/validation/newey_west.py src/validation/deflated_sr.py

# Verify Monte Carlo removed
grep -rn "monte_carlo_permutation_test\|P_VALUE" src/core/backtester.py || echo "MONTE CARLO REMOVED"

# Verify new output fields
grep -n "NAIVE_SHARPE\|DEFLATED_SR\|NW_SHARPE_BIAS" src/core/backtester.py

# Verify CLI commands
uv run python cli.py validate --method cpcv --groups 6 --test-groups 1
uv run python cli.py validate --method regime
uv run python cli.py validate --method stability --perturbation 0.2 --steps 5

# Run all tests
pytest --tb=short -v
```

## Risks

| Risk | Mitigation |
| --- | --- |
| Phase 1 (issue #8) not complete: backtester lacks dynamic loading or multi-metric output | Block Sprint 1 start; verify Phase 1 acceptance criteria first |
| `scipy.stats.norm` not in dependencies | Add `scipy` to pyproject.toml if missing |
| CPCV computation too slow for large datasets | Default to C(6,1)=6 paths; document C(8,2)=28 as recommended |
| results.tsv does not exist yet for n_trials counting | Default n_trials=1 if file missing; log warning |
| Strategy class has no numeric __init__ params for stability test | Return "no tuneable parameters found" message; stability=1.0 by convention |
