# Data Model: Turnover Reduction Confirmation Bars

## MarketRegimeState
- **Purpose**: Represents the broad-market condition that controls whether the strategy is allowed to trade normally.
- **Source**: Existing SPY daily-context classification inside the active strategy.
- **States**:
  - `neutral` — non-hostile default behavior
  - `bear_volatile` — hostile condition that forces flat exposure
- **Validation Rules**:
  - Must default to `neutral` when proxy data is unavailable or insufficient
  - Must take precedence over any confirmation or momentum signal

## RawMomentumDirection
- **Purpose**: Captures the immediate directional reading before confirmation is applied.
- **Values**:
  - `long`
  - `short`
  - `flat`
- **Derived From**:
  - The active strategy's existing 20-bar momentum comparison
- **Validation Rules**:
  - Must remain flat when there is insufficient price history
  - Must not become a tradable position until confirmation passes

## ConfirmationWindow
- **Purpose**: Represents the fixed number of consecutive bars required before a non-hostile raw signal becomes tradable.
- **Attributes**:
  - `length` — fixed positive integer used consistently across the strategy
  - `direction` — the raw directional sign being confirmed
- **Validation Rules**:
  - Must require the same direction for the full window
  - Any interruption resets confirmation to flat

## ConfirmedExposureSignal
- **Purpose**: The final long, short, or flat output consumed by the existing backtester.
- **Values**:
  - `long`
  - `short`
  - `flat`
- **State Transitions**:
  - `flat` -> `long` after enough consecutive long raw signals in a non-hostile regime
  - `flat` -> `short` after enough consecutive short raw signals in a non-hostile regime
  - `long`/`short` -> `flat` when confirmation breaks or hostile regime takes priority
  - any state -> `flat` immediately when `MarketRegimeState = bear_volatile`
- **Validation Rules**:
  - Must preserve both long and short capability outside hostile regimes
  - Must remain flat throughout hostile-regime intervals

## BaselineComparisonRecord
- **Purpose**: Provides the measurable reference used to decide whether the experiment is worth keeping.
- **Attributes**:
  - `comparison_slice`
  - `net_score`
  - `trade_count`
  - `max_drawdown`
  - `baseline_commit`
- **Validation Rules**:
  - Must be produced on the same bounded evaluation slice used by the stable baseline
  - Must be interpretable under the current transaction-cost model
