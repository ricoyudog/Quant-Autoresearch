## ADDED Requirements

### Requirement: Observer ingests repo-local run and iteration sources
The system SHALL ingest the current run state, per-iteration artifacts, per-iteration logs, and results ledger data from the local repository.

#### Scenario: Observer reads all required source classes
- **WHEN** the dashboard backend refreshes the active run
- **THEN** it reads `experiments/autoresearch_state.json`, relevant files under `experiments/iterations/<run_id>/`, and `experiments/results.tsv` to build dashboard state

### Requirement: Observer prioritizes source freshness by role
The system SHALL treat logs as the primary heartbeat source, structured artifacts as the primary semantic source, and the results ledger as the confirmation source for landed metrics.

#### Scenario: Heartbeat appears before ledger confirmation
- **WHEN** new log output exists for an active iteration but no new ledger row has been written yet
- **THEN** the dashboard still marks the run as active based on log freshness while deferring ledger-confirmed metric state until results data arrives

#### Scenario: Structured meaning appears after raw activity
- **WHEN** `decision.json` or `iteration_record.json` is written after earlier log activity
- **THEN** the observer enriches the affected iteration with hypothesis, decision, and summary fields without losing earlier heartbeat context

### Requirement: Observer normalizes run and iteration statuses
The system SHALL map raw repo signals into normalized run and iteration statuses for the dashboard.

#### Scenario: Run status is normalized from repo signals
- **WHEN** the observer evaluates state timestamps, log freshness, stop reasons, and artifact completion
- **THEN** it emits one run status from `Healthy`, `Busy`, `Waiting`, `Stalled`, `Failed`, `Blocked`, or `Completed`

#### Scenario: Iteration status is normalized from artifact progress
- **WHEN** the observer evaluates the selected iteration’s artifact and decision state
- **THEN** it emits one iteration status from `Queued`, `In Progress`, `Decision Pending`, `Evaluated`, `Kept`, `Reverted`, `Follow-up`, or `Failed`

### Requirement: Observer explains abnormal health conditions
The system SHALL provide enough diagnosis context for the dashboard to explain why a run appears stalled, blocked, or failed.

#### Scenario: Stalled run includes diagnosis signals
- **WHEN** the observer classifies a run as stalled
- **THEN** it includes the affected iteration, time since last heartbeat, and the stale signal used for classification so the dashboard can explain the condition without exposing raw file parsing details

#### Scenario: Blocked or failed run includes source reason
- **WHEN** the observer classifies a run as blocked or failed
- **THEN** it includes the underlying stop or failure reason from the repo state or decision artifacts in normalized dashboard state
