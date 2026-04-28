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

## Promotion rule

A broad backtest or live autoresearch run is allowed only after:

1. public cases validate structurally;
2. signal reproduction validator exists;
3. at least five public cases reproduce or are explicitly marked unsupported with evidence;
4. no report claims exact private-ledger replication.
