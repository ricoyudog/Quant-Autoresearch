# Sprint 2 — Backend Plan

> Feature: `v2-phase1`
> Role: Backend
> Derived from: #8 (Phase 1: Backtester + program.md + strategy interface) — interface + tests portion
> Last Updated: 2026-04-02

## 0) Governing Specs

1. `docs/upgrade-plan-v2.md` — Section 5 (program.md complete design), Section 8 (test plan), Section 3 (results.tsv format), Section 4 (Obsidian notes)
2. `docs/feature/v2-phase1/v2-phase1-development-plan.md` — Tasks PROG-01, STRAT-01, TEST-01, TEST-02, TEST-03, COMMIT-02

## 1) Sprint Mission

Create the root `program.md` file that serves as the complete instruction set for the Claude Code/Codex agent, remove the EDITABLE REGION markers from `active_strategy.py` to enable full-file modification, and write comprehensive tests for all new backtester functions and the strategy interface.

## 2) Scope / Out of Scope

**Scope**
- Write `program.md` at repository root (complete agent instruction file per Section 5 spec)
- Remove `# --- EDITABLE REGION BREAK ---` and `# --- EDITABLE REGION END ---` from `active_strategy.py`
- Create `tests/unit/test_backtester_v2.py` with tests for all new backtester functions
- Create `tests/unit/test_strategy_interface.py` with tests for dynamic loading and free-form strategy
- Run full test suite to verify everything passes

**Out of Scope**
- `results.tsv` creation or `experiments/notes/` directory — runtime concern, not code
- CLI simplification — Phase 3
- Obsidian vault setup — Phase 3
- Updating `CLAUDE.md` — Phase 4
- Deflated Sharpe Ratio — future session

## 3) Step-by-Step Plan

### Step 1 — Write root program.md (PROG-01)
- [ ] Create `program.md` at repository root
- [ ] Content follows `docs/upgrade-plan-v2.md` Section 5 spec exactly:
  - **Setup** section: run tag, branch creation, in-scope files, data verification, baseline run
  - **Experimentation** section: what CAN/CANNOT do, vectorized only, no shift(-N)
  - **The goal** section: highest SCORE (Average Walk-Forward OOS Sharpe)
  - **Output format** section: full YAML-like format with all 12 metrics + PER_SYMBOL block
  - **Decision rules** section: KEEP/DISCARD criteria, simplicity criterion
  - **Logging results** section: results.tsv format
  - **Obsidian experiment notes** section: note format and structure
  - **The experiment loop** section: NEVER STOP, 13-step loop
- [ ] Verify: `test -f program.md && wc -l program.md`

### Step 2 — Remove EDITABLE REGION markers (STRAT-01)
- [ ] Open `src/strategies/active_strategy.py`
- [ ] Remove line 23: `# --- EDITABLE REGION BREAK ---`
- [ ] Remove line 50: `# --- EDITABLE REGION END ---`
- [ ] Verify file still valid Python: `python -c "import ast; ast.parse(open('src/strategies/active_strategy.py').read()); print('VALID')"`
- [ ] Verify markers gone: `grep "EDITABLE REGION" src/strategies/active_strategy.py && echo "FAIL" || echo "OK"`
- [ ] Verify `TradingStrategy` class still intact: `grep "class TradingStrategy" src/strategies/active_strategy.py`

### Step 3 — Write tests/unit/test_backtester_v2.py (TEST-01)
- [ ] Create test file with the following test functions:

#### find_strategy_class tests
- [ ] `test_find_strategy_class_found` — mock class with generate_signals is found
- [ ] `test_find_strategy_class_not_found` — empty dict returns None
- [ ] `test_find_strategy_class_multiple` — first matching class returned
- [ ] `test_find_strategy_class_non_class_ignored` — functions/variables ignored

#### calculate_metrics tests
- [ ] `test_calculate_metrics_basic` — all 10 keys present in return dict
- [ ] `test_calculate_metrics_zero_std` — constant returns → sharpe=0, sortino=0
- [ ] `test_calculate_metrics_all_positive` — win_rate=1.0, avg_loss=0
- [ ] `test_calculate_metrics_all_negative` — win_rate=0.0, profit_factor=0
- [ ] `test_calculate_metrics_sortino_vs_sharpe` — sortino > sharpe for upside-skewed returns
- [ ] `test_calculate_metrics_calmar` — known return path gives expected calmar
- [ ] `test_calculate_metrics_drawdown` — known drawdown value
- [ ] `test_calculate_metrics_max_dd_days` — known drawdown duration
- [ ] `test_calculate_metrics_profit_factor` — known PF value
- [ ] `test_calculate_metrics_win_rate` — known WR value
- [ ] `test_calculate_metrics_avg_win_loss` — known avg values

#### calculate_baseline_sharpe tests
- [ ] `test_calculate_baseline_sharpe_basic` — multi-symbol dict returns positive float
- [ ] `test_calculate_baseline_sharpe_zero_std` — constant returns → 0.0
- [ ] `test_calculate_baseline_sharpe_single_symbol` — works with one symbol

#### run_per_symbol_analysis tests
- [ ] `test_run_per_symbol_analysis_basic` — returns dict with all symbols as keys
- [ ] `test_run_per_symbol_analysis_keys` — each symbol has sharpe, sortino, dd, pf, trades, wr
- [ ] `test_run_per_symbol_analysis_signal_lag` — signals shifted by 1 bar

#### Output format tests
- [ ] `test_output_format_has_all_metrics` — stdout contains all metric lines
- [ ] `test_output_format_has_per_symbol` — stdout contains PER_SYMBOL block

### Step 4 — Write tests/unit/test_strategy_interface.py (TEST-02)
- [ ] Create test file with the following test functions:

#### Dynamic loading tests
- [ ] `test_free_form_class_accepted` — custom class name works via find_strategy_class
- [ ] `test_custom_class_name` — "MomentumStrategy" loads correctly
- [ ] `test_multiple_methods_allowed` — class with generate_signals + helper methods
- [ ] `test_no_generate_signals_rejected` — class without generate_signals returns None
- [ ] `test_non_class_with_generate_signals_ignored` — function named generate_signals ignored

#### Strategy file tests
- [ ] `test_editable_region_removed` — no EDITABLE REGION in active_strategy.py
- [ ] `test_strategy_in_sandbox` — active_strategy.py compiles in RestrictedPython
- [ ] `test_strategy_returns_series` — generate_signals returns pd.Series for sample data
- [ ] `test_strategy_signal_range` — signals in {-1, 0, 1}
- [ ] `test_strategy_has_imports` — file has pandas and numpy imports

### Step 5 — Run full test suite (TEST-03)
- [ ] `pytest tests/unit/test_backtester_v2.py -v`
- [ ] `pytest tests/unit/test_strategy_interface.py -v`
- [ ] `pytest tests/unit/ -v --tb=short`
- [ ] All tests pass with 0 failures

### Step 6 — Commit Sprint 2 (COMMIT-02)
- [ ] `git add program.md src/strategies/active_strategy.py tests/unit/test_backtester_v2.py tests/unit/test_strategy_interface.py`
- [ ] `git commit -m "feat(v2-phase1): add program.md, remove EDITABLE REGION, add backtester and strategy tests"`

## 4) Test Plan

Tests are the deliverable of this sprint. Verification is that all tests pass:

```bash
# New tests
pytest tests/unit/test_backtester_v2.py tests/unit/test_strategy_interface.py -v

# Full suite (new + existing)
pytest --tb=short -v

# Quick smoke test — backtester end-to-end
uv run python src/core/backtester.py 2>&1 | grep "^SCORE:\|^SORTINO:\|^BASELINE_SHARPE:\|^PER_SYMBOL:"
```

## 5) Verification Commands

```bash
# program.md exists and is substantive
test -f program.md && wc -l program.md

# EDITABLE REGION gone
grep "EDITABLE REGION" src/strategies/active_strategy.py && echo "FAIL" || echo "MARKERS REMOVED"

# Test files exist
test -f tests/unit/test_backtester_v2.py && echo "backtester_v2 tests EXIST"
test -f tests/unit/test_strategy_interface.py && echo "strategy_interface tests EXIST"

# Count test functions
grep -c "def test_" tests/unit/test_backtester_v2.py
grep -c "def test_" tests/unit/test_strategy_interface.py

# Run all
pytest tests/unit/ --tb=short -q
```

## 6) Implementation Update Space

### Completed Work

_(To be filled during implementation)_

### Command Results

_(To be filled during implementation)_

### Blockers / Deviations

_(To be filled during implementation)_

### Follow-ups

- Phase 2 cleanup already completed (issues #1-#7)
- Phase 3: CLI simplification, Obsidian vault setup
- Future session: Deflated Sharpe Ratio to replace P_VALUE placeholder
