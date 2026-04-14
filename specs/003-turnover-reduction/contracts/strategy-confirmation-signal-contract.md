# Contract: Strategy Confirmation Signal Experiment

## Purpose

Document the behavioral contract for the turnover-reduction experiment so implementation and testing stay aligned without changing the repository's broader runtime interfaces.

## Input Contract

### Daily Context Input
The strategy continues to receive the existing daily-bar context used for universe selection and broad-market regime assessment.

Expected behavioral guarantees:
- A broad-market proxy may be present or absent.
- If the proxy is absent or insufficient, the strategy falls back to neutral regime behavior.
- If the proxy indicates a hostile bear-volatile condition, the strategy must flatten all exposure regardless of raw minute-level momentum.

### Minute Context Input
The strategy continues to receive minute-bar frames using the current V2 backtester contract.

Expected behavioral guarantees:
- Raw directional momentum is still derived from the current minute-level momentum rule.
- A tradable long or short signal is allowed only after the fixed confirmation sequence is satisfied.
- Unconfirmed direction changes must remain flat.

## Output Contract

The strategy must emit the same signal-shape contract expected today:
- one aligned signal series per eligible ticker
- each series expresses long, short, or flat exposure only
- hostile regimes override confirmation and produce flat output

## Comparison Contract

The experiment must be judged on the same bounded evaluation slice as the latest stable baseline.

Required comparison outputs:
- net score under the current transaction-cost model
- trade count
- maximum drawdown

The experiment result must support one of three decisions:
- keep as the new baseline
- rework and retest
- reject and try a different turnover-reduction mechanism
