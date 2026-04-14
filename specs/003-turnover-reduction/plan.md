# Implementation Plan: Turnover Reduction Confirmation Bars

**Branch**: `[003-turnover-reduction]` | **Date**: 2026-04-14 | **Spec**: [`specs/003-turnover-reduction/spec.md`](./spec.md)
**Input**: Feature specification from `/specs/003-turnover-reduction/spec.md`

## Summary

Reduce fee-driven overtrading in the active minute-level momentum strategy by adding a fixed confirmation sequence to non-hostile trades while preserving the existing bear-volatile regime gate. The implementation stays strategy-local inside `src/strategies/active_strategy.py`, is validated test-first through `tests/unit/test_strategy_interface.py`, and is judged on the existing transaction-cost-aware bounded backtest surface.

## Technical Context

**Language/Version**: Python 3.10+ (repo guidance targets Python 3.12+ in active development)  
**Primary Dependencies**: pandas, numpy, pytest, RestrictedPython-compatible strategy surface, existing Typer CLI/backtester stack  
**Storage**: File-based repository artifacts (`src/strategies/active_strategy.py`, `experiments/results.tsv`, Obsidian vault notes) plus existing DuckDB daily cache input  
**Testing**: pytest unit tests plus bounded CLI backtest verification  
**Target Platform**: Local macOS/Linux developer environment running the existing V2 CLI and minute-data pipeline  
**Project Type**: Single-repository CLI research system with strategy module and test suite  
**Performance Goals**: Reduce transaction-cost-sensitive overtrading while keeping bounded backtest net score and drawdown acceptable relative to the latest stable baseline  
**Constraints**: No backtester or CLI contract changes; no new dependencies; preserve bear-volatile flattening; use the existing transaction-cost model as the evaluation authority  
**Scale/Scope**: One strategy-module experiment affecting the active strategy and its unit-test coverage, evaluated on the current bounded comparison slice (`2025-01-01..2025-03-31`, `--universe-size 5`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

There is no ratified Spec Kit constitution yet — `.specify/memory/constitution.md` still contains placeholders only — so repository policy is taken from AGENTS.md and the existing project guidance.

Pre-Phase-0 gates:
- **Test-first discipline** — PASS. Plan requires new/updated unit tests before strategy changes.
- **No new dependencies** — PASS. The experiment reuses existing pandas/numpy/pytest surfaces only.
- **Keep diffs small and reversible** — PASS. Scope is limited to the active strategy, tests, and planning artifacts.
- **Preserve evaluator authority** — PASS. Backtester, CLI contract, and transaction-cost model remain unchanged and serve as the decision surface.
- **Knowledge capture requirement** — PASS. Existing Obsidian experiment workflow is already in place and will be reused after implementation.

Post-Phase-1 re-check:
- **Design stays strategy-local** — PASS. Artifacts preserve a strategy-only change with no runtime contract expansion.
- **Scope remains bounded** — PASS. Threshold tuning, hold-duration logic, cooldowns, universe changes, and backtester changes remain out of scope.

## Project Structure

### Documentation (this feature)

```text
specs/003-turnover-reduction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── strategy-confirmation-signal-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── core/
│   └── backtester.py
├── strategies/
│   └── active_strategy.py
└── data/
    └── duckdb_connector.py

tests/
├── unit/
│   └── test_strategy_interface.py
├── integration/
│   └── test_minute_backtest.py
└── regression/
```

**Structure Decision**: Keep the implementation inside the existing single-project layout. The feature changes only the strategy module and its direct unit-test coverage, while relying on the already-existing CLI/backtester/integration surfaces for verification.

## Complexity Tracking

No constitution violations or complexity exceptions are required for this feature.
