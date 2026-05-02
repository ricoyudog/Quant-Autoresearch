# MartinLuk Phase 5.7 Missing Primary-Evidence Map

Generated at: `2026-05-02T03:29:00+00:00`

## Decision

- Overall decision: `record_missing_primary_evidence_without_upgrading_replay_or_launching_t020`
- T020 state: `- [ ] T020 Launch bounded autoresearch only after validator, focused tests, and replay gates pass`
- Public replay candidates mapped: `5`
- Phase 5.6 gap rows mapped: `20`
- Gap rows by classification: `{"primitive_not_emitted": 17, "trace_label_missing": 3}`

## No-overclaim boundary

This artifact identifies missing primary public evidence only. It does not add sources, update exact dates/fills, patch trace labels, prove profit, replicate private-account outcomes, or authorize T020/broad autoresearch.

## Public replay candidates

| Row | Case | Symbol | Missing primary evidence | Status |
| --- | --- | --- | --- | --- |
| `p5-public-sofi` | `MLUK-SOFI-PULLBACK-PDH-001` | `SOFI` | exact date; entry fill; partial fill; final exit fill; account equity | `insufficient_evidence_until_each_missing_primary_field_is_cited` |
| `p5-public-amc` | `MLUK-AMC-ORH-REENTRY-002` | `AMC` | exact first attempt timestamp; re-entry timestamp; stop adjustment timestamps; all exits | `insufficient_evidence_until_each_missing_primary_field_is_cited` |
| `p5-public-coin` | `MLUK-COIN-BTC-INSIDEDAY-003` | `COIN` | exact BTC context timestamp; entry/exit fills; position size | `insufficient_evidence_until_each_missing_primary_field_is_cited` |
| `p5-public-lmnd` | `MLUK-LMND-HIGHTIGHTFLAG-004` | `LMND` | exact split-adjusted prices; partial size; volume climax timestamp | `insufficient_evidence_until_each_missing_primary_field_is_cited` |
| `p5-public-smci` | `MLUK-SMCI-WEEKLYBASE-005` | `SMCI` | exact date; actual premature exit; would-have-held benchmark | `insufficient_evidence_until_each_missing_primary_field_is_cited` |

## Phase 5.6 gap rows

| Row | Gap | Kind | Symbol | Missing primary evidence categories | Evidence status |
| --- | --- | --- | --- | --- | --- |
| `p5-control-sofi-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `SOFI` | account_context_primary_evidence_missing, control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-sofi-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `SOFI` | account_context_primary_evidence_missing, control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-sofi-null-1` | `primitive_not_emitted` | `null_control_window` | `QQQ` | account_context_primary_evidence_missing, control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, null_control_public_operation_link_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-sofi-null-2` | `primitive_not_emitted` | `null_control_window` | `SOFI` | account_context_primary_evidence_missing, control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-amc-adjacent-1` | `trace_label_missing` | `adjacent_control_window` | `AMC` | control_identity_primary_evidence_missing, diagnostic_control_relabel_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-amc-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `AMC` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-amc-null-1` | `trace_label_missing` | `null_control_window` | `SPY` | control_identity_primary_evidence_missing, diagnostic_control_relabel_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, null_control_public_operation_link_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-amc-null-2` | `trace_label_missing` | `null_control_window` | `AMC` | control_identity_primary_evidence_missing, diagnostic_control_relabel_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-coin-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `COIN` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-coin-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `COIN` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-coin-null-1` | `primitive_not_emitted` | `null_control_window` | `QQQ` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, null_control_public_operation_link_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-coin-null-2` | `primitive_not_emitted` | `null_control_window` | `COIN` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-lmnd-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `LMND` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-lmnd-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `LMND` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-lmnd-null-1` | `primitive_not_emitted` | `null_control_window` | `SPY` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, null_control_public_operation_link_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-lmnd-null-2` | `primitive_not_emitted` | `null_control_window` | `LMND` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, fill_size_or_price_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-smci-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `SMCI` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-smci-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `SMCI` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-smci-null-1` | `primitive_not_emitted` | `null_control_window` | `QQQ` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, null_control_public_operation_link_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |
| `p5-control-smci-null-2` | `primitive_not_emitted` | `null_control_window` | `SMCI` | control_identity_primary_evidence_missing, exact_date_or_timestamp_primary_evidence_missing, exit_or_benchmark_primary_evidence_missing, operation_detail_primary_evidence_missing, primitive_trace_support_missing, setup_entry_label_primary_evidence_missing | `control_gap_preserved_until_cited_primary_evidence_and_bounded_replay_support_both_exist` |

## Source artifacts

- `specs/004-martinluk-primitive/phase5-7-public-evidence-upgrade-plan.json` SHA-256 `6e1cfcabdbad288aaf1bcfc2160864e0a76e5ccda231b99e0c22d45c913cf8b8`
- `specs/004-martinluk-primitive/phase5-6-evidence-gap-classification-packet.json` SHA-256 `8075db5d7943a50f0281a10c966f813564f40210b7f226e200068b2db4377aff`
- `specs/004-martinluk-primitive/phase5-6-row-contract-gap-comparison.json` SHA-256 `c2459bf0eaf17c594499b2a765d1951e6868599cb36f1f9f214228ea96818cd3`
- `specs/004-martinluk-primitive/phase5-2-bounded-replay-report.json` SHA-256 `ae4586d1071630b60b6ae004bf111880cf0af28bb07eea61ef9556f46ea75297`
- `specs/004-martinluk-primitive/public-operation-cases.json` SHA-256 `793017d0e66d96f8de4d429b4a3cf005792dd16f0cf23adecac8c3f96b08c3c3`
- `specs/004-martinluk-primitive/public-date-reconstruction.md` SHA-256 `a6c652e9a6963d261287dfdb3f4b78091fcbcf03b5b56ecf70a0525d41f96150`
- `specs/004-martinluk-primitive/source-ledger.json` SHA-256 `55919c835ba3467f9534206aeb4650752dbd95a5bf04f0bf23118cace824839a`

## Machine-readable artifact

- `specs/004-martinluk-primitive/phase5-7-missing-primary-evidence-map.json`
