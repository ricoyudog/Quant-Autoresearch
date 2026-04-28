# Phase 2 Acceptance Review: T006-T009

Generated: 2026-04-28T05:05:00Z

Scope: review whether Phase 2 public-case reproduction validator work is ready to
use as a gate before any `src/strategies/active_strategy.py` mutation.

## Verdict summary

| Task | Acceptance verdict | Evidence | Gaps / risks |
| --- | --- | --- | --- |
| T006 Add signal-trace input support | **Implemented for schema + deterministic matching, but bounded** | `validate_public_cases.py` accepts `--signals-path`, validates schema/replication target/signals list, classifies each case, and unit tests cover reproduced, insufficient evidence, and data-missing paths. | Matching only parses exact `YYYY-MM-DD`, `YYYY-MM-DD..YYYY-MM-DD`, slash ranges, list pairs, or dict windows. Current public reconstructed windows are descriptive `reconstructed_candidate:` strings, so real public cases classify as `insufficient_evidence` until machine-readable windows or trace semantics are added. |
| T007 Define expected windows for SOFI, AMC, COIN, LMND, SMCI | **Materially complete as candidate public windows, not exact fills** | `public-operation-cases.json` now has `date_reconstruction` for all five cases and `public-date-reconstruction.md` cites source IDs plus daily-bar alignment. | Windows are reconstructed candidates from public interview/chart clues and daily bars. Exact entry/trim/exit fills, intraday timestamps, and broker data remain unavailable. Do not mark as private-ledger replication. |
| T008 Add fixtures or trace examples for at least five public cases | **Partially complete / research-only** | `fixtures/signal-trace-public-cases-insufficient-evidence.json` names the five target cases and verifies the no-private-fill path. `tests/unit/test_martinluk_public_validator.py` has synthetic happy-path signal reproduction for five exact-date cases. | There is no positive real-public trace fixture that reproduces SOFI/AMC/COIN/LMND/SMCI, because exact trace dates/fills are still unsupported and current descriptive windows are not machine-parseable. |
| T009 Verify unsupported cases report missing evidence instead of failing silently | **Complete for current Phase 2 boundary** | Focused unit test `test_public_fixture_keeps_unknown_dates_insufficient`; command with public fixture returns `status: insufficient_evidence`, `classification_counts.insufficient_evidence: 8`, `not_reproduced: 0`, and lists unsupported cases. | Exit code is non-zero because the validator correctly refuses to pass without five reproduced cases. Automation must treat `insufficient_evidence` as a research-only stop, not as a test pass. |

## Command evidence

- `python3 specs/004-martinluk-primitive/validate_public_cases.py` -> PASS,
  `status: passed`, `case_count: 8`, `source_count: 9`, `errors: []`.
- `python3 specs/004-martinluk-primitive/validate_public_cases.py --signals-path specs/004-martinluk-primitive/fixtures/signal-trace-public-cases-insufficient-evidence.json`
  -> expected non-pass research-only result, `status: insufficient_evidence`,
  all eight cases classified as `insufficient_evidence`, zero `not_reproduced`.
- `uv run pytest tests/unit/test_martinluk_public_validator.py -q` -> PASS,
  `4 passed in 0.02s`.
- `uv run python -m py_compile specs/004-martinluk-primitive/validate_public_cases.py tests/unit/test_martinluk_public_validator.py`
  -> PASS.
- `git diff --exit-code -- pyproject.toml uv.lock` -> PASS, no dependency
  manifest changes.

## Recommendation

Phase 2 is safe as a **research gate**: it blocks silent private-ledger claims,
records candidate windows, and proves unsupported public cases remain explicit.
It is not yet a production reproduction gate for strategy mutation. Before using
it to approve `leader_pullback_orh` behavior, add either:

1. machine-readable `date_window` fields for reconstructed candidate windows, or
2. a validator-aware `date_reconstruction` matching path that can distinguish
   candidate public windows from exact execution fills.

Until then, any downstream run with real public cases should stop at
`insufficient_evidence` unless a future source supplies exact signal trace data.
