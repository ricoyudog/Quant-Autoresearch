# Research: Turnover Reduction Confirmation Bars

## Decision 1: Keep the experiment strategy-local
- **Decision**: Implement the confirmation-bar experiment only in `src/strategies/active_strategy.py`.
- **Rationale**: The current question is whether a more conservative signal cadence improves the net result under the existing cost model. Changing the backtester, CLI, or data pipeline at the same time would make the outcome harder to attribute.
- **Alternatives considered**:
  - Inject regime or confirmation behavior from the backtester — rejected because it widens scope and changes the evaluation contract.
  - Add a separate strategy file for the experiment — rejected because the current V2 workflow centers the active strategy as the single strategy-under-test.

## Decision 2: Preserve the bear-volatile regime gate unchanged
- **Decision**: Keep the existing bear-volatile flattening rule as the highest-priority gate.
- **Rationale**: The most recent completed experiment (`f9661d8`) already improved bounded score, drawdown, and trade count by flattening exposure in hostile broad-market conditions. The next experiment should build on that baseline rather than reopen the same question.
- **Alternatives considered**:
  - Soften the hostile-regime rule while adding confirmation bars — rejected because it mixes two hypotheses.
  - Remove the regime gate to test confirmation bars alone — rejected because it would discard the current best baseline.

## Decision 3: Use fixed confirmation bars as the first turnover-reduction mechanism
- **Decision**: Require a fixed multi-bar confirmation sequence before non-hostile long or short exposure becomes tradable.
- **Rationale**: Confirmation bars are the smallest change that directly attacks fee-driven churn. They reduce reaction speed and flips without introducing additional moving thresholds or external state.
- **Alternatives considered**:
  - Minimum hold duration — rejected for the first pass because it can trap the strategy in bad positions longer.
  - Cooldown timer after each flip — rejected because it introduces another timing rule without first testing whether simple confirmation is enough.
  - Momentum-strength threshold / no-trade band — rejected because threshold tuning invites premature parameter search.

## Decision 4: Start with a single fixed baseline comparison surface
- **Decision**: Judge the experiment first on the existing bounded backtest comparison slice: `uv run python cli.py backtest --start 2025-01-01 --end 2025-03-31 --universe-size 5`.
- **Rationale**: This is the same surface used by the latest stable baseline and the bear-volatile experiment note. Reusing it preserves comparability and minimizes runtime cost.
- **Alternatives considered**:
  - Use the unrestricted universe first — rejected because it is slower and was explicitly left as a follow-up gap in earlier verification.
  - Change the comparison window immediately — rejected because it would weaken comparison to the current baseline.

## Decision 5: Keep the existing transaction-cost model as the authority
- **Decision**: Measure success under the current backtester transaction-cost assumptions only.
- **Rationale**: The user explicitly prioritized reducing turnover and drawdown under the existing fee model. Introducing a second cost model now would expand scope from design validation into scenario analysis.
- **Alternatives considered**:
  - Add a separate high-fee stress test to the first experiment — rejected because the primary question is whether the current cost-aware baseline improves.

## Decision 6: Define success in net terms, not raw-signal terms
- **Decision**: Evaluate the experiment primarily on net score, then trade count, then drawdown.
- **Rationale**: Turnover only matters because of its cost impact. A large drop in trades without acceptable net score behavior would not justify keeping the change.
- **Alternatives considered**:
  - Optimize trade count first — rejected because fewer trades alone do not prove a better strategy.
  - Optimize drawdown first — rejected because a lower drawdown that collapses net score would still be an unsound next baseline.
