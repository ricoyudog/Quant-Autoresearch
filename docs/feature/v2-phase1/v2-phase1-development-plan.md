# V2 Phase 1 — Development Plan

> Feature branch: `feature/v2-phase1`
> Umbrella issue: #8
> Canonical root: `docs/feature/v2-phase1/`

## Context

The V2 architecture replaces the Python-controlled 6-Phase OPENDEV loop with a `program.md`-driven approach where Claude Code/Codex autonomously runs the experiment loop. Phase 1 builds the foundation: upgrading the backtester to produce rich multi-metric output, creating the `program.md` instruction file that drives the agent, and removing the EDITABLE REGION constraint so the agent can modify the entire strategy file.

The V2 cleanup (Phase 2, issues #1-#7) has already removed all V1 Python framework code. This phase operates on the surviving codebase.

## Current State

### backtester.py (271 lines)

Has:
- `security_check()` — AST-based security analysis
- `is_negative_val()` — helper for AST negative value detection
- `load_data()` — loads cached Parquet data via DataConnector
- `monte_carlo_permutation_test()` — permutation test for statistical significance
- `run_backtest()` — single-window backtest with Sharpe, Drawdown, Trades, P-Value
- `walk_forward_validation()` — 5-window walk-forward with hardcoded `TradingStrategy` class name

Missing:
- `find_strategy_class()` — dynamic class discovery (replaces hardcoded "TradingStrategy" at line 219)
- `calculate_metrics()` — full 10-metric calculation (Sortino, Calmar, Profit Factor, Win Rate, etc.)
- `calculate_baseline_sharpe()` — Buy&Hold baseline Sharpe
- `run_per_symbol_analysis()` — per-symbol breakdown output

Output format: only SCORE, DRAWDOWN, TRADES, P-VALUE (4 metrics)

### active_strategy.py (52 lines)

Has EDITABLE REGION BREAK (line 23) and EDITABLE REGION END (line 50) markers. V2 removes these markers; the entire file is modifiable by the agent.

### program.md

Does not exist yet. Must be created at repository root with the complete agent instruction set.

## Files to Modify

| File | Change | Sprint |
| --- | --- | --- |
| `src/core/backtester.py` | Major: add 4 functions, update output format, remove monte_carlo_permutation_test | Sprint 1 |
| `program.md` | New: root-level agent instruction file | Sprint 2 |
| `src/strategies/active_strategy.py` | Minor: remove EDITABLE REGION markers | Sprint 2 |

## Files to Create

| File | Purpose | Sprint |
| --- | --- | --- |
| `program.md` | Agent instruction file (research loop, constraints, output format) | Sprint 2 |
| `tests/unit/test_backtester_v2.py` | Tests for new backtester functions | Sprint 2 |
| `tests/unit/test_strategy_interface.py` | Tests for dynamic class loading and free-form strategy | Sprint 2 |

## Files to Remove

| File | Reason | Sprint |
| --- | --- | --- |
| (none — this is an additive/refactor phase) | | |

## Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 1 — Backtester Core | Upgrade backtester.py with new metrics and dynamic loading | 4 new functions, updated output format, removed monte_carlo | pending | proceed to program.md |
| Sprint 2 — Interface + Tests | Create program.md, remove EDITABLE REGION, add tests | program.md, clean strategy file, 2 test files | pending | merge readiness |

## Task Table

| Task ID | Task | Sprint | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| BT-01 | Create `feature/v2-phase1` branch | Sprint 1 | none | 0.05d | branch exists, tests green on main |
| BT-02 | Add `find_strategy_class()` | Sprint 1 | BT-01 | 0.1d | function works, replaces hardcoded class name |
| BT-03 | Add `calculate_metrics()` with 10 metrics | Sprint 1 | BT-01 | 0.3d | all 10 metrics computed correctly |
| BT-04 | Add `calculate_baseline_sharpe()` | Sprint 1 | BT-01 | 0.1d | Buy&Hold Sharpe computed correctly |
| BT-05 | Add `run_per_symbol_analysis()` | Sprint 1 | BT-01 | 0.2d | per-symbol breakdown output matches spec |
| BT-06 | Update `walk_forward_validation()` output format | Sprint 1 | BT-02..BT-05 | 0.1d | output matches YAML-like format in Section 2.1 |
| BT-07 | Remove `monte_carlo_permutation_test()` | Sprint 1 | BT-06 | 0.05d | function removed, P_VALUE still in output (placeholder 0.0) |
| BT-08 | Commit Sprint 1 | Sprint 1 | BT-02..BT-07 | 0.05d | all backtester changes committed |
| PROG-01 | Write root `program.md` | Sprint 2 | BT-06 | 0.3d | file matches Section 5 spec |
| STRAT-01 | Remove EDITABLE REGION markers from `active_strategy.py` | Sprint 2 | BT-01 | 0.05d | markers gone, file intact |
| TEST-01 | Write `tests/unit/test_backtester_v2.py` | Sprint 2 | BT-02..BT-07 | 0.3d | tests for all new functions |
| TEST-02 | Write `tests/unit/test_strategy_interface.py` | Sprint 2 | BT-02, STRAT-01 | 0.2d | tests for dynamic loading + free-form strategy |
| TEST-03 | Full test run | Sprint 2 | TEST-01, TEST-02 | 0.1d | `pytest` passes with 0 failures |
| COMMIT-02 | Commit Sprint 2 | Sprint 2 | TEST-03 | 0.05d | all changes committed |

## Acceptance Criteria

- [ ] `feature/v2-phase1` branch exists
- [ ] `find_strategy_class()` replaces hardcoded "TradingStrategy" at line 219
- [ ] `calculate_metrics()` returns all 10 metrics (Sharpe, Sortino, Calmar, Drawdown, Max DD Days, Trades, Win Rate, Profit Factor, Avg Win, Avg Loss)
- [ ] `calculate_baseline_sharpe()` computes Buy&Hold Sharpe
- [ ] `run_per_symbol_analysis()` produces per-symbol breakdown
- [ ] Output format matches Section 2.1 spec (YAML-like with PER_SYMBOL block)
- [ ] `monte_carlo_permutation_test()` removed from backtester.py
- [ ] `program.md` exists at repository root
- [ ] EDITABLE REGION markers removed from `active_strategy.py`
- [ ] `tests/unit/test_backtester_v2.py` covers all new functions
- [ ] `tests/unit/test_strategy_interface.py` covers dynamic loading
- [ ] `pytest` passes with 0 failures

## Verification Commands

```bash
# Verify new functions exist
grep -n "def find_strategy_class\|def calculate_metrics\|def calculate_baseline_sharpe\|def run_per_symbol_analysis" src/core/backtester.py

# Verify monte_carlo removed
grep -n "def monte_carlo_permutation_test" src/core/backtester.py && echo "FAIL: still present" || echo "OK: removed"

# Verify EDITABLE REGION removed
grep -n "EDITABLE REGION" src/strategies/active_strategy.py && echo "FAIL: markers present" || echo "OK: markers removed"

# Verify program.md exists
test -f program.md && echo "OK: program.md exists" || echo "FAIL: missing"

# Verify test files exist
test -f tests/unit/test_backtester_v2.py && echo "OK: backtester tests exist"
test -f tests/unit/test_strategy_interface.py && echo "OK: strategy interface tests exist"

# Run tests
pytest tests/unit/test_backtester_v2.py tests/unit/test_strategy_interface.py -v
```

## Risks

| Risk | Mitigation |
| --- | --- |
| `calculate_metrics()` edge cases (zero std, empty trades) | Explicit zero-division guards in every calculation |
| Removing monte_carlo changes P_VALUE semantics | Document that P_VALUE is placeholder (Deflated SR in future session) |
| program.md content drift from Section 5 spec | Validate against upgrade-plan-v2.md Section 5 |
| EDITABLE REGION removal breaks existing tests | Sprint 2 tests validate the new interface |
| walk_forward_validation output format change breaks downstream parsers | New format is the canonical V2 format |
