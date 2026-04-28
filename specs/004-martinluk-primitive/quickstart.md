# Quickstart: MartinLuk Primitive

## Phase 0/1 validation

```bash
python3 specs/004-martinluk-primitive/validate_public_cases.py
```

Expected result for the current ledger-only phase:

```json
{
  "status": "passed",
  "passed": true,
  "case_count": 8
}
```

## Review evidence

```bash
cat specs/004-martinluk-primitive/source-ledger.json
cat specs/004-martinluk-primitive/public-operation-cases.json
```

## Later implementation checks

Do not run these until strategy code exists:

```bash
python -m py_compile src/strategies/active_strategy.py
pytest tests/unit/test_strategy_interface.py -q
python3 specs/004-martinluk-primitive/validate_public_cases.py --signals-path <path>
```

`<path>` must point to a JSON document with
`schema_version: "martinluk_public_signal_trace_v1"`, replication target
`public_operation_reproducibility`, and a `signals` list containing stable
`case_id`, `symbol`, `direction`, `date`, `setup_type`, `entry_trigger`, and
`data_status` fields.

## Phase 4 validator semantics

The signal-trace validator remains fail-closed. Its CLI exits non-zero whenever
`passed` is false, including research-only `insufficient_evidence` results. For
Phase 4 dry-run verification, a non-zero validator result is acceptable only
when parsed JSON satisfies all of these conditions:

1. `status == "insufficient_evidence"` and `passed == false`;
2. there are no schema, replication-target, or diagnostic errors;
3. unsupported public cases have `classification_counts.not_reproduced == 0`;
4. the trace/report makes no private-ledger or exact-fill replication claim.

This is a research-only stop condition, not a promotion signal. Do not run
backtests, score comparisons, live/autoresearch loops, or promotion work as part
of Phase 4 verification.
