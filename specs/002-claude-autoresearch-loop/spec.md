# Feature Specification: Claude Code Autoresearch Loop

**Feature Branch**: `002-claude-autoresearch-loop`  
**Created**: 2026-04-13  
**Status**: Draft  
**Input**: User description: "設計一個像 Karpathy autoresearch 一樣、由 Claude Code 作為外部 agent 驅動的多輪 autoresearch 方案"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a repeatable multi-round autoresearch loop (Priority: P1)

As a research operator, I want to launch a Claude Code-driven autoresearch run with a fixed iteration budget so that the system can complete multiple strategy-improvement rounds without requiring manual orchestration after every round.

**Why this priority**: A repeatable multi-round loop is the core value of the feature. Without it, the repository still behaves like a collection of manual primitives instead of an autoresearch system.

**Independent Test**: Start a bounded run, observe at least two completed rounds, and verify that each round records its hypothesis, backtest result, and keep/revert decision without requiring manual edits between rounds.

**Acceptance Scenarios**:

1. **Given** the operator starts a bounded autoresearch run, **When** the system finishes multiple rounds, **Then** each round is executed in order with a persistent state record and a final run summary.
2. **Given** a round fails to improve on the current best strategy, **When** the round ends, **Then** the system records the failure and continues or stops according to the configured stop rules without leaving the strategy in an unreviewed intermediate state.

---

### User Story 2 - Keep or revert strategy changes from evaluator output (Priority: P2)

As a research operator, I want the loop to decide keep versus revert from deterministic evaluation results so that Claude Code can propose strategy changes without directly owning the final acceptance decision.

**Why this priority**: The evaluator must remain the truth surface. This protects the loop from agent optimism, silent regressions, and uncontrolled drift.

**Independent Test**: Run one improving round and one non-improving round; verify the improving change is retained and the non-improving change is reverted, with both decisions backed by recorded metrics.

**Acceptance Scenarios**:

1. **Given** a round produces a backtest result above the required threshold, **When** the result is parsed, **Then** the system records a keep decision and updates the best-known strategy state.
2. **Given** a round does not exceed the required threshold, **When** the result is parsed, **Then** the system restores the prior strategy state and records a revert decision with the reason.

---

### User Story 3 - Resume and audit prior runs (Priority: P3)

As a maintainer, I want a stopped or interrupted autoresearch run to be resumable from persisted state so that long-running research sessions remain auditable and do not lose prior progress.

**Why this priority**: Multi-round research is only practical if runs can survive interruption and still produce a trustworthy history.

**Independent Test**: Interrupt a run after one completed round, resume it, and verify the next round starts from the persisted best-known state rather than from an implicit reset.

**Acceptance Scenarios**:

1. **Given** a prior run has persisted state and iteration artifacts, **When** the operator resumes the run, **Then** the system restores the current iteration number, best-known result, and prior decisions before continuing.
2. **Given** a maintainer reviews a completed run, **When** they inspect the run artifacts, **Then** they can reconstruct each round's hypothesis, outcome, and strategy decision path.

### Edge Cases

- What happens when Claude Code edits the strategy file but the evaluation command crashes before a decision can be recorded?
- How does the loop behave when a round produces no valid backtest metrics or malformed output?
- What happens when the run hits the stop condition on a non-improving streak before the maximum iteration budget is reached?
- How is resume handled if state exists but the current strategy file no longer matches the recorded best-known baseline?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a bounded multi-round autoresearch run driven by Claude Code as an external research agent.
- **FR-002**: The system MUST treat the deterministic backtest and validation surfaces as the final authority for keep versus revert decisions.
- **FR-003**: The system MUST persist run-level state that records the current iteration, best-known result, most recent decision, and stop-condition progress.
- **FR-004**: The system MUST persist per-iteration artifacts that capture the hypothesis, strategy change summary, evaluation outcome, and keep/revert decision.
- **FR-005**: The system MUST create a recoverable strategy snapshot before each round so that non-qualifying changes can be reverted automatically.
- **FR-006**: The system MUST update the retained strategy state only after a round satisfies the configured keep rule.
- **FR-007**: The system MUST support operator-configured stop conditions, including an iteration budget and a no-improvement limit.
- **FR-008**: The system MUST support resuming an interrupted autoresearch run from persisted state without discarding previously completed rounds.
- **FR-009**: The system MUST keep the Claude Code responsibility limited to research and strategy proposal work; the final acceptance decision MUST remain outside the agent.
- **FR-010**: The system MUST write enough run history that a maintainer can audit why each round was kept, reverted, or terminated.
- **FR-011**: The system MUST allow research context from existing repository surfaces, including notes, prior results, and deterministic analysis outputs, to inform each round.
- **FR-012**: The system MUST keep the repository's fixed evaluator and strategy-under-iteration surfaces recognizable, so the design remains aligned with a Karpathy-style outer-loop model rather than an embedded agent framework.

### Key Entities *(include if feature involves data)*

- **Autoresearch Run**: The top-level research session that tracks iteration budget, stop conditions, current status, and best-known outcome.
- **Iteration Record**: A single completed or failed round containing hypothesis, strategy-change summary, evaluator output, and final keep/revert decision.
- **Strategy Snapshot**: The reversible copy of the strategy-under-iteration taken before a round begins.
- **Decision Record**: The normalized keep/revert outcome derived from evaluator metrics and decision rules.
- **Run State**: The persisted resume surface that tracks current iteration number, no-improvement streak, best-known score, and run status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can start a bounded autoresearch run that completes at least 3 consecutive rounds without manual orchestration between rounds.
- **SC-002**: 100% of completed rounds produce an auditable iteration artifact with hypothesis, evaluation result, and final keep/revert decision.
- **SC-003**: 100% of non-qualifying rounds restore the pre-round strategy state before the next round begins.
- **SC-004**: A stopped run can be resumed with no loss of previously completed iteration records and with the correct next iteration number.
- **SC-005**: A maintainer can determine within 10 minutes why the latest retained strategy version was kept by reading the persisted run state and iteration artifacts alone.

## Assumptions

- Claude Code is available as the external research agent and can be invoked repeatedly by an outer orchestration layer.
- The repository's current deterministic evaluator surfaces remain the authoritative source of backtest and validation outcomes.
- The strategy-under-iteration continues to be represented by a bounded, reviewable strategy file rather than by a dynamic multi-file code generation surface.
- The first implementation targets a single-runner workflow and does not attempt multi-agent parallel search.
- Research runs may legitimately plateau or regress for multiple rounds; monotonic improvement is not assumed.
