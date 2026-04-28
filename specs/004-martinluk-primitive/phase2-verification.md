# Phase 2 Verification Evidence: MartinLuk Primitive

Generated: 2026-04-28T05:03:00Z

Scope: verification evidence for Phase 2 public-case reproduction validator work
(T006-T009) and the public-date reconstruction lane. This evidence is for the
spec/validator surface only; it does not claim private USIC ledger replication
or validate `src/strategies/active_strategy.py`.

## Commands run

| Check | Command | Result |
| --- | --- | --- |
| JSON syntax | `python3 -m json.tool specs/004-martinluk-primitive/public-operation-cases.json` | PASS, exited 0 |
| Baseline ledger validator | `python3 specs/004-martinluk-primitive/validate_public_cases.py` | PASS, `status: passed`, `case_count: 8`, `source_count: 9`, `errors: []` |
| Signal-trace unsupported-case fixture | `python3 specs/004-martinluk-primitive/validate_public_cases.py --signals-path specs/004-martinluk-primitive/fixtures/signal-trace-public-cases-insufficient-evidence.json` | EXPECTED RESEARCH-ONLY RESULT, exited 1 with `status: insufficient_evidence`, `classification_counts.insufficient_evidence: 8`, `not_reproduced: 0`; this verifies unsupported cases are explicit rather than silently passing |
| Focused unit tests | `uv run pytest tests/unit/test_martinluk_public_validator.py -q` | PASS, `4 passed in 0.02s` |
| Python syntax/type-adjacent check | `uv run python -m py_compile specs/004-martinluk-primitive/validate_public_cases.py tests/unit/test_martinluk_public_validator.py` | PASS, exited 0 |
| Dependency guardrail | `git diff --exit-code -- pyproject.toml uv.lock` | PASS, no dependency manifest diff |
| Reconstruction metadata check | custom Python check over `public-operation-cases.json` | PASS, five target cases have `reconstructed_candidate` windows, `date_reconstruction.status: reconstructed_candidate_not_exact_fill`, and non-empty limitations |

## Baseline validator output

```json
{
  "case_count": 8,
  "errors": [],
  "passed": true,
  "source_count": 9,
  "status": "passed"
}
```

## Signal-trace fixture evidence

The fixture at
`specs/004-martinluk-primitive/fixtures/signal-trace-public-cases-insufficient-evidence.json`
intentionally emits no private-ledger fills. The validator returned
`insufficient_evidence` rather than `passed`, with all eight public cases listed
as unsupported and zero `not_reproduced` cases.

Important nuance: the five reconstructed long-side cases now have candidate
calendar windows for public signal research, but exact fills/timestamps/sizes are
still unavailable. Until a future trace can match deterministic machine-readable
windows and signals, this remains a research-only validator result, not a
production strategy-pass claim.

## Accepted evidence artifacts

- `specs/004-martinluk-primitive/public-operation-cases.json` — public cases plus
  date-reconstruction metadata for SOFI, AMC, COIN, LMND, and SMCI.
- `specs/004-martinluk-primitive/public-date-reconstruction.md` — source-backed
  reconstruction table and unsupported-field boundary.
- `specs/004-martinluk-primitive/fixtures/signal-trace-public-cases-insufficient-evidence.json`
  — explicit unsupported-case fixture.
- `tests/unit/test_martinluk_public_validator.py` — focused validator unit tests.

## Remaining risks / non-claims

- The candidate windows are public-evidence reconstructions, not exact execution
  ledger dates.
- Intraday 1m/5m timestamps, broker fills, partial sizes, stop adjustments,
  slippage/fees, margin, and account equity remain unavailable.
- `src/strategies/active_strategy.py` was intentionally not edited or verified in
  this Phase 2 lane.
