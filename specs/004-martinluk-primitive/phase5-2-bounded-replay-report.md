# MartinLuk Phase 5.2 Bounded Replay Report

Run ID: `martinluk_phase5_1_bounded_replay_v1`
Overall run status: `research_only`
Promoted: `false`

## No-overclaim boundary

Phase 5.1 is a bounded row-level replay of the frozen Phase 5 public candidate/control manifest. It is research-only unless all public replay candidate gates are separately satisfied. It is not a broad backtest, not profit proof, not Martin Luk realized P&L, not private-account replication, and not exact-fill replication. Realized entry, exit, size, fees, slippage, and account P&L remain N/A unless a later primary-fill evidence phase explicitly upgrades the evidence contract.

## Hash chain

- Phase 5 manifest SHA-256: `cfc867254cf2ca731397395083903b63c8c60b804deb6949a502288d031ed725`
- Replay request SHA-256: `ccf7c6e63f18ebb0a922fff7b4b1dde4da0c9dc084347e540c82a55ae00d8383`
- Query ledger SHA-256: `ab4314ea10e22a8b52086d365e4882daf53f3baa31152cb8b8e56ab2b9ca3a87`
- Runtime SHA-256: `4aec98b9a31a53df1ca6a6f0e4569734fd62027ad71ab8e5206bd40e0c191e51`

## Public replay candidates

- Required reproduced public replay candidates: `5`
- Reproduced public replay candidates: `0`
- Public status counts: `{"insufficient_evidence": 5}`

## Diagnostic controls

- Control rows: `20`
- Clean controls: `18`
- False-positive controls: `2`
- False-positive control row IDs: `["p5-control-amc-null-1", "p5-control-amc-null-2"]`
- Controls counted toward promotion: `0`

## Diagnostic promotion veto

- Active: `true`
- Reasons: `["false_positive_controls_present"]`
- False-positive control count: `2`
- False-positive control row IDs: `["p5-control-amc-null-1", "p5-control-amc-null-2"]`

## Audit-only rows

- Audit rows: `3`
- Audit rows execute loaders: `false`

## Realized outcomes

Realized entry, exit, position size, account P&L, fees, and slippage are `N/A` for every row.

## Phase 5.2 artifact note

Phase 5.2 report artifacts add diagnostic promotion-veto fields only; they do not broaden replay scope, query audit rows, or upgrade realized outcomes.
