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

- [ ] T012 Run GitNexus impact analysis for `src/strategies/active_strategy.py` symbols before editing
- [ ] T013 Add failing strategy-interface tests for leader universe, ORH/IRH entry, hard stop, and 9 EMA exit
- [ ] T014 Implement `leader_pullback_orh` behavior in `src/strategies/active_strategy.py`
- [ ] T015 Run `pytest tests/unit/test_strategy_interface.py -q`
- [ ] T016 Run `python3 specs/004-martinluk-primitive/validate_public_cases.py --signals-path <trace>`

## Phase 5: Bounded Backtest and Autoresearch Gate

- [ ] T017 Run a no-leverage bounded backtest with the new primitive
- [ ] T018 Compare public-case reproduction before aggregate score
- [ ] T019 Record result in Obsidian and repo report artifacts
- [ ] T020 Launch bounded autoresearch only after validator and focused tests pass

## Parallelization Notes

- T006/T007 can run in parallel with source-date reconstruction if files are disjoint.
- Strategy edits in T014 are shared-file work and should stay local or single-owner.
- Broad backtests depend on validator and tests; do not parallelize them before prerequisites pass.
