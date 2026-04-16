> Status: historical

# V2 Closeout — Integration Evidence

**Collected On**: 2026-04-11
**Comparison Branch**: `main-dev`

## Branch Ancestry Snapshot

```text
MERGED   feature/v2-cleanup
MERGED   feature/v2-overfit-defense
MERGED   feature/v2-phase1
MERGED   feature/v2-phase3
MERGED   feature/v2-phase4
UNMERGED feature/v2-research
UNMERGED feature/v2-minute-autoresearch
```

## Final Branch Dispositions

### `feature/v2-research`

- **State**: not an ancestor of `main-dev`
- **Observed branch-only tail**:
  - tip commit `be35cef` only removes incidental `.gitignore` noise
  - the remaining branch diff is against an older backtester architecture (`data.connector`, import-time strategy resolution, legacy `P_VALUE` output)
- **Disposition**: **retire as superseded**
- **Rationale**: the current `main-dev` backtester has already moved to the minute-runtime architecture, and the branch-only repair diff targets an obsolete pre-Phase-3 code shape. The current blocker was resolved safely by updating stale tests to the supported public V2 entrypoint contract instead of reviving the obsolete branch diff.

### `feature/v2-minute-autoresearch`

- **State**: not an ancestor of `main-dev`
- **Observed branch-only commit**:
  - `6d4b9ce` — `Close the V2 umbrella once every child lane has landed`
- **Observed diff scope vs `main-dev`**:
  - umbrella closeout card and merge-ledger wording only
- **Disposition**: **retire as superseded**
- **Rationale**: the current `main-dev` minute-autoresearch docs already record the umbrella as closed on GitHub, the child lanes as merged, and the merge ledger as historical. The branch is therefore no longer needed to preserve truthful repository state.

## Integrated Workstreams

- `feature/v2-cleanup`
- `feature/v2-overfit-defense`
- `feature/v2-phase1`
- `feature/v2-phase3`
- `feature/v2-phase4`

These workstreams are already ancestors of `main-dev` and do not block closeout on integration grounds.

## Closeout Interpretation

- The two non-ancestor V2 branches remain in git history, but they are now explicitly classified as **historical superseded branches**, not active integration blockers.
- No additional merge action is required to make the canonical repository state truthful.
