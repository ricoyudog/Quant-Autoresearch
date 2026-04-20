## ADDED Requirements

### Requirement: Dashboard explains the selected iteration in a fixed reading order
The system SHALL render the selected iteration using a stable reading order that prioritizes research intent before quantitative evidence and decision outcome.

#### Scenario: Selected iteration panel uses the approved section order
- **WHEN** an operator selects an iteration from the timeline
- **THEN** the dashboard shows `Hypothesis diff`, `Strategy diff`, `Metric breakdown`, and `Decision reasoning` in that order

### Requirement: Dashboard provides drill-down detail for a single iteration
The system SHALL provide a dedicated iteration detail view for deep inspection of one iteration.

#### Scenario: Iteration detail page expands inspection depth
- **WHEN** the operator opens an iteration detail view
- **THEN** the page shows the iteration’s normalized status, hypothesis summary, strategy diff, metric breakdown, decision reasoning, and key artifact or log references for that iteration

### Requirement: Dashboard compares each iteration against approved baselines
The system SHALL support comparison of the selected iteration against the previous iteration, the current baseline, and the best iteration in the active run.

#### Scenario: Metrics expose the three required comparison baselines
- **WHEN** the dashboard renders metric details for a selected iteration
- **THEN** it presents comparisons for `vs previous iteration`, `vs current baseline`, and `vs best iteration in current run`

#### Scenario: Conceptual and code changes can be inspected together
- **WHEN** an iteration has both hypothesis context and strategy changes
- **THEN** the operator can inspect the hypothesis/decision diff and the strategy diff from the same iteration view without leaving the dashboard flow

### Requirement: Dashboard distinguishes decision outcomes with reasons
The system SHALL distinguish kept, reverted, follow-up, and failed iterations and explain why the outcome was assigned.

#### Scenario: Decision reasoning is visible for a completed iteration
- **WHEN** an iteration has a completed decision artifact
- **THEN** the dashboard shows the normalized decision outcome and the recorded reasons for that outcome in the selected-iteration view and detail page
