## 1. Observer Foundation

- [x] 1.1 Choose the smallest local dashboard runtime and document the chosen stack in the change implementation notes
- [x] 1.2 Implement a normalized observer module that reads run state, iteration artifacts, logs, and `experiments/results.tsv`
- [x] 1.3 Add focused tests for source ingestion, status normalization, and stale/blocked/failed detection using representative fixture data

## 2. Home Page Live Monitor

- [x] 2.1 Implement the home page shell with `Run Health Strip`, `Iteration Timeline`, `Selected Iteration Panel`, and support-panel layout
- [x] 2.2 Render timeline nodes with hypothesis label, `drawdown`, `turnover`, `deflated_sr`, and `baseline delta`
- [x] 2.3 Implement live refresh behavior so run health and active iteration state update as logs and artifacts change

## 3. Iteration Analysis Views

- [x] 3.1 Implement the selected-iteration panel using the fixed order: hypothesis diff, strategy diff, metric breakdown, decision reasoning
- [x] 3.2 Implement an iteration detail page with drill-down views for artifacts, logs, and baseline comparisons
- [x] 3.3 Add comparison helpers for `vs previous iteration`, `vs current baseline`, and `vs best iteration in current run`

## 4. Health Diagnostics and Failure UX

- [x] 4.1 Implement normalized run and iteration status mapping for healthy, waiting, stalled, blocked, failed, and completed conditions
- [x] 4.2 Surface diagnosis details in the health strip and iteration views without requiring raw-file inspection
- [x] 4.3 Add regression coverage for stalled, blocked, failed, and partial-artifact states

## 5. Verification and Finish

- [x] 5.1 Validate the dashboard against a real or representative active-run artifact tree under `experiments/iterations/`
- [x] 5.2 Verify that the home page answers run health within 10 seconds and that iteration drill-downs show the expected diffs and reasoning
- [x] 5.3 Update any implementation-facing docs needed to explain how to launch the dashboard and interpret its statuses
- [x] 5.4 Make the representative dashboard validation deterministic so the home-page health expectation cannot age from `Healthy` into `Stalled` during later reruns
- [x] 5.5 Tighten the representative dashboard validation to prove the home page stays healthy and the iteration detail page still shows the expected diffs and decision reasoning under the same fixture timing model
- [x] 5.6 Re-run the full dashboard verification set and record clean evidence: representative integration test, full `pytest`, CLI help, browser validation, and no remaining known dashboard verification failures
- [x] 5.7 Escape or safely render untrusted log excerpts, diagnosis text, and artifact/path fields so the dashboard cannot execute stored HTML or script content from repo-local artifacts
- [x] 5.8 Resolve repo-relative artifact paths against the observed repository root and hide stale iteration timelines when there is no active run state
- [x] 5.9 Stop attaching ledger rows to iterations by plain list index and make run-health heartbeat selection use the freshest viable signal across logs, artifacts, and state
- [x] 5.10 Add regression coverage for escaped dashboard rendering, repo-relative artifact paths, no-active-run timeline behavior, ledger ambiguity handling, and freshest-heartbeat selection; then rerun the full dashboard verification set cleanly
- [x] 5.11 Remove the single-row unkeyed ledger fallback so ledger metrics only attach to iterations with explicit, unambiguous iteration identifiers
- [x] 5.12 Reset selected-iteration and detail-page panels to empty or missing placeholders when refreshed state has no matching iteration
- [x] 5.13 Re-run the focused dashboard tests, full `pytest`, and a final review pass with no remaining Important findings
