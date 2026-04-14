# Feature Specification: Turnover Reduction Confirmation Bars

**Feature Branch**: `[003-turnover-reduction]`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Reduce turnover and drawdown in the current minute-level momentum strategy by adding confirmation bars under the existing transaction-cost model while preserving the bear-volatile regime gate."

## Clarifications

### Session 2026-04-14

- Q: How long should the fixed confirmation sequence be? → A: 3 bars
- Q: How should confirmed reversals behave? → A: Go flat first, then require a fresh 3-bar confirmation before taking the opposite side
- Q: What counts as the formal keep gate? → A: The bounded comparison slice is sufficient for a keep decision; unrestricted runs are follow-up evidence

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reduce fee-driven overtrading (Priority: P1)

As a strategy researcher, I want the active minute-level momentum strategy to wait for multi-bar confirmation before taking non-hostile trades so that unnecessary reversals and transaction-cost drag are reduced.

**Why this priority**: The current strategy is still losing heavily after costs, and the most immediate problem is excessive trade frequency rather than missing new alpha sources.

**Independent Test**: Run the confirmation-bar variant against the latest stable baseline on the same evaluation slice and confirm that trade count drops while the net score remains acceptable for further iteration.

**Acceptance Scenarios**:

1. **Given** a non-hostile market regime, **When** raw momentum changes direction for fewer than 3 consecutive bars, **Then** the strategy remains flat instead of opening or reversing a position.
2. **Given** a non-hostile market regime, **When** raw momentum holds the same direction for 3 consecutive bars, **Then** the strategy emits a tradable position in that direction.

---

### User Story 2 - Preserve hostile-regime protection (Priority: P2)

As a strategy researcher, I want the existing hostile-regime flattening rule to remain in force so that turnover-reduction work does not reintroduce exposure during bear-volatile market conditions.

**Why this priority**: The current risk improvement depends on hostile regimes staying flat; a turnover filter is only useful if it preserves that protection.

**Independent Test**: Force a hostile-regime context and confirm that the strategy still produces flat exposure even when raw momentum would otherwise satisfy confirmation.

**Acceptance Scenarios**:

1. **Given** the broad market is classified as bear-volatile, **When** minute-level momentum repeatedly confirms a long or short direction, **Then** the strategy still outputs flat exposure for that interval.
2. **Given** broad-market proxy data is unavailable or insufficient, **When** the strategy prepares to trade, **Then** it falls back to neutral behavior rather than blocking all trading.

---

### User Story 3 - Produce a clean next-step decision (Priority: P3)

As a future researcher, I want this experiment to be directly comparable with the latest stable baseline so that I can decide whether to keep, refine, or reject the confirmation-bar approach before adding more complexity.

**Why this priority**: The project needs a disciplined improvement trail, not stacked changes whose effects cannot be separated.

**Independent Test**: Compare the experiment output against the current stable baseline using the same evaluation slice and cost assumptions, then verify that the result can be classified as keep, rework, or reject using explicit metrics.

**Acceptance Scenarios**:

1. **Given** a recorded stable baseline, **When** the confirmation-bar experiment is evaluated on the same bounded comparison slice, **Then** the researcher can directly compare net score, drawdown, and trade count without translation or re-interpretation.
2. **Given** the comparison is complete, **When** the outcome is reviewed, **Then** the result supports a clear decision about whether the confirmation-bar approach should become the new baseline.

### Edge Cases

- What happens when the strategy has insufficient history to compute the 20-bar raw momentum signal or the full confirmation window?
- How does the strategy behave when raw momentum alternates direction too quickly to satisfy confirmation?
- What happens when SPY or equivalent broad-market proxy data is missing from the available daily context?
- How does the strategy behave when a hostile regime persists while individual symbols continue to generate strong directional raw momentum?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The strategy MUST preserve the existing bear-volatile regime gate as the highest-priority exposure rule.
- **FR-002**: The strategy MUST require a fixed 3-bar confirmation sequence before taking a non-hostile long or short position.
- **FR-003**: The strategy MUST treat unconfirmed or rapidly reversing raw momentum as flat exposure, and it MUST require a fresh 3-bar confirmation before taking the opposite side after a contradiction.
- **FR-004**: The strategy MUST continue to support both long and short exposure outside hostile regimes once confirmation is satisfied.
- **FR-005**: The strategy MUST default to neutral regime behavior when broad-market proxy data is unavailable or insufficient.
- **FR-006**: The experiment MUST be comparable to the latest stable baseline on the same bounded comparison slice under the same transaction-cost assumptions.
- **FR-007**: The experiment MUST produce a result that can be judged using explicit net-score, trade-count, and drawdown comparisons.
- **FR-009**: The bounded comparison slice MUST be sufficient for a formal keep/rework/reject decision; unrestricted runs, when performed, are follow-up evidence rather than a prerequisite gate.
- **FR-008**: The confirmation rule MUST be applied consistently across all eligible symbols and throughout the full evaluation interval.

### Key Entities *(include if feature involves data)*

- **Market Regime State**: The broad-market condition that determines whether the strategy can trade normally or must remain flat.
- **Raw Momentum Direction**: The pre-confirmation directional reading derived from recent price movement for a symbol.
- **Confirmed Exposure Signal**: The tradable long, short, or flat output after regime gating and confirmation filtering are applied.
- **Baseline Comparison Record**: The reference metrics from the latest stable experiment used to judge whether the new variant is an improvement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the agreed comparison slice and current transaction-cost model, the confirmation-bar variant reduces trade count by at least 20% relative to the latest stable baseline.
- **SC-002**: On the same comparison slice, the confirmation-bar variant does not worsen net score by more than 10% relative to the latest stable baseline.
- **SC-003**: On the same comparison slice, the confirmation-bar variant does not produce a worse maximum drawdown than the latest stable baseline.
- **SC-004**: In every interval classified as bear-volatile, the strategy emits flat exposure for 100% of affected symbols.

## Assumptions

- The existing bear-volatile regime gate is already accepted as the current stable strategy baseline.
- The latest stable baseline metrics are recorded and available before this experiment is judged.
- The current transaction-cost model remains the authoritative cost assumption for deciding whether this experiment is successful.
- The same bounded comparison slice used for recent baseline validation remains the default evaluation surface for this experiment.
- Threshold tuning, minimum-hold rules, cooldown logic, backtester changes, and universe-selection changes are out of scope for this feature.
