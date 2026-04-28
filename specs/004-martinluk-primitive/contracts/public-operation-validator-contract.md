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
      "data_status": "available"
    }
  ]
}
```

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
