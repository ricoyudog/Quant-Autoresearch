## ADDED Requirements

### Requirement: Dashboard shows active run health first
The system SHALL provide a home page that surfaces the active run’s health before any secondary dashboard content.

#### Scenario: Healthy run summary is visible on page load
- **WHEN** the operator opens the dashboard while an active run has fresh state or log activity
- **THEN** the dashboard shows the run identifier, normalized status, active iteration, latest update time, and heartbeat freshness in a dedicated top-level run-health region

#### Scenario: Blocked or failed run is summarized clearly
- **WHEN** the observer detects a blocked, failed, or completed run state
- **THEN** the run-health region shows the normalized status and the associated stop or failure reason without requiring the operator to inspect raw files

### Requirement: Dashboard presents a timeline of active-run iterations
The system SHALL present the active run as a timeline of iterations that emphasizes research-direction evolution and risk-adjusted change over time.

#### Scenario: Latest iteration is selected by default
- **WHEN** the dashboard loads an active run with one or more completed or in-progress iterations
- **THEN** the latest iteration is selected automatically and highlighted in the timeline

#### Scenario: Timeline nodes summarize key iteration signals
- **WHEN** an iteration has enough structured data to render a timeline node
- **THEN** the node shows the iteration number, a short hypothesis or direction label, `drawdown`, `turnover`, `deflated_sr`, and `baseline delta`

### Requirement: Dashboard exposes dense support panels for live awareness
The system SHALL provide secondary quant-monitor panels that increase live situational awareness without replacing the timeline as primary navigation.

#### Scenario: Support panels show recent activity and trend context
- **WHEN** the home page renders an active run
- **THEN** the dashboard shows recent log activity, artifact availability, run-level performance trend, and recent decision summary in support panels adjacent to the main timeline and selected-iteration views

#### Scenario: Support panels update as new iteration data lands
- **WHEN** new log lines, artifacts, or ledger updates appear for the active run
- **THEN** the related support panels refresh to reflect the latest available information without requiring a full page reload
