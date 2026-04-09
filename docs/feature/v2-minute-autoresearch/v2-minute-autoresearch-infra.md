# V2 Minute Autoresearch — Infra Plan

## Goal

Capture the non-code planning constraints required for this feature package to remain mergeable and publishable later.

## Scope

- branch and merge target
- docs root and workspace shape
- GitLab publication blocker
- Obsidian / minute-data / environment expectations that the future implementation will depend on

## Key Constraints

- feature branch: `feature/v2-minute-autoresearch`
- merge target: `main-dev`
- canonical docs root: `docs/feature/v2-minute-autoresearch/`
- GitLab publication currently blocked because:
  - `glab` not installed
  - no GitLab CLI config found

## Runtime Expectations To Preserve

- Obsidian remains the upstream idea store
- minute-level strategy mission remains primary
- backtester invariants remain hard constraints

## Publication Follow-up

Once a GitLab-capable environment exists:

- publish umbrella draft
- publish child issue drafts
- confirm `workflow::todo` board/list
- replace local draft references with live issue links

## References

- `.omx/context/v2-minute-autoresearch-orchestration-20260409T074500Z.md`
- `.omx/specs/deep-interview-spec-vs-impl.md`

