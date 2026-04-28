# Contract: Public Operation Validator

## Purpose

The validator protects the project from treating Martin Luk public strategy descriptions as if they were a complete private execution ledger.

## Required Inputs

- `source-ledger.json`
- `public-operation-cases.json`
- optional future signal trace file from strategy backtests

## Ledger Validation Rules

- Every case must have a non-empty `case_id`.
- Every case must include at least one `source_id`.
- Every `source_id` must exist in `source-ledger.json`.
- Every case must include `setup_type`, `entry_trigger`, `stop_rule`, `exit_rule`, `confidence`, and `missing_fields`.
- The top-level replication target must be `public_operation_reproducibility`.
- The top-level non-target must explicitly reject private ledger cloning.

## Future Signal Validation Rules

Signal traces supplied with `--signals-path` use this deterministic shape:

```json
{
  "schema_version": "martinluk_public_signal_trace_v1",
  "replication_target": "public_operation_reproducibility",
  "signals": [
    {
      "signal_id": "stable optional identifier",
      "case_id": "MLUK-SOFI-PULLBACK-PDH-001",
      "symbol": "SOFI",
      "direction": "long",
      "date": "YYYY-MM-DD",
      "setup_type": "leader_pullback_prior_day_high",
      "entry_trigger": "break_or_reclaim_above_prior_day_high_after_pullback",
      "data_status": "available",
      "r_multiple": 2.4,
      "mae": -0.35,
      "mae_unit": "R",
      "mfe": 3.1,
      "mfe_unit": "R",
      "stop_width_pct": 4.2,
      "entry_type": "breakout_reclaim",
      "trim_type": "partial_strength_trim",
      "exit_type": "rule_exit",
      "holding_period_bars": 18
    }
  ]
}
```

Diagnostic fields are part of each `signals[]` entry itself, not a nested
`diagnostics` object. Matched reproduced signals must include:

- `r_multiple`;
- `mae` and `mae_unit`;
- `mfe` and `mfe_unit`;
- `stop_width_pct`;
- `entry_type`;
- `trim_type`;
- `exit_type`;
- at least one of `holding_period_bars` or `holding_period_minutes`.

Open reproduced trades are represented with `exit_type: "open"`. They must
still include entry, stop-width, MAE/MFE value+unit, and holding-period
diagnostics. `r_multiple` and `trim_type` may be `null` only for these open
trades; closed trades must provide non-null values for all reproduced-signal
diagnostics. A trace that supplies `mae` without `mae_unit`, or `mfe` without
`mfe_unit`, must fail with an explicit diagnostic error.

Future changes to diagnostic semantics, field placement, or required fields
require an explicit `schema_version` decision before implementation.

When signal traces exist, each case should evaluate to one of:

- `reproduced`: expected direction and trigger appear inside expected window;
- `not_reproduced`: enough data exists but signal did not match;
- `insufficient_evidence`: public case lacks date/fill/window detail;
- `data_missing`: local market data is unavailable.

## Passing Criteria

Current ledger phase:

- JSON parses;
- at least seven cases;
- all required fields and source links pass.

Future signal phase:

- at least five public cases reproduced, or the run must remain research-only;
- unsupported cases are listed with missing fields;
- no exact private-ledger replication claim is emitted.

The CLI remains non-zero for any `passed: false` result. A non-zero
`insufficient_evidence` result may be accepted by a Phase 4 dry-run plan only as
a research-only schema pass: no schema/replication-target/diagnostic errors, no
`not_reproduced` classifications for unsupported public cases, and no
private-ledger or exact-fill replication claim. Any other non-zero result is a
validator failure, not an acceptable stop condition.
