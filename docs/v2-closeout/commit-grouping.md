# V2 Closeout — Commit Grouping Review

**Reviewed On**: 2026-04-11  
**Reviewed Branch State**: `001-v2-closeout` at `fdc1498`  
**Comparison Base**: `main-dev`

## Audit Summary

The current V2 closeout checkpoint is a **single commit** (`fdc1498`, `Preserve the V2 closeout baseline so team workers can branch safely`) that combines four different change types:

- generated OMX/Specify/GitNexus tooling scaffolding
- the canonical V2 closeout documentation package
- the planning/spec artifacts for `001-v2-closeout`
- the targeted overfit regression-test repair

That checkpoint is a valid worker-launch baseline, but it is not yet review-optimal as a final history shape.

## Evidence Snapshot

### Commit-range facts

- `git log --reverse --format='%h %s' main-dev..HEAD` returns exactly one commit: `fdc1498 Preserve the V2 closeout baseline so team workers can branch safely`
- `git diff --shortstat main-dev..HEAD` reports **85 files changed, 10708 insertions(+), 27 deletions(-)**

### Scope grouped by review concern

| Group | Files | Insertions | Deletions | Notes |
| --- | ---: | ---: | ---: | --- |
| Tooling/runtime scaffolding | 67 | 9853 | 1 | `.specify/`, `.agents/skills/`, `.claude/skills/`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` |
| Closeout docs | 3 | 145 | 0 | `docs/v2-closeout/*` |
| Status-doc alignments | 6 | 12 | 10 | existing V2 status docs under `docs/feature/` plus `docs/upgrade-plan-v2.md` |
| Closeout specs | 8 | 667 | 0 | `specs/001-v2-closeout/*` |
| Test repair | 1 | 31 | 16 | `tests/unit/test_backtester_overfit.py` |

### Review-significant observations

1. **Tooling dominates the diff**: about 92% of added lines (`9853 / 10708`) are tooling/runtime scaffolding rather than closeout evidence or the regression fix.
2. **The only executable behavior change is localized**: `tests/unit/test_backtester_overfit.py` is the single Python test file in the `main-dev..HEAD` range.
3. **The closeout narrative is documentation-first**: the actual readiness package lives in `docs/v2-closeout/*`, with small alignment edits in existing V2 status docs.
4. **The spec artifacts are useful review context, but separable**: `specs/001-v2-closeout/*` explains the closeout workflow without affecting runtime behavior.

## Recommended Commit Grouping

### Group 1 — regression repair

**Suggested intent**: preserve the overfit verification contract on the public minute-runtime entrypoint

**Files**:
- `tests/unit/test_backtester_overfit.py`

**Why isolate it**:
- This is the only functional verification repair in the range.
- Reviewers can validate the blocker fix without reading tooling or documentation noise.

### Group 2 — canonical closeout package

**Suggested intent**: publish the V2 closeout decision package and align the checked-in status surface

**Files**:
- `docs/v2-closeout/README.md`
- `docs/v2-closeout/integration.md`
- `docs/v2-closeout/verification.md`
- `docs/feature/v2-cleanup/README.md`
- `docs/feature/v2-phase1/README.md`
- `docs/feature/v2-phase3/README.md`
- `docs/feature/v2-research/README.md`
- `docs/feature/v2-research/v2-research-development-plan.md`
- `docs/upgrade-plan-v2.md`

**Why isolate it**:
- These files are the actual closeout deliverable.
- They should review as one coherent documentation decision instead of being buried under generated scaffolding.

### Group 3 — closeout planning/spec artifacts

**Suggested intent**: capture the `001-v2-closeout` spec/plan trail that explains how the closeout package was produced

**Files**:
- `specs/001-v2-closeout/checklists/requirements.md`
- `specs/001-v2-closeout/contracts/closeout-artifact-contract.md`
- `specs/001-v2-closeout/data-model.md`
- `specs/001-v2-closeout/plan.md`
- `specs/001-v2-closeout/quickstart.md`
- `specs/001-v2-closeout/research.md`
- `specs/001-v2-closeout/spec.md`
- `specs/001-v2-closeout/tasks.md`

**Why isolate it**:
- These artifacts are valuable, but they are implementation-planning records rather than the closeout result itself.
- Keeping them separate lets reviewers choose whether they want the planning history in the same PR/commit stream.

### Group 4 — tooling/bootstrap import

**Suggested intent**: vendor the OMX/Specify/GitNexus workspace scaffolding required by the checkpointed environment

**Files**:
- `.specify/**`
- `.agents/skills/speckit-*/SKILL.md`
- `.claude/skills/**`
- `AGENTS.md`
- `CLAUDE.md`
- `.gitignore`

**Why isolate it**:
- This is the largest and noisiest slice.
- It is operationally useful for the workspace, but it is not the V2 closeout decision itself.
- If the final goal is a narrowly reviewable closeout PR, this group is the first candidate to move to a separate PR or to keep as a standalone tooling commit.

## Cleanup Recommendations

1. **Do not ship the checkpoint as one final squash commit** unless the team explicitly values a single archival snapshot over reviewability.
2. **Keep the overfit test repair separate from the documentation closeout** so future regressions can bisect cleanly to the contract fix.
3. **Keep `AGENTS.md` / `CLAUDE.md` with the tooling import**, not with the closeout docs; those edits are workflow guidance, not closeout evidence.
4. **Keep `.gitignore` with the GitNexus/tooling commit**, because the `.gitnexus` ignore rule is unrelated to the closeout narrative.
5. **If history must be reduced to two commits**, prefer:
   - Commit A: `tests/unit/test_backtester_overfit.py`
   - Commit B: all documentation/spec/tooling artifacts
   This is less ideal than four groups, but still preserves the only behavior-affecting change as a standalone review unit.

## Recommended Leader Action

Before final integration or PR creation, re-stage the current checkpoint into the four groups above (or the two-commit fallback) so that:

- the regression repair is independently reviewable
- the closeout package reads as the canonical product change
- the generated tooling scaffolding does not dominate the closeout review

This review documents the grouping recommendation only. It does **not** recommend reverting the current verified branch state.

## Safe Restaging Sequence

If the leader decides to split the checkpoint before final integration, use this order so the current evidence-backed state stays recoverable throughout the rewrite:

1. keep `fdc1498` reachable via a temporary branch or tag before rewriting history
2. restage and commit `tests/unit/test_backtester_overfit.py` first
3. restage and commit the closeout/status documentation package second
4. restage and commit the `specs/001-v2-closeout/*` planning trail third
5. move the OMX/Specify/GitNexus scaffolding into the last commit or a separate PR

This preserves the verified checkpoint while making the final review history materially easier to audit.
