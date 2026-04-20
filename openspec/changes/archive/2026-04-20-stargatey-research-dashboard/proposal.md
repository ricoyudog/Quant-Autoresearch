## Why

Quant Autoresearch currently exposes the research loop through CLI commands, raw logs, iteration artifact folders, and `experiments/results.tsv`, but it does not provide a single live cockpit that shows whether the current run is healthy and how the research direction is evolving. We need a local dashboard now so the operator can understand the active run within seconds instead of stitching together state, logs, artifacts, and metrics by hand.

## What Changes

- Add a local web dashboard for the active research run that is read-only and keeps CLI as the execution surface.
- Add a live run-health view that summarizes status, heartbeat freshness, active iteration, and blocked/stalled/failed conditions.
- Add an iteration timeline that shows hypothesis-direction evolution alongside risk-adjusted metrics for each round.
- Add a selected-iteration panel and detail view that explain hypothesis changes, strategy diffs, metric breakdowns, and keep/revert/follow-up reasoning.
- Add a normalized observer layer that reads repo-local run state, iteration artifacts, logs, and `experiments/results.tsv` into a stable dashboard model.
- Preserve future expansion for multi-run history without making it a first-version requirement.

## Capabilities

### New Capabilities
- `research-dashboard-monitoring`: Live monitoring surface for active run health, iteration timeline, and high-signal quant panels.
- `research-dashboard-iteration-analysis`: Iteration-focused analysis views for hypothesis diff, strategy diff, metrics, and decision reasoning.
- `research-dashboard-observer`: Local observer model that ingests run state, logs, artifacts, and ledger data into normalized dashboard state.

### Modified Capabilities
- None.

## Impact

- Affected systems: local dashboard runtime, dashboard UI routes/views, observer/service layer, repo-local artifact readers.
- Affected data surfaces: `experiments/autoresearch_state.json`, `experiments/iterations/**`, `experiments/results.tsv`, strategy snapshots, and generated note drafts.
- API impact: introduces a new local dashboard-facing state contract for run health, timeline nodes, iteration details, and normalized statuses.
- Dependency impact: no new dependency is required by the proposal itself, but implementation will need to choose a lightweight local web/UI stack.
- Runtime impact: additive only; CLI start/stop behavior and evaluator-led keep/revert authority remain unchanged.

## GitHub Issue

- Parent: #2 (https://github.com/yllvar/Quant-Autoresearch/issues/2)
