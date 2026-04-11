# Tasks: V2 Closeout Readiness

**Input**: Design documents from `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/001-v2-closeout/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: No new test-writing tasks are included because the specification does not request a TDD workflow. Existing verification commands are captured as execution tasks where needed for closeout evidence.

**Organization**: Tasks are grouped by user story so each story can be completed and reviewed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., `US1`, `US2`, `US3`)
- Every task includes an exact file path

## Path Conventions

- Planning artifacts live under `specs/001-v2-closeout/`
- Canonical closeout deliverables live under `docs/v2-closeout/`
- Existing repository status records to reconcile live under `docs/feature/` and `docs/upgrade-plan-v2.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the canonical closeout workspace that all later story work will update.

- [x] T001 Create the closeout workspace directory and seed the executive summary file at `docs/v2-closeout/README.md`
- [x] T002 [P] Create the branch/integration evidence file at `docs/v2-closeout/integration.md`
- [x] T003 [P] Create the verification evidence file at `docs/v2-closeout/verification.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared closeout structure and gate definitions before user-story work begins.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [x] T004 Define the canonical V2 workstream inventory and completion-standard sections in `docs/v2-closeout/README.md`
- [x] T005 [P] Add the branch ancestry, merge disposition, and evidence-reference templates to `docs/v2-closeout/integration.md`
- [x] T006 [P] Add the verification baseline, failing-suite, and evidence-reference templates to `docs/v2-closeout/verification.md`

**Checkpoint**: The closeout package skeleton exists and is ready to receive evidence.

---

## Phase 3: User Story 1 - Determine release readiness (Priority: P1) 🎯 MVP

**Goal**: Build a canonical readiness view that lets a reviewer decide whether V2 is complete without reading every historical planning file first.

**Independent Test**: A reviewer can open `docs/v2-closeout/README.md`, `docs/v2-closeout/integration.md`, and `docs/v2-closeout/verification.md` and determine the current V2 readiness state in under 15 minutes.

### Implementation for User Story 1

- [x] T007 [US1] Inventory all in-scope V2 workstreams and their source records in `docs/v2-closeout/README.md`
- [x] T008 [P] [US1] Capture merged and unmerged V2 branch ancestry evidence in `docs/v2-closeout/integration.md`
- [x] T009 [P] [US1] Capture the current `pytest` baseline and failing-suite summary in `docs/v2-closeout/verification.md`
- [x] T010 [US1] Classify each V2 workstream as `complete`, `open`, or `intentionally_deferred` and write the executive readiness summary in `docs/v2-closeout/README.md`

**Checkpoint**: User Story 1 is complete when the closeout package clearly states whether V2 is currently complete, incomplete, or conditionally blocked.

---

## Phase 4: User Story 2 - Resolve outstanding blockers (Priority: P2)

**Goal**: Convert the observed blockers into explicit closeout actions with evidence-backed dispositions.

**Independent Test**: Starting from the closeout package, a contributor can list every open blocker, the required next action, and the proof needed to close it.

### Implementation for User Story 2

- [x] T011 [US2] Record blocker categories, severities, and required evidence for all open V2 findings in `docs/v2-closeout/README.md`
- [x] T012 [US2] Update legacy overfit test expectations in `tests/unit/test_backtester_overfit.py` to match the supported V2 minute-runtime contract
- [x] T013 [P] [US2] Document the disposition and required evidence for `feature/v2-research` and `feature/v2-minute-autoresearch` in `docs/v2-closeout/integration.md`
- [x] T014 [US2] Refresh the blocker table and next-action summary in `docs/v2-closeout/README.md` using the outcomes from `tests/unit/test_backtester_overfit.py` and `docs/v2-closeout/integration.md`

**Checkpoint**: User Story 2 is complete when every blocker has a concrete next action and test-related blockers no longer rely on obsolete expectations.

---

## Phase 5: User Story 3 - Validate canonical status (Priority: P3)

**Goal**: Reconcile contradictory V2 status records so the canonical closeout package matches the checked-in documentation surface.

**Independent Test**: A reviewer can compare the canonical closeout package against the updated source documents and find no unresolved status contradiction in the targeted files.

### Implementation for User Story 3

- [x] T015 [P] [US3] Align the umbrella V2 session/status summary in `docs/upgrade-plan-v2.md` with the canonical closeout state
- [x] T016 [P] [US3] Align `docs/feature/v2-research/README.md` and `docs/feature/v2-research/v2-research-development-plan.md` with the canonical workstream state
- [x] T017 [P] [US3] Align status tables in `docs/feature/v2-phase1/README.md`, `docs/feature/v2-cleanup/README.md`, and `docs/feature/v2-phase3/README.md` with the canonical workstream state
- [x] T018 [US3] Reconcile any remaining status conflicts and update the final completion-standard narrative in `docs/v2-closeout/README.md`

**Checkpoint**: User Story 3 is complete when the targeted V2 planning/status documents agree with the canonical closeout package.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Re-run the readiness checks and finalize the closeout package for review.

- [x] T019 [P] Re-run branch ancestry verification and append the final evidence snapshot to `docs/v2-closeout/integration.md`
- [x] T020 [P] Re-run the repository test gate and append the final verification snapshot to `docs/v2-closeout/verification.md`
- [x] T021 Validate `docs/v2-closeout/README.md` against `specs/001-v2-closeout/contracts/closeout-artifact-contract.md` and finalize the readiness outcome in `docs/v2-closeout/README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies
- **Phase 2: Foundational** — depends on Phase 1 and blocks all user stories
- **Phase 3: User Story 1** — depends on Phase 2
- **Phase 4: User Story 2** — depends on Phase 3 because blocker resolution relies on the canonical inventory and evidence baseline
- **Phase 5: User Story 3** — depends on Phase 3 and should follow Phase 4 if blocker outcomes change final status wording
- **Phase 6: Polish** — depends on completion of all desired user stories

### User Story Dependencies

- **User Story 1 (P1)**: No story dependencies once foundational work is done
- **User Story 2 (P2)**: Depends on User Story 1's canonical inventory and evidence capture
- **User Story 3 (P3)**: Depends on User Story 1's canonical inventory; should be finalized after User Story 2 if blocker resolution changes status labels

### Within Each User Story

- Evidence capture before executive summary updates
- Canonical inventory before blocker classification
- Blocker resolution before final status reconciliation
- Final verification before final readiness claim

## Parallel Opportunities

- `T002` and `T003` can run in parallel after `T001`
- `T005` and `T006` can run in parallel after `T004`
- `T008` and `T009` can run in parallel after Phase 2
- `T013` can run in parallel with `T012` after `T011`
- `T015`, `T016`, and `T017` can run in parallel after User Story 2 is stable
- `T019` and `T020` can run in parallel before `T021`

---

## Parallel Example: User Story 1

```bash
# Capture integration and verification evidence at the same time:
Task: "Capture merged and unmerged V2 branch ancestry evidence in docs/v2-closeout/integration.md"
Task: "Capture the current pytest baseline and failing-suite summary in docs/v2-closeout/verification.md"
```

---

## Parallel Example: User Story 3

```bash
# Reconcile independent status documents in parallel:
Task: "Align the umbrella V2 session/status summary in docs/upgrade-plan-v2.md with the canonical closeout state"
Task: "Align docs/feature/v2-research/README.md and docs/feature/v2-research/v2-research-development-plan.md with the canonical workstream state"
Task: "Align status tables in docs/feature/v2-phase1/README.md, docs/feature/v2-cleanup/README.md, and docs/feature/v2-phase3/README.md with the canonical workstream state"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and verify that the canonical closeout package alone answers the readiness question

### Incremental Delivery

1. Ship the canonical readiness package first (User Story 1)
2. Resolve blockers and stale verification assumptions next (User Story 2)
3. Reconcile the remaining checked-in status records last (User Story 3)
4. Run final evidence capture and contract validation in Phase 6

### Suggested MVP Scope

The suggested MVP scope is **User Story 1 only** because it delivers the first canonical answer to “is V2 complete?” and establishes the inventory needed by all follow-on work.

## Notes

- All tasks use the required checklist format.
- Tasks marked `[P]` target different files and can be delegated safely.
- No new dependencies are introduced by this task plan.
- Existing verification commands are treated as evidence-generation steps, not as new test-authoring work.
