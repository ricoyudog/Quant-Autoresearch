# Tasks: MartinLuk Leader Pullback / ORH Primitive

**Input**: Design artifacts from `specs/004-martinluk-primitive/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `source-ledger.json`, `public-operation-cases.json`, validator contract

**Tests**: Required before strategy mutation. Phase 0/1 uses ledger validation; implementation phase adds strategy-interface and signal-reproduction tests.

## Phase 1: Evidence Foundation

- [X] T001 Promote `.omx/specs/autoresearch-martinluk-primitive/source-ledger.json` into `specs/004-martinluk-primitive/source-ledger.json`
- [X] T002 Create `specs/004-martinluk-primitive/public-operation-cases.json` with at least seven public cases
- [X] T003 Document the replication boundary in `specs/004-martinluk-primitive/spec.md`
- [X] T004 Add validator contract at `specs/004-martinluk-primitive/contracts/public-operation-validator-contract.md`
- [X] T005 Add ledger validator script at `specs/004-martinluk-primitive/validate_public_cases.py`

## Phase 2: Public-Case Reproduction Validator

- [X] T006 Add signal-trace input support to `specs/004-martinluk-primitive/validate_public_cases.py`
- [X] T007 Define expected windows for SOFI, AMC, COIN, LMND, and SMCI after date reconstruction
- [X] T008 Add fixtures or trace examples for at least five public cases
- [X] T009 Verify unsupported cases report missing evidence instead of failing silently

Phase 2 closeout note: T007/T008 are complete as a public-evidence research gate,
not as positive private-ledger reproduction. The current public fixture proves
the validator stops at `insufficient_evidence` when exact fills/timestamps remain
unsupported; see `phase2-acceptance-review.md` for gaps before strategy mutation.

## Phase 3: Strategy Diagnostics

- [X] T010 Add or expose R-multiple, MAE/MFE, stop width, entry type, trim type, exit type, and holding period diagnostics
- [X] T011 Add tests that diagnostics are present in the candidate report or signal trace

Phase 3 closeout note: T010/T011 are complete for the validator signal-trace
contract. Diagnostics are required on matched reproduced `signals[]` entries and
focused tests cover required fields, unit errors, and the open-trade nullable
exception; see `phase3-verification.md`. This is not a claim that
`active_strategy.py` emits production MartinLuk traces yet.

## Phase 4: Dry-Run Primitive Implementation

- [X] T012 Run GitNexus impact analysis for `src/strategies/active_strategy.py` symbols before editing
- [X] T013 Add failing strategy-interface tests for leader universe, ORH/IRH entry, hard stop, and 9 EMA exit
- [X] T014 Implement `leader_pullback_orh` behavior in `src/strategies/active_strategy.py`
- [X] T015 Run `pytest tests/unit/test_strategy_interface.py -q`
- [X] T016 Run `python3 specs/004-martinluk-primitive/validate_public_cases.py --signals-path <trace>`

Phase 4 verification note (2026-05-02): T012-T016 are complete as bounded
base-strategy verification. GitNexus impact analysis was run before any
strategy-symbol edit consideration; no strategy code change was required in
this pass. Focused strategy-interface tests passed (`36 passed`), MartinLuk
focused validator/replay/no-overclaim tests passed (`118 passed`), compile/JSON
validation passed, the active strategy emitted validator-compatible long/short
smoke traces, and the public-case validator correctly stayed
`insufficient_evidence` for missing primary dates/fills/account context. See
`phase4-base-strategy-verification.md`.

## Phase 5: Bounded Validation and Replay Gate

- [X] T017 Add frozen bounded validation manifest and dry-run report artifacts
- [X] T018 Preserve public-case reproduction status before any aggregate scoring
- [X] T019 Record Phase 5 dry-run result in repo report artifacts
- [ ] T020 Launch bounded autoresearch only after validator, focused tests, and replay gates pass

Phase 5 closeout note: T017-T019 are complete as bounded dry-run evidence only.
The report stays `research_only`/`promoted=false`, records zero market-data
queries, and does not prove profit, exact fills, private-account replication, or
broad historical validity. T020 remains blocked after the 2026-05-02 Phase 4
base-strategy verification because public-case validator evidence remains
`insufficient_evidence` for missing primary exact dates/fills/account context,
even though bounded validation/replay check-only contracts pass.

## Phase 5.1: Bounded Data Replay

- [X] T021 Add `phase5-1-replay-request.json` with frozen manifest hash and allowed loader/runner contract
- [X] T022 Add separate `run_phase5_bounded_replay.py` runner without backtester, validator orchestration, or `select_universe`
- [X] T023 Generate `phase5-1-query-ledger.json`, `phase5-1-runtime.json`, and bounded replay report artifacts
- [X] T024 Add focused Phase 5.1 unit and integration tests for hash fail-closed, query union, audit exclusion, control semantics, and artifact immutability
- [X] T025 Verify Phase 5 dry-run artifacts and `active_strategy.py` remain unchanged

Phase 5.1 closeout note: the replay remains strictly bounded to the 25 executable
manifest rows; audit-only rows do not query market data; controls are diagnostic
only; realized outcome fields stay `N/A`; and the generated report remains
`research_only`/`promoted=false`. This is not a Phase 5 broad backtest, optimizer,
profit proof, or exact-fill replication.

## Parallelization Notes

- T006/T007 can run in parallel with source-date reconstruction if files are disjoint.
- Strategy edits in T014 are shared-file work and should stay local or single-owner.
- Broad backtests depend on validator and tests; do not parallelize them before prerequisites pass.
