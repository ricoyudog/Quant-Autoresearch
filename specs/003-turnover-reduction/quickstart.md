# Quickstart: Turnover Reduction Confirmation Bars

## Purpose

Use this workflow to implement and verify the confirmation-bar experiment against the current stable regime-gated baseline.

## Prerequisites

- Repository root: `/Users/chunsingyu/softwares/Quant-Autoresearch`
- Active branch: `003-turnover-reduction`
- Existing stable baseline references:
  - runtime repair commit `456cbed`
  - bear-volatile regime-gate commit `f9661d8`
- Daily cache available at `data/daily_cache.duckdb`

## Verification Workflow

1. Implement the confirmation-bar rule only in `src/strategies/active_strategy.py`.
2. Add or update unit tests in `tests/unit/test_strategy_interface.py` first.
3. Run focused strategy-interface verification:
   ```bash
   uv run pytest tests/unit/test_strategy_interface.py -q
   ```
4. Check strategy syntax and diff hygiene:
   ```bash
   uv run python -m compileall src/strategies/active_strategy.py
   git diff --check
   ```
5. Run the bounded comparison backtest:
   ```bash
   uv run python cli.py backtest --start 2025-01-01 --end 2025-03-31 --universe-size 5
   ```
6. Compare the result to the current stable bounded baseline:
   - SCORE: `-24.5034`
   - DRAWDOWN: `-0.5991`
   - TRADES: `4914`

## Keep / Rework Heuristic

Treat the experiment as promising when:
- net score does not materially worsen relative to the current stable baseline
- trade count drops meaningfully
- drawdown does not deteriorate

If trade count barely moves, drawdown worsens, or net score collapses, prefer rework or rejection before adding more complexity.

## Success-Criteria Decision Checklist

Use the current stable bounded baseline as the comparison source:
- baseline SCORE: `-24.5034`
- baseline DRAWDOWN: `-0.5991`
- baseline TRADES: `4914`

Mark the experiment outcome explicitly:
- **SC-001 PASS** if TRADES are `<= 3931` (at least 20% lower than baseline)
- **SC-002 PASS** if SCORE is `>= -26.9538` (does not worsen by more than 10% relative to baseline magnitude)
- **SC-003 PASS** if DRAWDOWN is `>= -0.5991` (not worse than baseline drawdown)
- **SC-004 PASS** if hostile-regime tests still show flat exposure for all affected symbols

Decision guide:
- **Keep** when SC-001, SC-003, and SC-004 pass and SC-002 does not fail
- **Rework** when turnover improves but score or drawdown meaningfully regress
- **Reject** when turnover barely changes or the bounded result is broadly worse than baseline

## Knowledge Capture

After verification, update the Obsidian experiment trail:
- add or update a note under `quant-autoresearch/experiments/`
- record the baseline, commands, metrics, decision, and next experiment
- update `experiment-index.md` if the baseline changes

## Latest Local Evidence

Latest local verification on 2026-04-14:

- `uv run pytest tests/unit/test_strategy_interface.py -q` -> `30 passed`
- `uv run pytest tests/unit/test_backtester_v2.py -q -k 'runs_default_active_strategy_in_sandbox'` -> `1 passed`
- `uv run python cli.py backtest --start 2025-01-01 --end 2025-03-31 --universe-size 5` -> completed with:
  - SCORE `-19.1477`
  - DRAWDOWN `-0.5641`
  - TRADES `2374`
