# MartinLuk Phase 5.7 Public-Evidence Upgrade Plan

Generated at: `2026-05-02T03:18:00+00:00`

## Decision

- Overall decision: `keep_t020_blocked_and_collect_primary_public_evidence_only`
- T020 state: `- [ ] T020 Launch bounded autoresearch only after validator, focused tests, and replay gates pass`
- Broad autoresearch allowed: `false`
- New primary public evidence added: `false`
- Source-ledger update policy: `proposal_only_until_cited_primary_public_evidence_supports_the_specific_missing_field`

## No-overclaim boundary

Phase 5.7 is a planning artifact only. It preserves insufficient_evidence, research_only, promoted=false, and N/A realized outcomes. It is not a broad backtest, not profit proof, not Martin Luk realized P&L, not private-account replication, not exact-fill replication, and not evidence to launch T020.

## Current bounded replay status

- Overall run status: `research_only`
- Promoted: `false`
- Public replay candidates reproduced: `0` / `5`
- Public status counts: `{"insufficient_evidence": 5}`
- Public gap classifications: `{"evidence_not_sufficient": 5}`
- False-positive control row IDs: `[]`
- Controls counted toward promotion: `0`

## Public candidate evidence upgrade matrix

| Row | Case | Symbol | Candidate window | Current status | Missing primary public evidence | Upgrade status |
| --- | --- | --- | --- | --- | --- | --- |
| `p5-public-sofi` | `MLUK-SOFI-PULLBACK-PDH-001` | `SOFI` | `2024-10-29..2024-12-19` | `insufficient_evidence` / `evidence_not_sufficient` | exact date; entry fill; partial fill; final exit fill; account equity | `blocked_pending_cited_primary_public_evidence` |
| `p5-public-amc` | `MLUK-AMC-ORH-REENTRY-002` | `AMC` | `2024-05-13..2024-05-14` | `insufficient_evidence` / `evidence_not_sufficient` | exact first attempt timestamp; re-entry timestamp; stop adjustment timestamps; all exits | `blocked_pending_cited_primary_public_evidence` |
| `p5-public-coin` | `MLUK-COIN-BTC-INSIDEDAY-003` | `COIN` | `2024-02-07..2024-02-16` | `insufficient_evidence` / `evidence_not_sufficient` | exact BTC context timestamp; entry/exit fills; position size | `blocked_pending_cited_primary_public_evidence` |
| `p5-public-lmnd` | `MLUK-LMND-HIGHTIGHTFLAG-004` | `LMND` | `2024-11-18..2024-11-21` | `insufficient_evidence` / `evidence_not_sufficient` | exact split-adjusted prices; partial size; volume climax timestamp | `blocked_pending_cited_primary_public_evidence` |
| `p5-public-smci` | `MLUK-SMCI-WEEKLYBASE-005` | `SMCI` | `2024-01-16..2024-01-19` | `insufficient_evidence` / `evidence_not_sufficient` | exact date; actual premature exit; would-have-held benchmark | `blocked_pending_cited_primary_public_evidence` |

## Upgrade sequence

### evidence_search

- Action: For each missing public field, search only for public primary or source-near evidence that states the operation-level date, timestamp, fill, trim, exit, stop-management, size, or benchmark detail directly.
- Stop condition: If no cited primary evidence supports the missing field, keep the row insufficient_evidence and record the gap; do not infer from market bars alone.

### ledger_or_date_reconstruction_proposal

- Action: Only propose source-ledger or public-date-reconstruction changes when the cited evidence can be tied to a specific missing field and source ID.
- Stop condition: No cited evidence means proposal-only/no-op; do not update exact dates, fills, or labels.

### bounded_validator_replay

- Action: After evidence-backed artifact updates, rerun validator and bounded replay gates with the frozen no-overclaim contract.
- Stop condition: Any remaining public candidate with insufficient_evidence keeps promoted=false and blocks T020.

### t020_gate_review

- Action: Review T020 only after all five public replay candidates have evidence-backed reproduction and diagnostic controls remain clean.
- Stop condition: Until that condition is met, T020 stays unchecked and no broad autoresearch launches.

## Source artifacts

- `specs/004-martinluk-primitive/phase5-2-bounded-replay-report.json` SHA-256 `ae4586d1071630b60b6ae004bf111880cf0af28bb07eea61ef9556f46ea75297`
- `specs/004-martinluk-primitive/phase5-6-row-contract-gap-comparison.json` SHA-256 `c2459bf0eaf17c594499b2a765d1951e6868599cb36f1f9f214228ea96818cd3`
- `specs/004-martinluk-primitive/phase5-6-evidence-gap-classification-packet.json` SHA-256 `8075db5d7943a50f0281a10c966f813564f40210b7f226e200068b2db4377aff`
- `specs/004-martinluk-primitive/phase5-replay-manifest.json` SHA-256 `cfc867254cf2ca731397395083903b63c8c60b804deb6949a502288d031ed725`
- `specs/004-martinluk-primitive/public-operation-cases.json` SHA-256 `793017d0e66d96f8de4d429b4a3cf005792dd16f0cf23adecac8c3f96b08c3c3`
- `specs/004-martinluk-primitive/public-date-reconstruction.md` SHA-256 `a6c652e9a6963d261287dfdb3f4b78091fcbcf03b5b56ecf70a0525d41f96150`
- `specs/004-martinluk-primitive/source-ledger.json` SHA-256 `55919c835ba3467f9534206aeb4650752dbd95a5bf04f0bf23118cace824839a`
- `specs/004-martinluk-primitive/tasks.md` SHA-256 `536156f5da0844850bcdeae2813e3c3c00afa851b81aadae97b06c3258e1b517`

## Machine-readable artifact

- `specs/004-martinluk-primitive/phase5-7-public-evidence-upgrade-plan.json`
