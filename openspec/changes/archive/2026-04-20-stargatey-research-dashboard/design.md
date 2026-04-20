## Context

Quant Autoresearch already emits the right raw ingredients for a live dashboard:

- `experiments/autoresearch_state.json` for run state
- `experiments/iterations/<run_id>/iteration-<n>/` for structured iteration artifacts and logs
- `experiments/results.tsv` for a stable performance ledger
- retained snapshots and strategy files for diffing

The current operator workflow is manual. To answer whether a run is healthy, the operator has to inspect multiple files and infer whether silence means completion, waiting, or a fault. To understand whether research is improving, the operator has to correlate artifacts, logs, snapshots, and ledger rows.

The dashboard must fit the repo’s current architecture:

- it must stay local-first
- it must not replace CLI execution
- it must not imply unsupported autonomous promotion behavior
- it must preserve evaluator/backtester-led keep/revert authority

The operator preference is a dense, solo-use cockpit with a timeline-first structure and quant-monitor support panels, prioritizing risk-adjusted quality over raw score.

## Goals / Non-Goals

**Goals:**
- Provide a local web dashboard that answers run health within 10 seconds.
- Normalize repo-local state, logs, artifacts, and ledger data into a stable dashboard model.
- Make iteration evolution the primary narrative via a timeline-first UI.
- Support drill-down analysis for a selected iteration, including hypothesis diff, strategy diff, metrics, and decision reasoning.
- Detect and explain stalled, blocked, failed, and waiting states without changing the underlying runtime contract.
- Keep the design additive and reversible.

**Non-Goals:**
- Starting, pausing, stopping, or editing research from the dashboard.
- Replacing CLI commands or the backtester’s authority.
- Building a collaboration or multi-user system.
- Shipping a full multi-run history center in the first version.
- Defining a specific frontend framework or chart library in this proposal stage.

## Decisions

### 1. Use a local read-only dashboard service

**Decision:** Implement the dashboard as a local web application backed by a read-only observer/service layer.

**Why:** The operator needs drill-down pages, timeline navigation, diff views, and charts that are awkward in a TUI. A local web surface supports dense information without changing the execution path.

**Alternatives considered:**
- Terminal dashboard only: lower build complexity, but weaker for timeline navigation, diffs, and side-by-side comparison.
- Static report generation: simpler delivery, but insufficient for live heartbeat and run-health monitoring.

### 2. Introduce a normalized observer model between files and UI

**Decision:** Add a backend observer layer that reads raw repo files and emits normalized run, iteration, metric, and health state for the UI.

**Why:** The raw files arrive at different times and have different roles. The UI should not encode direct file-specific logic for every view. A normalized model makes testing, stale-state detection, and partial updates much easier.

**Alternatives considered:**
- Read files directly in the UI: fast to start, but couples the UI to file timing and repo structure.
- Only render `results.tsv`: stable, but loses live heartbeat and decision context.

**Data model impact:** The implementation will need normalized entities such as `RunSummary`, `RunHealth`, `IterationSummary`, `IterationDetail`, `MetricComparison`, and `ArtifactStatus`.

### 3. Make run health topmost and timeline primary

**Decision:** The home page should use `Run Health Strip` first, `Iteration Timeline` as primary navigation, `Selected Iteration Panel` as the main detail region, and dense support panels as secondary awareness aids.

**Why:** The operator’s top question is whether the run is healthy. The second need is understanding how the research direction changes across rounds. This makes a timeline-first shell more useful than a generic panel grid.

**Alternatives considered:**
- Grid-first quant monitor: dense, but weak for storytelling and stepwise evolution.
- Latest-round-only focus: fast to read, but hides direction drift and iteration learning.

### 4. Prioritize logs, then artifacts, then results ledger

**Decision:** The observer should treat logs as the fastest heartbeat, structured artifacts as the source of meaning, and `results.tsv` as the ledger confirmation layer.

**Why:** These surfaces land at different times during a live run. The dashboard must be able to show activity before a full decision record exists, then enrich the view as the structured files appear, and finally confirm metrics once the ledger updates.

**Alternatives considered:**
- State file only: too coarse for run liveness and phase inference.
- Ledger-first: too slow for live monitoring.

### 5. Normalize health and iteration status explicitly

**Decision:** The observer must map raw repo state into a finite run-status model (`Healthy`, `Busy`, `Waiting`, `Stalled`, `Failed`, `Blocked`, `Completed`) and iteration-status model (`Queued`, `In Progress`, `Decision Pending`, `Evaluated`, `Kept`, `Reverted`, `Follow-up`, `Failed`).

**Why:** Operators need a consistent interpretation layer instead of inferring semantics from raw files and timestamps.

**Alternatives considered:**
- Expose raw state fields directly: less code, but shifts interpretation burden back to the operator.

**API contract impact:** The implementation should expose one dashboard-facing contract that includes explicit status enums, timestamps, diagnosis signals, and comparison data rather than raw file blobs.

### 6. Keep first-version scope additive and rollback-safe

**Decision:** The first version will only add read-only monitoring and analysis surfaces.

**Why:** The repo already has a working CLI-led research contract. A read-only dashboard can be introduced without changing the strategy loop’s authority or needing migration of existing artifacts.

**Alternatives considered:**
- Adding dashboard controls in v1: attractive, but increases risk and blurs runtime boundaries too early.

## Risks / Trade-offs

- [Partial artifact timing] → The dashboard may see logs before `decision.json` or `iteration_record.json` exists. Mitigation: model incomplete states explicitly and fill details progressively.
- [Status misclassification] → Silence can mean waiting, stall, or completion. Mitigation: base health on multiple signals (`updated_at`, log freshness, presence of decision artifacts, stop reason).
- [Framework choice drift] → Picking a heavy stack could slow delivery. Mitigation: keep the design framework-agnostic until implementation planning chooses the smallest viable stack.
- [Diff complexity] → Strategy and hypothesis diffs can be noisy. Mitigation: separate conceptual diff from code diff and default to concise summaries with expandable detail.
- [Live polling cost] → Aggressive refresh loops can add noise or overhead. Mitigation: keep the update model small and prioritize health-strip updates over full view recomputation.

## Migration Plan

1. Implement the observer layer against existing repo-local artifacts and state files.
2. Add the home page shell with run health, timeline, and selected-iteration panel.
3. Add the iteration detail page and diff/metric comparison views.
4. Validate against real and simulated run states, including stale and failed conditions.
5. Roll back by disabling or removing the dashboard service and routes if needed; no artifact migration is required because the dashboard is read-only and additive.

## Open Questions

- Which local web/runtime stack best fits the repo without adding unnecessary dependencies?
- Should the first implementation use filesystem watching, short-interval polling, or a hybrid?
- How much strategy diff context should be rendered inline before falling back to linked detail?
- Should the first version expose note-draft content inline or only summarize it in the decision section?
