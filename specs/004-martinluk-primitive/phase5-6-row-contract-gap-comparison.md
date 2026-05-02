# MartinLuk Phase 5.6 Row Contract Gap Comparison

Generated from `specs/004-martinluk-primitive/phase5-2-bounded-replay-report.json` and `specs/004-martinluk-primitive/phase5-replay-manifest.json`.

## Decision

- Do **not** patch `active_strategy.py` trace labels in this slice.
- Eligible trace-label patch rows: `[]`.
- Reason: the three `trace_label_missing` rows are diagnostic controls with generic strategy activity, while the public AMC source still lacks exact first-attempt, re-entry, stop-adjustment, and exit timestamps. Relabeling generic ORH traces as the public AMC re-entry contract would overclaim.
- The seventeen `primitive_not_emitted` rows have no existing primitive signal to relabel.

## No-overclaim boundary

Phase 5.1 is a bounded row-level replay of the frozen Phase 5 public candidate/control manifest. It is research-only unless all public replay candidate gates are separately satisfied. It is not a broad backtest, not profit proof, not Martin Luk realized P&L, not private-account replication, and not exact-fill replication. Realized entry, exit, size, fees, slippage, and account P&L remain N/A unless a later primary-fill evidence phase explicitly upgrades the evidence contract.

## Source-backed public candidate contracts

| Row | Case | Symbol | Setup type | Entry trigger | Candidate window | Missing public fields | Source refs exist | Phase 5.2 gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `p5-public-sofi` | `MLUK-SOFI-PULLBACK-PDH-001` | `SOFI` | `leader_pullback_prior_day_high` | `break_or_reclaim_above_prior_day_high_after_pullback` | 2024-10-29..2024-12-19 | exact date, entry fill, partial fill, final exit fill, account equity | `lilys_traderlion_2024_transcript` | `evidence_not_sufficient` |
| `p5-public-amc` | `MLUK-AMC-ORH-REENTRY-002` | `AMC` | `opening_range_high_inside_day_reentry` | `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | 2024-05-13..2024-05-14 | exact first attempt timestamp, re-entry timestamp, stop adjustment timestamps, all exits | `lilys_traderlion_2024_transcript` | `evidence_not_sufficient` |
| `p5-public-coin` | `MLUK-COIN-BTC-INSIDEDAY-003` | `COIN` | `theme_linked_inside_day_prior_high` | `inside_day_high_or_prior_high_break_or_low_of_day_reclaim` | 2024-02-07..2024-02-16 | exact BTC context timestamp, entry/exit fills, position size | `financialwisdom_martin_luk_strategy`, `lilys_traderlion_2024_transcript` | `evidence_not_sufficient` |
| `p5-public-lmnd` | `MLUK-LMND-HIGHTIGHTFLAG-004` | `LMND` | `high_tight_flag_inside_day` | `prior_day_high_or_inside_day_high_break` | 2024-11-18..2024-11-21 | exact split-adjusted prices, partial size, volume climax timestamp | `lilys_traderlion_2024_transcript` | `evidence_not_sufficient` |
| `p5-public-smci` | `MLUK-SMCI-WEEKLYBASE-005` | `SMCI` | `weekly_base_tight_risk_breakout` | `base_breakout_or_tight_intraday_continuation_trigger` | 2024-01-16..2024-01-19 | exact date, actual premature exit, would-have-held benchmark | `lilys_traderlion_2024_transcript` | `evidence_not_sufficient` |

All five public replay rows match the `public-operation-cases.json` contracts and reuse source IDs present in `source-ledger.json`. `public-date-reconstruction.md` still frames these as candidate windows, not exact private fills or timestamps.

## Active strategy trace contract comparison

- `src/strategies/active_strategy.py:210-230` and `249-269` emit long traces as `setup_type=leader_pullback_orh`, `entry_trigger=opening_range_high_breakout`, `case_id=PHASE4-{ticker}-ORH`.
- `src/strategies/active_strategy.py:297-317` and `336-355` emit short traces as `setup_type=declining_ema_avwap_bounce_short`, `entry_trigger=resistance_rejection_breakdown`, `case_id=V1-{ticker}-SHORT`.
- The Phase 5 public row contracts require public-case-specific labels such as `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt`; those labels are not emitted by the current strategy trace contract.

## Trace-label-missing rows

| Row | Control role | Symbol | Required setup / trigger | Window | Trace signals | Rejections | Series positives | Conclusion |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- |
| `p5-control-amc-adjacent-1` | `before_window` | `AMC` | `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | 2024-05-09..2024-05-10 | 10 | date_window_mismatch=10, direction_mismatch=1, entry_trigger_mismatch=10, setup_type_mismatch=10 | 0 | `do_not_patch_trace_label_without_new_primary_evidence` |
| `p5-control-amc-null-1` | `null_ticker` | `SPY` | `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | 2024-05-13..2024-05-14 | 80 | direction_mismatch=29, entry_trigger_mismatch=80, setup_type_mismatch=80 | 317 | `do_not_patch_trace_label_without_new_primary_evidence` |
| `p5-control-amc-null-2` | `null_date` | `AMC` | `opening_range_high_inside_day_reentry` / `5m_ORH_or_later_tight_intraday_range_high_after_failed_first_attempt` | 2024-04-29..2024-04-30 | 18 | direction_mismatch=1, entry_trigger_mismatch=18, setup_type_mismatch=18 | 60 | `do_not_patch_trace_label_without_new_primary_evidence` |

These rows prove generic primitive/series activity exists in diagnostic windows, not that the public AMC re-entry operation has a source-supported exact trace label.

## Primitive-not-emitted rows

| Parent case | Count | Row IDs |
| --- | ---: | --- |
| `MLUK-AMC-ORH-REENTRY-002` | 1 | `p5-control-amc-adjacent-2` |
| `MLUK-COIN-BTC-INSIDEDAY-003` | 4 | `p5-control-coin-adjacent-1`, `p5-control-coin-adjacent-2`, `p5-control-coin-null-1`, `p5-control-coin-null-2` |
| `MLUK-LMND-HIGHTIGHTFLAG-004` | 4 | `p5-control-lmnd-adjacent-1`, `p5-control-lmnd-adjacent-2`, `p5-control-lmnd-null-1`, `p5-control-lmnd-null-2` |
| `MLUK-SMCI-WEEKLYBASE-005` | 4 | `p5-control-smci-adjacent-1`, `p5-control-smci-adjacent-2`, `p5-control-smci-null-1`, `p5-control-smci-null-2` |
| `MLUK-SOFI-PULLBACK-PDH-001` | 4 | `p5-control-sofi-adjacent-1`, `p5-control-sofi-adjacent-2`, `p5-control-sofi-null-1`, `p5-control-sofi-null-2` |

The `primitive_not_emitted` rows have no matching trace primitive under the row symbol, direction, setup type, entry trigger, and allowed-window contract, so there is no supported label-only patch.

## Contract consistency checks

- Manifest executable rows: `25`
- Phase 5.2 report rows: `25`
- Match-provenance required fields align with manifest: `true`
- Gap classification summary: `{"evidence_not_sufficient": 8, "primitive_not_emitted": 17, "trace_label_missing": 3}`

## Machine-readable artifact

- `specs/004-martinluk-primitive/phase5-6-row-contract-gap-comparison.json`
