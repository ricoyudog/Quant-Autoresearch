# Data Model: V2 Closeout Readiness

## 1. V2 Workstream

Represents a distinct slice of V2 scope that contributes to the final closeout decision.

### Fields

- **name**: Human-readable workstream name
- **scope_summary**: Short description of what the workstream covers
- **canonical_sources**: Referenced repository artifacts that define or summarize the workstream
- **integration_state**: `integrated`, `not_integrated`, or `partially_integrated`
- **verification_state**: `verified`, `failing`, `not_run`, or `stale`
- **status_state**: `consistent`, `conflicting`, or `unknown`
- **closeout_state**: `complete`, `open`, or `intentionally_deferred`
- **blocking_findings**: List of associated closeout findings
- **required_evidence**: Evidence records required to mark the workstream complete

### Relationships

- One workstream can have many closeout findings
- One workstream can reference many evidence records
- One workstream is evaluated against one shared completion standard

## 2. Closeout Finding

Represents an observation that affects readiness.

### Fields

- **id**: Stable identifier
- **title**: Short finding title
- **category**: `integration_gap`, `verification_blocker`, or `status_conflict`
- **severity**: `high`, `medium`, or `low`
- **summary**: What was observed
- **impact**: Why the finding matters to closeout
- **next_action**: Required follow-up to resolve or reclassify the finding
- **evidence_needed**: Proof needed to mark the finding resolved
- **dependency_notes**: Upstream or downstream relationships with other findings
- **resolution_state**: `open`, `resolved`, or `deferred`

### Relationships

- Many findings can belong to one workstream
- A finding can reference one or more evidence records

## 3. Completion Standard

Represents the gate used to decide whether V2 can be declared complete.

### Fields

- **integration_gate**: Definition of required integration state
- **verification_gate**: Definition of required verification state
- **status_consistency_gate**: Definition of required document consistency
- **deferred_work_rule**: Rule for how deferred work affects the closeout claim
- **claim_rule**: The exact conditions under which V2 may be called complete

### Relationships

- One completion standard evaluates all V2 workstreams

## 4. Evidence Record

Represents proof attached to a claim or finding.

### Fields

- **source_type**: `git_state`, `test_result`, `document_record`, or `manual_review_note`
- **source_location**: File path, branch name, command output location, or other precise reference
- **observation_date**: Date the evidence was collected
- **summary**: What the evidence shows
- **trust_level**: `primary`, `supporting`, or `unverified`

### Relationships

- One evidence record can support many workstreams or findings
- Each completion claim should reference at least one evidence record
