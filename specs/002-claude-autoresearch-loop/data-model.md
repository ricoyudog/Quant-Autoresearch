# Data Model: Claude Code Autoresearch Loop

## 1. Autoresearch Run

Represents a bounded multi-round research session.

### Fields

- **run_id**: Stable identifier for the session
- **status**: `pending`, `running`, `paused`, `completed`, or `failed`
- **iteration_budget**: Maximum rounds allowed
- **target_score**: Optional threshold that can stop the run early
- **max_no_improve**: Allowed consecutive non-improving rounds
- **current_iteration**: Latest round number attempted
- **best_score**: Highest retained score so far
- **best_iteration**: Iteration that produced the current retained best
- **no_improve_streak**: Current streak of non-improving rounds
- **strategy_path**: Strategy-under-iteration target
- **state_path**: Persisted run-state location

## 2. Iteration Record

Represents one round of Claude Code research plus deterministic evaluation.

### Fields

- **iteration_id**: Stable per-round identifier
- **run_id**: Parent run reference
- **iteration_number**: Ordered round number
- **hypothesis**: Human-readable summary of the round idea
- **context_sources**: Prior notes, results, and analysis inputs consumed for the round
- **strategy_change_summary**: What Claude Code attempted to change
- **evaluation_summary**: Parsed evaluator output for the round
- **decision**: `keep`, `revert`, or `failed`
- **decision_reason**: Why the final decision was made
- **artifact_paths**: Paths to patch, note, log, or summary artifacts

## 3. Strategy Snapshot

Represents the reversible pre-round copy of the strategy-under-iteration.

### Fields

- **iteration_number**: Round that created the snapshot
- **strategy_path**: File being protected
- **snapshot_path**: Location of the reversible copy
- **created_at**: Snapshot timestamp
- **restored**: Whether the snapshot was used for revert

## 4. Decision Record

Represents the normalized keep/revert output derived from evaluation.

### Fields

- **score**: Parsed round score
- **baseline_score**: Parsed baseline comparator
- **previous_best**: Best retained score before the round
- **decision**: `keep` or `revert`
- **reasons**: List of machine-readable reasons for the decision
- **validation_advisories**: Additional warnings such as weak robustness indicators

## 5. Run State

Represents the persisted resume surface.

### Fields

- **run_id**: Active run identifier
- **current_iteration**: Next round to attempt
- **best_score**: Retained best score
- **best_strategy_reference**: Pointer to the currently retained strategy state
- **last_decision**: Most recent keep/revert outcome
- **no_improve_streak**: Stagnation counter
- **status**: Run lifecycle state
- **updated_at**: Most recent state write time
