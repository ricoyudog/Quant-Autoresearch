# Phase 3b Risk Ledger: MartinLuk Primitive Validator Closure

Generated: 2026-04-28T08:42:23Z

Scope: Phase-3-fixable validator/schema risk closure only. This ledger does not claim production `active_strategy.py` trace emission, exact private USIC ledger replication, or exact public fill reconstruction.

| Risk | Status | Owner phase | Future trigger | Evidence / boundary |
| --- | --- | --- | --- | --- |
| Required reproduced-signal diagnostics can be absent from matched reproduced traces | Closed | Phase 3/3b | Re-open only if `martinluk_public_signal_trace_v1` changes required diagnostic fields | Validator requires direct reproduced-signal diagnostics and focused unit tests cover missing-field failures. |
| Diagnostics placed under a nested `diagnostics` object could silently pass despite the v1 direct-field contract | Closed | Phase 3/3b | Re-open only after a schema-version decision intentionally allows nested placement | Nested diagnostics object rejection remains part of the validator/test contract. |
| MAE/MFE values can be supplied without explicit units or with duplicate/ambiguous unit errors | Closed | Phase 3/3b | Re-open if additional diagnostic value/unit pairs are added | Validator/test coverage keeps MAE/MFE unit errors explicit and singular. |
| Diagnostic numeric fields can carry invalid types, including booleans | Closed | Phase 3/3b | Re-open if new numeric diagnostics are added to the reproduced-trace contract | Phase 3b validator hardening rejects non-numeric and bool values for numeric diagnostics. |
| Diagnostic numeric ranges can allow nonsensical negative stop width or holding periods | Closed | Phase 3/3b | Re-open if new range-constrained diagnostics are introduced | Phase 3b validator hardening rejects negative stop width and negative holding periods. |
| Diagnostic label fields can be empty or non-string while still satisfying presence checks | Closed | Phase 3/3b | Re-open if a future schema version adds strict enums or new label fields | Phase 3b keeps v1 labels flexible but requires non-empty strings where fields are required. |
| Public insufficient-evidence cases could drift into `not_reproduced` or pass silently | Closed | Phase 3/3b | Re-run when public fixtures or matching rules change | Insufficient-evidence JSON assertion must prove `status == insufficient_evidence` and `classification_counts.not_reproduced == 0`. |
| Synthetic reproduced fixtures do not prove real SOFI/AMC/COIN/LMND/SMCI reproduction | Accepted | Phase 3/3b | Phase 5 evidence/data reconstruction can revisit after exact timestamps/fills are available | Accepted non-claim: synthetic schema tests verify validator behavior only, not public-case reproduction. |
| `src/strategies/active_strategy.py` does not emit MartinLuk production signal traces | Deferred to Phase 4 | Phase 4 strategy trace emission | Start Phase 4 with GitNexus impact on `active_strategy.py`, failing strategy-interface tests, and a trace-adapter acceptance target | Out of scope for Phase 3b; active strategy must remain untouched here. |
| Strategy-interface coverage for leader universe, ORH/IRH entry, hard stop, and 9 EMA exit is not implemented | Deferred to Phase 4 | Phase 4 dry-run primitive implementation | Create failing `tests/unit/test_strategy_interface.py` cases before strategy mutation | Phase 3b closes validator/schema risks only. |
| Exact intraday timestamps, broker fills, partial sizes, stop adjustments, fees, slippage, margin, and account equity remain unavailable | Deferred to Phase 5 | Phase 5 evidence/data reconstruction | Revisit only with approved public/private evidence sources, schema decisions, or broker/VOD/chart ledgers | Exact private/public fill replication is not claimed in Phase 3b. |

## No-overclaim statement

Phase 3b closes Phase-3-fixable validator/schema risks only. Remaining production strategy trace emission belongs to Phase 4, and exact public/private fill reconstruction belongs to Phase 5/evidence work.
