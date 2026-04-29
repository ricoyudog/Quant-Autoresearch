# MartinLuk Phase 5 Bounded Validation Dry-Run Report

Run ID: `martinluk_phase5_dry_run_v1`
Overall run status: `research_only`
Promoted: `false`

## No-overclaim boundary

Phase 5 is a bounded public candidate-window dry-run report. It records evidence class, validation status, data availability, and hypothetical strategy-bar diagnostics only. It is not profit proof, not Martin Luk realized P&L, not private account replication, and not exact fill replication; realized entry, exit, size, fees, slippage, and account P&L remain N/A unless new primary fill evidence is separately approved.

## Manifest and sources

- Manifest: `specs/004-martinluk-primitive/phase5-replay-manifest.json`
- Manifest SHA-256: `cfc867254cf2ca731397395083903b63c8c60b804deb6949a502288d031ed725`
- Daily source: `src/data/duckdb_connector.py::load_daily_data`
- Minute source: `src/data/duckdb_connector.py::query_minute_data`
- Market data queries in this dry run: `0`

## Public replay gate

- Required reproduced public replay candidates: `5`
- Reproduced public replay candidates: `0`
- Controls counted toward promotion: `0`
- Public status counts: `{"insufficient_evidence": 5}`

## Bounded controls

- Control rows: `20`
- Control status counts: `{"insufficient_evidence": 20}`
- Note: controls are diagnostic only and never count toward public-case promotion.

## Audit-only evidence rows

| case_id | evidence_class | status | reason |
| --- | --- | --- | --- |
| `MLUK-GLD-SLV-DECLINING9EMA-SHORT-006` | `research_only_insufficient_evidence` | `insufficient_evidence` | exact post date and primary GLD/SLV instrument are unavailable |
| `MLUK-SNDK-RETRY-COOLDOWN-007` | `research_only_insufficient_evidence` | `insufficient_evidence` | direction, retry timestamps, and exact switch rule are unavailable |
| `MLUK-NVDA-TSLA-QUANTUM-2025-PULLBACK-008` | `unsupported_until_new_primary_evidence` | `insufficient_evidence` | 2025 multi-symbol case requires new primary VOD/source extraction before replay |

## Validation

- Manifest validation passed: `true`
- Executable rows: `25`
- Public replay rows: `5`
- Adjacent controls: `10`
- Null controls: `10`
- Audit rows: `3`
- Validation errors: `[]`

## Realized outcome fields

Realized entry, exit, size, fees, slippage, and account P&L are `N/A` for every row because current public evidence does not contain exact fills.
