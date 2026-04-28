# Phase 3 Verification Evidence: MartinLuk Primitive Diagnostics

Generated: 2026-04-28T06:56:00Z

Scope: verification evidence for Phase 3 strategy-diagnostic trace work
(T010-T011). This evidence covers the public-operation validator contract,
synthetic signal-trace diagnostics, and task closeout only. It does not edit or
validate `src/strategies/active_strategy.py`, and it does not claim exact private
USIC ledger replication.

Verified on leader-reconciled HEAD `a368b62` after the validator/test lanes were
integrated.

## Commands run

| Check | Command | Result |
| --- | --- | --- |
| Focused diagnostic unit tests | `uv run pytest tests/unit/test_martinluk_public_validator.py -q` | PASS, `10 passed in 0.03s` |
| Baseline ledger validator | `python3 specs/004-martinluk-primitive/validate_public_cases.py` | PASS, `status: passed`, `case_count: 8`, `source_count: 9`, `errors: []` |
| Public insufficient-evidence fixture | `python3 specs/004-martinluk-primitive/validate_public_cases.py --signals-path specs/004-martinluk-primitive/fixtures/signal-trace-public-cases-insufficient-evidence.json` | EXPECTED NON-PASS, exited 1 with `status: insufficient_evidence`, `classification_counts.insufficient_evidence: 8`, `classification_counts.not_reproduced: 0`, and `diagnostic_errors: []` |
| Fixture JSON inspection | custom Python check over `/tmp/worker3-phase3/validator-insufficient.json` output | PASS, verified `status == insufficient_evidence` and `not_reproduced == 0` |
| Python syntax check | `python3 -m py_compile specs/004-martinluk-primitive/validate_public_cases.py tests/unit/test_martinluk_public_validator.py` | PASS, exited 0 |
| Active strategy guardrail | `git diff --exit-code -- src/strategies/active_strategy.py` | PASS, no active-strategy diff |
| Dependency guardrail | `git diff --exit-code -- pyproject.toml uv.lock` | PASS, no dependency manifest diff |

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

## Diagnostic trace coverage

The Phase 3 validator/test lane verifies synthetic reproduced signal traces with
diagnostics present directly on each `signals[]` entry. Matched reproduced
signals require R-multiple, MAE/MFE values and units, stop-width percentage,
entry type, trim type, exit type, and a holding-period field. The tests also
cover the approved open-trade exception for nullable exit-dependent diagnostics
when `exit_type == "open"`, and explicit failures when MAE/MFE values are
provided without units.

The public insufficient-evidence fixture remains a research-bound non-pass: it
returns `insufficient_evidence` with zero `not_reproduced` cases, preserving the
Phase 2 boundary that public cases without exact fills/timestamps must not pass
silently.

## Accepted evidence artifacts

- `specs/004-martinluk-primitive/contracts/public-operation-validator-contract.md`
  — documents direct signal-entry diagnostic fields and the schema-version
  decision gate for future semantic or placement changes.
- `specs/004-martinluk-primitive/validate_public_cases.py` — enforces matched
  reproduced-signal diagnostic requirements and reports `diagnostic_errors` in
  `signal_validation`.
- `tests/unit/test_martinluk_public_validator.py` — focused synthetic schema and
  diagnostic tests, kept separate from real public-case evidence.
- `specs/004-martinluk-primitive/fixtures/signal-trace-public-cases-insufficient-evidence.json`
  — preserves the explicit unsupported-public-case behavior.

## Remaining risks / non-claims

- Diagnostic schema coverage is validator-level only; no production strategy
  trace has been emitted by `src/strategies/active_strategy.py` in this phase.
- Public reconstructed cases still lack exact intraday timestamps, broker fills,
  partial sizes, stop adjustments, slippage/fees, margin, and account equity.
- `src/strategies/active_strategy.py` was intentionally not edited.
