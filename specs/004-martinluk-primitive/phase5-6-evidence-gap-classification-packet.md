# MartinLuk Phase 5.6 Evidence Gap Classification Packet

Generated at: `2026-05-02T03:13:14+00:00`

## Decision

- Overall decision: `do_not_patch_trace_labels_and_do_not_launch_t020`
- T020 state: `- [ ] T020 Launch bounded autoresearch only after validator, focused tests, and replay gates pass`
- Safe trace-label patches: `0`
- Reviewed gap rows: `20` (`trace_label_missing=3`, `primitive_not_emitted=17`)

## No-overclaim boundary

This packet preserves insufficient_evidence and control-row diagnostics. It is not a broad backtest, profit proof, Martin Luk private-account replication, exact-fill replication, or evidence to launch T020.


## Missing-field taxonomy

The Phase 5.6 packet now classifies every parent public-case and source-ledger missing field in the machine-readable artifact. These classifications are blockers that preserve `insufficient_evidence`; they are not promotion evidence.

Allowed categories: `exact_date_missing`, `setup_entry_label_missing`, `fill_missing`, `exit_missing`, `account_context_missing`.

| Field | Classification | Scope / rationale |
| --- | --- | --- |
| `exact date` | `exact_date_missing` | candidate window exists, but no source-backed exact operation date |
| `exact first attempt timestamp` | `exact_date_missing` | first intraday attempt timestamp remains unavailable |
| `re-entry timestamp` | `exact_date_missing` | re-entry timestamp remains unavailable |
| `exact BTC context timestamp` | `exact_date_missing` | BTC context timing remains unavailable |
| `volume climax timestamp` | `exact_date_missing` | intraday volume-climax timing remains unavailable |
| `entry fill` | `fill_missing` | entry execution fill remains unavailable |
| `partial fill` | `fill_missing` | partial execution fill remains unavailable |
| `entry/exit fills` | `fill_missing` | entry and exit execution fills remain unavailable |
| `exact split-adjusted prices` | `fill_missing` | exact adjusted execution prices remain unavailable |
| `partial size` | `fill_missing` | partial execution size remains unavailable |
| `final exit fill` | `exit_missing` | final exit execution fill remains unavailable |
| `stop adjustment timestamps` | `exit_missing` | stop-management timing remains unavailable |
| `all exits` | `exit_missing` | exit sequence/timing remains unavailable |
| `actual premature exit` | `exit_missing` | actual premature exit remains unavailable |
| `would-have-held benchmark` | `exit_missing` | counterfactual held benchmark remains unavailable |
| `account equity` | `account_context_missing` | account equity/context remains unavailable |
| `position size` | `account_context_missing` | position/account sizing remains unavailable |
| `required setup_type/entry_trigger trace match` | `setup_entry_label_missing` | all 20 reviewed control rows lack a source-backed exact setup/entry trace match safe to patch |
| `exact dates/fills` | `exact_date_missing` | source-level compound date/fill note; parent-case fields retain fill-specific blockers |
| `complete fills` | `fill_missing` | source-level complete execution fills remain unavailable |
| `portfolio sizing` | `account_context_missing` | source-level portfolio/account sizing remains unavailable |
| `exact full execution ledger` | `fill_missing` | source-level full execution ledger remains unavailable |

## Source artifacts

- `specs/004-martinluk-primitive/phase5-2-bounded-replay-report.json` SHA-256 `ae4586d1071630b60b6ae004bf111880cf0af28bb07eea61ef9556f46ea75297`
- `specs/004-martinluk-primitive/public-operation-cases.json` SHA-256 `793017d0e66d96f8de4d429b4a3cf005792dd16f0cf23adecac8c3f96b08c3c3`
- `specs/004-martinluk-primitive/source-ledger.json` SHA-256 `55919c835ba3467f9534206aeb4650752dbd95a5bf04f0bf23118cace824839a`
- `src/strategies/active_strategy.py` SHA-256 `4116d921eb060fbe7b19ba3c625317aa8464a51e9ced8435a15b19d61c6cf705`
- `specs/004-martinluk-primitive/tasks.md` SHA-256 `536156f5da0844850bcdeae2813e3c3c00afa851b81aadae97b06c3258e1b517`

## Active strategy trace labels

- `leader_pullback_orh` / `opening_range_high_breakout` from `src/strategies/active_strategy.py:217-218,256-257`
- `declining_ema_avwap_bounce_short` / `resistance_rejection_breakdown` from `src/strategies/active_strategy.py:304-305,343-344`

## Row decisions

| Row | Gap | Kind | Symbol | Window | Required setup / trigger | Trace/series evidence | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `p5-control-sofi-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `SOFI` | `2024-10-22..2024-10-28` | `leader_pullback_prior_day_high` / `break_or_reclaim_above_prior_day_high_after_pullback` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-sofi-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `SOFI` | `2024-12-20..2024-12-27` | `leader_pullback_prior_day_high` / `break_or_reclaim_above_prior_day_high_after_pullback` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-sofi-null-1` | `primitive_not_emitted` | `null_control_window` | `QQQ` | `2024-10-29..2024-12-19` | `leader_pullback_prior_day_high` / `break_or_reclaim_above_prior_day_high_after_pullback` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, null_ticker_control_must_not_be_upgraded, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-sofi-null-2` | `primitive_not_emitted` | `null_control_window` | `SOFI` | `2024-09-23..2024-09-27` | `leader_pullback_prior_day_high` / `break_or_reclaim_above_prior_day_high_after_pullback` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-amc-adjacent-1` | `trace_label_missing` | `adjacent_control_window` | `AMC` | `2024-05-09..2024-05-10` | `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | trace=10; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, label_patch_would_turn_diagnostic_control_activity_into_reproduction_evidence, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-amc-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `AMC` | `2024-05-15..2024-05-16` | `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-amc-null-1` | `trace_label_missing` | `null_control_window` | `SPY` | `2024-05-13..2024-05-14` | `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | trace=80; series=317; ignored=row_setup_entry_trigger_requires_trace_match | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, null_ticker_control_must_not_be_upgraded, label_patch_would_turn_diagnostic_control_activity_into_reproduction_evidence, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-amc-null-2` | `trace_label_missing` | `null_control_window` | `AMC` | `2024-04-29..2024-04-30` | `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | trace=18; series=60; ignored=row_setup_entry_trigger_requires_trace_match | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, label_patch_would_turn_diagnostic_control_activity_into_reproduction_evidence, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-coin-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `COIN` | `2024-01-31..2024-02-06` | `theme_linked_inside_day_prior_high` / `inside_day_high_or_prior_high_break_or_low_of_day_reclaim` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-coin-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `COIN` | `2024-02-20..2024-02-23` | `theme_linked_inside_day_prior_high` / `inside_day_high_or_prior_high_break_or_low_of_day_reclaim` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-coin-null-1` | `primitive_not_emitted` | `null_control_window` | `QQQ` | `2024-02-07..2024-02-16` | `theme_linked_inside_day_prior_high` / `inside_day_high_or_prior_high_break_or_low_of_day_reclaim` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, null_ticker_control_must_not_be_upgraded, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-coin-null-2` | `primitive_not_emitted` | `null_control_window` | `COIN` | `2024-01-22..2024-01-26` | `theme_linked_inside_day_prior_high` / `inside_day_high_or_prior_high_break_or_low_of_day_reclaim` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-lmnd-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `LMND` | `2024-11-11..2024-11-14` | `high_tight_flag_inside_day` / `prior_day_high_or_inside_day_high_break` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-lmnd-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `LMND` | `2024-11-22..2024-11-27` | `high_tight_flag_inside_day` / `prior_day_high_or_inside_day_high_break` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-lmnd-null-1` | `primitive_not_emitted` | `null_control_window` | `SPY` | `2024-11-18..2024-11-21` | `high_tight_flag_inside_day` / `prior_day_high_or_inside_day_high_break` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, null_ticker_control_must_not_be_upgraded, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-lmnd-null-2` | `primitive_not_emitted` | `null_control_window` | `LMND` | `2024-10-21..2024-10-24` | `high_tight_flag_inside_day` / `prior_day_high_or_inside_day_high_break` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-smci-adjacent-1` | `primitive_not_emitted` | `adjacent_control_window` | `SMCI` | `2024-01-08..2024-01-12` | `weekly_base_tight_risk_breakout` / `base_breakout_or_tight_intraday_continuation_trigger` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-smci-adjacent-2` | `primitive_not_emitted` | `adjacent_control_window` | `SMCI` | `2024-01-22..2024-01-26` | `weekly_base_tight_risk_breakout` / `base_breakout_or_tight_intraday_continuation_trigger` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-smci-null-1` | `primitive_not_emitted` | `null_control_window` | `QQQ` | `2024-01-16..2024-01-19` | `weekly_base_tight_risk_breakout` / `base_breakout_or_tight_intraday_continuation_trigger` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, null_ticker_control_must_not_be_upgraded, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |
| `p5-control-smci-null-2` | `primitive_not_emitted` | `null_control_window` | `SMCI` | `2023-12-11..2023-12-15` | `weekly_base_tight_risk_breakout` / `base_breakout_or_tight_intraday_continuation_trigger` | trace=0; series=0; ignored=none | `do_not_patch_preserve_gap_classification` — row_is_control_not_public_operation_evidence, active_strategy_does_not_emit_exact_required_setup_entry_pair, no_matching_primitive_trace_or_series_to_relabel, parent_public_case_still_missing_exact_fill_or_intraday_management_fields |

## Interpretation

- `trace_label_missing` means primitive activity or trace signals exist, but not with the row-required setup/entry labels and window. These rows are controls, so label patching would convert diagnostics into unsupported reproduction evidence.
- `primitive_not_emitted` means no matching primitive signal was emitted for the bounded row window. There is no trace label to patch.
- Parent public cases can document setup/entry hypotheses, but the reviewed rows are adjacent/null controls and must not be upgraded beyond their bounded diagnostic role.
- Public-case missing fields remain exact intraday timestamps, fills, stop adjustments, exits, or complete fills depending on the case; realized outcomes stay `N/A`.
