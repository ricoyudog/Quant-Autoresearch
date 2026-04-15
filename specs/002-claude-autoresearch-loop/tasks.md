# Tasks: Claude Code Autoresearch Loop

**Input**: Design documents from `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/002-claude-autoresearch-loop/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: This feature needs verification tasks because the spec explicitly requires bounded multi-round execution, keep/revert correctness, and resume behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., `US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Path Conventions

- Runner code: `scripts/`
- Strategy-under-iteration: `src/strategies/active_strategy.py`
- Existing deterministic runtime: `cli.py`, `src/core/backtester.py`, `src/core/research.py`
- Persistent loop artifacts: `experiments/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new autoresearch runner workspace and operator-facing entry surface.

- [x] T001 Create the runner package scaffolding in `scripts/autoresearch_runner.py` and `scripts/run_claude_iteration.sh`
- [x] T002 [P] Create the iteration artifact directory contract under `experiments/iterations/.gitkeep`
- [x] T003 [P] Create the initial run-state schema file or template in `experiments/autoresearch_state.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared runner foundations that every user story depends on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [x] T004 Implement run-state load/save helpers in `scripts/autoresearch_runner.py`
- [x] T005 [P] Implement strategy snapshot and restore helpers for `src/strategies/active_strategy.py` in `scripts/autoresearch_runner.py`
- [x] T006 [P] Implement backtest-output parsing and decision normalization using `src/memory/idea_keep_revert.py` in `scripts/autoresearch_runner.py`
- [x] T007 Wire the Claude Code iteration invocation wrapper in `scripts/run_claude_iteration.sh`
- [x] T008 Add foundational unit coverage for run-state, snapshot, and decision parsing in `tests/unit/test_autoresearch_runner.py`

**Checkpoint**: The runner can persist state, snapshot the strategy, invoke Claude Code externally, and normalize evaluator output.

---

## Phase 3: User Story 1 - Run a repeatable multi-round autoresearch loop (Priority: P1) 🎯 MVP

**Goal**: Launch a bounded Claude Code-driven multi-round loop without manual orchestration between rounds.

**Independent Test**: Start a bounded run and verify at least two completed rounds are recorded with distinct iteration artifacts and an updated run state.

### Tests for User Story 1

- [x] T009 [P] [US1] Add a runner lifecycle unit test for bounded multi-round execution in `tests/unit/test_autoresearch_runner.py`
- [x] T010 [P] [US1] Add an integration-style dry-run test for the external iteration wrapper in `tests/integration/test_autoresearch_runner_integration.py`

### Implementation for User Story 1

- [x] T011 [US1] Implement bounded run initialization and iteration budgeting in `scripts/autoresearch_runner.py`
- [x] T012 [US1] Implement per-iteration context assembly from `program.md`, `experiments/results.tsv`, and recent notes in `scripts/autoresearch_runner.py`
- [x] T013 [US1] Implement iteration artifact writing for each completed round in `scripts/autoresearch_runner.py`
- [x] T014 [US1] Expose an operator launch path and documented arguments in `scripts/run_claude_iteration.sh`

**Checkpoint**: User Story 1 is complete when the runner can execute multiple rounds in sequence and persist structured round artifacts.

---

## Phase 4: User Story 2 - Keep or revert strategy changes from evaluator output (Priority: P2)

**Goal**: Enforce deterministic keep/revert decisions outside Claude Code.

**Independent Test**: Simulate one improving and one non-improving round; verify the improving change is retained and the non-improving change restores the prior strategy snapshot.

### Tests for User Story 2

- [x] T015 [P] [US2] Add a keep-path regression test for retained strategy updates in `tests/unit/test_autoresearch_runner.py`
- [x] T016 [P] [US2] Add a revert-path regression test for failed or non-improving rounds in `tests/unit/test_autoresearch_runner.py`

### Implementation for User Story 2

- [x] T017 [US2] Implement keep/revert decision application around `src/strategies/active_strategy.py` in `scripts/autoresearch_runner.py`
- [x] T018 [US2] Implement best-known-score and no-improvement tracking in `scripts/autoresearch_runner.py`
- [x] T019 [US2] Implement failure handling for malformed or missing evaluator output in `scripts/autoresearch_runner.py`

**Checkpoint**: User Story 2 is complete when the runner, not Claude Code, deterministically owns strategy retention decisions.

---

## Phase 5: User Story 3 - Resume and audit prior runs (Priority: P3)

**Goal**: Resume interrupted runs from persisted state and preserve a trustworthy audit trail.

**Independent Test**: Stop a run after one completed round, restart it, and confirm the next round continues from the persisted state and best-known baseline.

### Tests for User Story 3

- [x] T020 [P] [US3] Add a resume-state unit test in `tests/unit/test_autoresearch_runner.py`
- [x] T021 [P] [US3] Add an iteration-audit artifact test in `tests/integration/test_autoresearch_runner_integration.py`

### Implementation for User Story 3

- [x] T022 [US3] Implement resume-from-state behavior in `scripts/autoresearch_runner.py`
- [x] T023 [US3] Implement operator-facing run summaries and status reporting in `scripts/autoresearch_runner.py`
- [x] T024 [US3] Update `program.md` with the Claude Code outer-loop contract and operator expectations

**Checkpoint**: User Story 3 is complete when interrupted runs resume correctly and completed runs are audit-friendly.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation across all stories.

- [x] T025 [P] Document operator usage and stop-condition semantics in `README.md`
- [x] T026 [P] Run the full autoresearch runner verification matrix from `specs/002-claude-autoresearch-loop/quickstart.md`
- [x] T027 Validate the new runner against `specs/002-claude-autoresearch-loop/contracts/autoresearch-runner-contract.md` and summarize any residual risks in `specs/002-claude-autoresearch-loop/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies
- **Phase 2: Foundational** — depends on Phase 1 and blocks all user stories
- **Phase 3: User Story 1** — depends on Phase 2
- **Phase 4: User Story 2** — depends on User Story 1 because decision application needs the working multi-round lifecycle
- **Phase 5: User Story 3** — depends on User Story 1 and User Story 2 because resume must preserve the real keep/revert state
- **Phase 6: Polish** — depends on completion of all desired user stories

### User Story Dependencies

- **User Story 1 (P1)**: First runnable MVP after foundations
- **User Story 2 (P2)**: Extends the MVP with deterministic retention rules
- **User Story 3 (P3)**: Extends the MVP with resume and audit guarantees

### Within Each User Story

- Tests before behavior changes
- State and artifact plumbing before operator-facing summaries
- Decision parsing before keep/revert application
- Resume behavior after persisted state is stable

## Parallel Opportunities

- `T002` and `T003` can run in parallel after `T001`
- `T005`, `T006`, and `T007` can run in parallel after `T004`
- `T009` and `T010` can run in parallel
- `T015` and `T016` can run in parallel
- `T020` and `T021` can run in parallel
- `T025` and `T026` can run in parallel after all user stories are complete

---

## Parallel Example: User Story 1

```bash
# Launch the user-story 1 verification tasks together:
Task: "Add a runner lifecycle unit test for bounded multi-round execution in tests/unit/test_autoresearch_runner.py"
Task: "Add an integration-style dry-run test for the external iteration wrapper in tests/integration/test_autoresearch_runner.py"
```

---

## Parallel Example: Foundations

```bash
# Build independent foundation helpers in parallel:
Task: "Implement strategy snapshot and restore helpers for src/strategies/active_strategy.py in scripts/autoresearch_runner.py"
Task: "Implement backtest-output parsing and decision normalization using src/memory/idea_keep_revert.py in scripts/autoresearch_runner.py"
Task: "Wire the Claude Code iteration invocation wrapper in scripts/run_claude_iteration.sh"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup
2. Complete Foundations
3. Complete User Story 1
4. Verify that the runner can execute multiple rounds with persistent artifacts before moving on

### Incremental Delivery

1. Deliver a bounded multi-round runner first
2. Add deterministic keep/revert ownership second
3. Add resume and audit behavior third
4. Finish with documentation and full verification

### Suggested MVP Scope

The suggested MVP scope is **User Story 1 only** because it establishes the Claude Code outer-loop runner and proves that the repository can execute multiple rounds without manual orchestration.

## Notes

- All tasks follow the required checklist format.
- Tasks marked `[P]` are parallel-safe because they focus on separate test files, documentation files, or isolated helper work.
- This plan intentionally keeps Claude Code orchestration outside the repository runtime rather than introducing an embedded agent framework.
