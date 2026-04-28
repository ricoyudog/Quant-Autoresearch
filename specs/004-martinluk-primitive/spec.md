# Feature Specification: MartinLuk Leader Pullback / ORH Primitive

## Status

Draft; Phase 0/1 ledger materialized. No strategy code has been changed.

## User Story 1 - Preserve a public-operation evidence base (P1)

As the research operator, I want Martin Luk public strategy evidence represented as structured cases so that future strategy changes are measured against concrete examples rather than vague inspiration.

### Acceptance Scenarios

1. **Given** a public strategy source, **when** it is added to `source-ledger.json`, **then** it records URL, source type, use, confidence, and whether it supports exact replication.
2. **Given** a public operation case, **when** it is added to `public-operation-cases.json`, **then** it records setup, entry, stop, trim, exit, source IDs, confidence, and missing fields.
3. **Given** a case lacks source IDs, **when** validation runs, **then** it fails.

## User Story 2 - Define a reproducible primitive before strategy mutation (P1)

As a strategy developer, I want a deterministic primitive contract before editing `active_strategy.py` so that the next implementation does not repeat broad 20-bar momentum variations.

### Acceptance Scenarios

1. **Given** the primitive spec, **when** implementation starts, **then** it uses leader selection, EMA/AVWAP context, ORH/IRH/prior-high or pullback entries, hard stops, partial trims, and trend exits.
2. **Given** the primitive is unvalidated on public cases, **when** any post-Phase-4 promotion is requested, **then** the validator blocks promotion.

## User Story 3 - Prevent private-ledger replication overclaims (P1)

As the project owner, I want explicit language that public evidence cannot guarantee every USIC trade so that reports stay honest and auditable.

### Acceptance Scenarios

1. **Given** a report claims exact replication, **when** no full broker/VOD/chart ledger is attached, **then** the validator marks the claim invalid.
2. **Given** only public examples exist, **when** the strategy reproduces them, **then** the output claim is limited to public-operation reproducibility.

## Functional Requirements

- **FR-001**: The spec MUST define the replication boundary as public-operation reproducibility, not private-ledger cloning.
- **FR-002**: The source ledger MUST include source confidence and intended use.
- **FR-003**: The operation ledger MUST include setup, entry, stop, trim, exit, source IDs, confidence, and missing fields.
- **FR-004**: The primitive MUST prioritize hot leaders and pullback/breakout structures rather than broad liquid minute-momentum.
- **FR-005**: The first implementation MUST start with 0.5% portfolio risk per trade, no leverage, hard stops, and max stop 2.5% unless explicitly testing a separate 5% branch.
- **FR-006**: The validator MUST return `insufficient_evidence` or fail when a case lacks enough public information for signal reproduction.
- **FR-007**: Post-Phase-4 promotion work, including backtests or live autoresearch mutation, MUST wait until the public-case validator exists and passes.

## Non-Goals

- No live trading.
- No claim to copy Martin Luk's exact account or PnL.
- No initial leverage/margin replication.
- No immediate edit to `src/strategies/active_strategy.py` in Phase 0/1.
- No new external dependencies.

## Success Metrics

- At least seven public operation cases are structured.
- JSON ledger validation passes.
- Later strategy implementation can reproduce at least five public cases or explicitly classify unsupported cases.
- Reports include R-multiple, stop width, entry type, exit type, and missing-evidence notes.
