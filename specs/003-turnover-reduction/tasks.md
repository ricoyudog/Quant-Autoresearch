# Tasks: Turnover Reduction Confirmation Bars

**Input**: Design documents from `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/`
**Prerequisites**: `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/plan.md`, `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/spec.md`, `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/research.md`, `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/data-model.md`, `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/contracts/strategy-confirmation-signal-contract.md`, `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/quickstart.md`

**Tests**: Tests are required because the specification and plan explicitly call for test-first validation of strategy behavior changes.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently where possible, while acknowledging shared-file sequencing for the active strategy.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes an exact file path

## Path Conventions

- Strategy code lives in `/Users/chunsingyu/softwares/Quant-Autoresearch/src/strategies/`
- Unit tests live in `/Users/chunsingyu/softwares/Quant-Autoresearch/tests/unit/`
- Experiment planning artifacts live in `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/`
- Obsidian knowledge-capture artifacts live in `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/`

## Phase 1: Setup (Shared Context)

**Purpose**: Anchor the implementation against the current stable baseline and existing knowledge trail before editing code.

- [X] T001 [P] Review the current bounded comparison command and acceptance thresholds in `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/quickstart.md`
- [X] T002 [P] Review the latest stable baseline trail in `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/experiment-index.md` and `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/2026-04-14-regime-gate-bear-volatile.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prepare the shared test surface that all user stories depend on.

**⚠️ CRITICAL**: No user story implementation should begin until this phase is complete.

- [X] T003 Add reusable confirmation-window and hostile-regime fixture helpers in `/Users/chunsingyu/softwares/Quant-Autoresearch/tests/unit/test_strategy_interface.py`

**Checkpoint**: Shared strategy test fixtures are ready; story-specific red/green work can begin.

---

## Phase 3: User Story 1 - Reduce fee-driven overtrading (Priority: P1) 🎯 MVP

**Goal**: Delay non-hostile entries and reversals until raw momentum has held direction for the required confirmation sequence.

**Independent Test**: Run `uv run pytest /Users/chunsingyu/softwares/Quant-Autoresearch/tests/unit/test_strategy_interface.py -q` and confirm the new confirmation-bar tests pass while the bounded comparison command remains available in `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/quickstart.md`.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests first, ensure they fail for the expected reason, then implement the strategy change.**

- [X] T004 [US1] Add failing unit tests for delayed long/short confirmation and configurable confirmation length in `/Users/chunsingyu/softwares/Quant-Autoresearch/tests/unit/test_strategy_interface.py`

### Implementation for User Story 1

- [X] T005 [US1] Implement the confirmation-bar parameter and non-hostile confirmation filter in `/Users/chunsingyu/softwares/Quant-Autoresearch/src/strategies/active_strategy.py`
- [X] T006 [US1] Re-run the focused strategy-interface verification from `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/quickstart.md` and reconcile any command drift in that same file

**Checkpoint**: Non-hostile trades require confirmation before positions are emitted.

---

## Phase 4: User Story 2 - Preserve hostile-regime protection (Priority: P2)

**Goal**: Keep the bear-volatile flattening rule authoritative and ensure missing SPY context still falls back to neutral behavior.

**Independent Test**: Force hostile and SPY-missing contexts in `tests/unit/test_strategy_interface.py` and verify that hostile intervals stay flat while neutral fallback still permits confirmed trading.

### Tests for User Story 2 ⚠️

- [X] T007 [US2] Add failing unit tests for bear-volatile precedence over confirmation and neutral fallback without SPY context in `/Users/chunsingyu/softwares/Quant-Autoresearch/tests/unit/test_strategy_interface.py`

### Implementation for User Story 2

- [X] T008 [US2] Update regime-aware signal flow in `/Users/chunsingyu/softwares/Quant-Autoresearch/src/strategies/active_strategy.py` so hostile flattening overrides confirmation while missing SPY context remains neutral
- [X] T009 [US2] Re-run `uv run pytest /Users/chunsingyu/softwares/Quant-Autoresearch/tests/unit/test_strategy_interface.py -q` and confirm alignment with `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/contracts/strategy-confirmation-signal-contract.md`

**Checkpoint**: Hostile-regime protection remains intact after the turnover-reduction change.

---

## Phase 5: User Story 3 - Produce a clean next-step decision (Priority: P3)

**Goal**: Generate a comparable experiment result and record it so the next session can decide keep/rework/reject without reconstructing context.

**Independent Test**: Execute the bounded comparison backtest, compare the result to the current stable baseline, and update the experiment trail so the decision and next experiment are explicit.

### Tests for User Story 3 ⚠️

- [X] T010 [US3] Run the bounded comparison backtest from `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/quickstart.md` against `/Users/chunsingyu/softwares/Quant-Autoresearch/src/strategies/active_strategy.py` and inspect the new row in `/Users/chunsingyu/softwares/Quant-Autoresearch/experiments/results.tsv`

### Implementation for User Story 3

- [X] T011 [P] [US3] Write the experiment outcome note at `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/2026-04-14-turnover-reduction-confirmation-bars.md`
- [X] T012 [P] [US3] Update the baseline/next-step map in `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/experiment-index.md`
- [X] T013 [US3] Append the decision summary and follow-up pointer to `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/research/2026-04-13-daily-research-kickoff.md`

**Checkpoint**: The experiment is comparable, classified, and reusable by the next research session.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation hygiene, and reusable knowledge updates.

- [X] T014 [P] Run `uv run python -m compileall /Users/chunsingyu/softwares/Quant-Autoresearch/src/strategies/active_strategy.py` and `git diff --check`, then align any command/result drift in `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/quickstart.md`
- [X] T015 [P] If the experiment is kept, update `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/knowledge/strategy-pattern-catalog.md` with the confirmation-bar finding
- [X] T016 Validate the final knowledge trail across `/Users/chunsingyu/softwares/Quant-Autoresearch/experiments/results.tsv`, `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/experiment-index.md`, and `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/003-turnover-reduction/quickstart.md` before handoff

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies
- **Phase 2: Foundational** — depends on Phase 1 and blocks all story work
- **Phase 3: User Story 1** — depends on Phase 2
- **Phase 4: User Story 2** — depends on Phase 3 because it reuses the same strategy and test surfaces while preserving the new confirmation logic
- **Phase 5: User Story 3** — depends on Phases 3 and 4 because it evaluates the final combined behavior
- **Phase 6: Polish** — depends on all desired story work being complete

### User Story Dependencies

- **US1 (P1)**: First deliverable; establishes the confirmation-bar behavior
- **US2 (P2)**: Extends the same strategy module, so it should land after US1 even though its behavior is independently testable
- **US3 (P3)**: Depends on the final US1+US2 behavior because it records and judges the completed experiment

### Within Each User Story

- Tests must be written and observed failing before implementation
- Strategy code changes follow the red tests
- Focused verification follows each code change before moving to the next story
- Experiment logging follows successful bounded comparison results

### Parallel Opportunities

- T001 and T002 can run in parallel during Setup
- T011 and T012 can run in parallel after T010 because they update different Obsidian files from the same verified result
- T014 and T015 can run in parallel after the experiment decision is known because they touch different files

---

## Parallel Example: User Story 3

```bash
# After the bounded comparison result is available:
Task: "Write the experiment outcome note at /Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/2026-04-14-turnover-reduction-confirmation-bars.md"
Task: "Update the baseline/next-step map in /Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch/experiments/experiment-index.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup
2. Complete Foundational fixtures
3. Complete User Story 1
4. Run the focused strategy-interface verification
5. Compare early bounded results before deciding whether to continue

### Incremental Delivery

1. Deliver confirmation bars in non-hostile conditions (US1)
2. Re-assert hostile-regime and neutral-fallback behavior (US2)
3. Record the comparison result and next-step decision in the knowledge trail (US3)
4. Finish with compile/diff hygiene and pattern-catalog updates

### Suggested MVP Scope

The suggested MVP scope is **User Story 1 only** because it answers the core research question — whether confirmation bars reduce fee-driven overtrading — with the smallest reversible strategy change.

## Notes

- All tasks follow the required checklist format.
- Tasks touching the same files are intentionally sequential to avoid self-conflicts in the active strategy and its unit-test surface.
- Obsidian update tasks use exact vault paths so the experiment trail remains reproducible across sessions.
