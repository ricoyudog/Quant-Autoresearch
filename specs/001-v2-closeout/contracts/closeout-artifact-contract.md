# Contract: V2 Closeout Artifact

## Purpose

Define the minimum structure and semantics required for the final V2 closeout artifact so reviewers can make a consistent readiness decision.

## Required Sections

1. **Executive Readiness Summary**
   - Must state whether V2 is `complete`, `incomplete`, or `conditionally blocked`
   - Must include a one-paragraph explanation of the decision

2. **Canonical Workstream Inventory**
   - Must list every in-scope V2 workstream
   - Must show each workstream's integration, verification, and closeout state

3. **Open Findings**
   - Must list all unresolved closeout findings
   - Must include category, severity, impact, next action, and required evidence

4. **Completion Standard**
   - Must define the gates for declaring V2 complete
   - Must explain how deferred work is handled

5. **Evidence References**
   - Must link every completion claim and open finding to supporting evidence
   - Must mark unsupported claims as unverified

6. **Risk and Assumption Notes**
   - Must capture residual risks, missing evidence, and any assumptions still required to interpret the artifact

## Allowed State Values

### Workstream Closeout States

- `complete`
- `open`
- `intentionally_deferred`

### Finding Categories

- `integration_gap`
- `verification_blocker`
- `status_conflict`

### Readiness Outcomes

- `complete`
- `incomplete`
- `conditionally_blocked`

## Review Rules

- A workstream cannot be marked `complete` without at least one supporting evidence reference.
- A closeout artifact cannot report V2 as `complete` while any high-severity finding remains open.
- A status conflict must remain visible until the conflicting records are reconciled or explicitly superseded.
- Deferred work must be explicitly named; omission does not count as deferral.
