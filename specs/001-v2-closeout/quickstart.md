# Quickstart: V2 Closeout Readiness

## Purpose

Use this workflow to regenerate and review the V2 closeout package from repository evidence.

## Prerequisites

- Repository available at `/Users/chunsingyu/softwares/Quant-Autoresearch`
- Active branch: `001-v2-closeout`
- `uv` installed
- Local git history available

## Steps

1. **Open the specification and plan**
   - Review `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/001-v2-closeout/spec.md`
   - Review `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/001-v2-closeout/plan.md`

2. **Collect integration evidence**
   - Inspect which V2 branches are already ancestors of the primary development line
   - Record any V2 branches that remain outside the primary development line

3. **Collect verification evidence**
   - Run the repository test gate
   - Capture failing suites, especially those that block a V2 completion claim

4. **Collect status-consistency evidence**
   - Compare V2 feature READMEs, development plans, and umbrella planning documents
   - Record any conflicts between claimed completion state and observed repository evidence

5. **Build the canonical inventory**
   - Classify each V2 workstream as `complete`, `open`, or `intentionally_deferred`
   - Attach evidence references to each classification

6. **Evaluate the completion standard**
   - Confirm whether integration, verification, and status-consistency gates all pass
   - If any gate fails, classify the overall readiness outcome as `incomplete` or `conditionally_blocked`

7. **Prepare reviewer-facing output**
   - Produce the executive readiness summary
   - Include the canonical workstream inventory, open findings, completion standard, and evidence references

## Expected Outcome

At the end of this workflow, a reviewer should be able to determine quickly whether V2 can honestly be declared complete and what specific blockers remain if it cannot.
