> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Minute Autoresearch — Infra Plan

## Goal

Capture the non-code planning constraints required for this feature package to remain mergeable and publishable later.

## Scope

- branch and merge target
- docs root and workspace shape
- GitHub issue publication status
- Obsidian / minute-data / environment expectations that the future implementation will depend on

## Key Constraints

- feature branch: `feature/v2-minute-autoresearch`
- merge target: `main-dev`
- historical docs root used during planning: `docs/feature/v2-minute-autoresearch/`
- GitHub issues published:
  - umbrella `#17`
  - issue A `#18`
  - issue B `#19`
  - issue C `#20`
  - issue D `#21`

## Runtime Expectations To Preserve

- Obsidian remains the upstream idea store
- minute-level strategy mission remains primary
- backtester invariants remain hard constraints

## Publication Follow-up

- keep the local issue-card drafts synchronized with the live GitHub issues
- keep the `workflow::todo` label contract consistent for future issue creation

## References

- `.omx/context/v2-minute-autoresearch-orchestration-20260409T074500Z.md`
- `.omx/specs/deep-interview-spec-vs-impl.md`
