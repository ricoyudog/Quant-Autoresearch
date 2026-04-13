# Contract: Claude Code Autoresearch Runner

## Purpose

Define the expected lifecycle and inputs/outputs for a Karpathy-style outer-loop runner that uses Claude Code for per-iteration research and the repository evaluator for final acceptance decisions.

## Required Runner Inputs

- **strategy target**: The bounded strategy-under-iteration file
- **iteration budget**: Maximum number of rounds
- **no-improvement limit**: Maximum allowed stagnation streak
- **optional target score**: Early-stop success threshold
- **context sources**: `program.md`, prior results, recent experiment notes, and optional analysis outputs

## Required Runner Outputs

1. **Run state file**
   - Must record the current iteration, best-known score, last decision, and status

2. **Per-iteration record**
   - Must record the round hypothesis, strategy-change summary, evaluator output, and final decision

3. **Strategy snapshot**
   - Must exist before Claude Code edits the strategy

4. **Decision outcome**
   - Must be one of `keep`, `revert`, or `failed`

## Required Lifecycle

1. Load run state or initialize a new run
2. Read the current retained strategy baseline
3. Collect iteration context from approved repository sources
4. Snapshot the strategy target
5. Invoke Claude Code for a bounded strategy proposal round
6. Run deterministic evaluation
7. Parse evaluator output into a normalized decision record
8. Keep or revert the strategy based on the decision
9. Persist iteration artifacts and updated run state
10. Stop or continue based on configured stop conditions

## Decision Rules

- A round cannot be marked `keep` without a parsed evaluator result
- A failed evaluation must not silently retain the round's strategy edits
- Resume must continue from persisted run state rather than reconstructing history heuristically
- The runner must remain the authority over iteration control and strategy retention
