# Implementation Plan: V2 Closeout Readiness

**Branch**: `001-v2-closeout` | **Date**: 2026-04-11 | **Spec**: `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/001-v2-closeout/spec.md`
**Input**: Feature specification from `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/001-v2-closeout/spec.md`

**Note**: This plan covers planning only. It defines how the repository should produce and verify a canonical V2 closeout package; it does not itself close the V2 workstreams.

## Summary

Create a documentation-first closeout package that consolidates V2 integration status, verification blockers, and status-record conflicts into one reviewable readiness source. The plan uses existing repository evidence—git branch state, test results, and V2 planning artifacts—to produce a canonical closeout inventory, a blocker model, and a repeatable reviewer workflow without adding new runtime dependencies.

## Technical Context

**Language/Version**: Python 3.12+ for repository tooling; Markdown and JSON for closeout artifacts  
**Primary Dependencies**: stdlib file handling, git CLI, pytest, uv, Typer-based repo tooling, existing planning docs  
**Storage**: Repository files under `/Users/chunsingyu/softwares/Quant-Autoresearch`, especially `specs/`, `docs/feature/`, and git metadata  
**Testing**: `pytest`, targeted repository inspection commands, and artifact cross-check review  
**Target Platform**: Local developer CLI workflow on macOS/Linux-like shell environments  
**Project Type**: CLI/documentation-oriented Python repository  
**Performance Goals**: Reviewer can determine V2 readiness from the closeout package in under 15 minutes; artifact regeneration should fit within a normal verification session  
**Constraints**: No new dependencies, keep diffs small and reversible, preserve existing behavior, rely on repository evidence instead of unverifiable claims, and keep documentation statuses synchronized with observed repo state  
**Scale/Scope**: Entire V2 surface in the current repository, including merged workstreams, unmerged branches, failing verification, and contradictory status records across planning docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The current `/Users/chunsingyu/softwares/Quant-Autoresearch/.specify/memory/constitution.md` is still an unfilled template, so it does not define enforceable project-specific gates. Until it is ratified, this plan uses the repository's active operating rules as the effective gate set:

- **Pass**: No new dependencies are introduced by the closeout package.
- **Pass**: The feature remains documentation-first and keeps implementation changes small, reviewable, and reversible.
- **Pass**: Verification evidence is required before any V2 completion claim can be made.
- **Pass**: The plan does not require destructive changes or branch rewriting.

**Post-design re-check**: Phase 1 artifacts continue to satisfy the same effective gates because they only define documentation, evidence, and review structure.

## Project Structure

### Documentation (this feature)

```text
/Users/chunsingyu/softwares/Quant-Autoresearch/specs/001-v2-closeout/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── closeout-artifact-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
/Users/chunsingyu/softwares/Quant-Autoresearch/
├── src/
│   ├── analysis/
│   ├── core/
│   ├── data/
│   ├── memory/
│   ├── strategies/
│   ├── utils/
│   └── validation/
├── tests/
│   ├── integration/
│   ├── regression/
│   ├── security/
│   └── unit/
├── docs/
│   └── feature/
│       ├── v2-cleanup/
│       ├── v2-data-pipeline/
│       ├── v2-minute-autoresearch/
│       ├── v2-overfit-defense/
│       ├── v2-phase1/
│       ├── v2-phase3/
│       ├── v2-phase4/
│       └── v2-research/
└── specs/
    └── 001-v2-closeout/
```

**Structure Decision**: Use the existing single-project Python repository layout and add planning artifacts only under `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/001-v2-closeout/`. The closeout work consumes evidence from `docs/feature/`, git branch state, and test results rather than introducing a new application surface.

## Phase 0: Research Approach

Phase 0 resolves planning decisions by standardizing:

1. What counts as a V2 workstream for closeout purposes
2. Which evidence sources are authoritative for readiness claims
3. How unmerged branches, failing tests, and status conflicts are classified
4. What minimal artifact contract a reviewer needs to make a closeout decision quickly

All resulting decisions are captured in `research.md`.

## Phase 1: Design Approach

Phase 1 turns the research decisions into design artifacts:

- `data-model.md` defines the core closeout entities and their required fields
- `contracts/closeout-artifact-contract.md` defines the expected structure and semantics of the final closeout artifact
- `quickstart.md` defines the reviewer/operator workflow to regenerate and validate the closeout package

No additional runtime interfaces are introduced beyond the repository's existing command-line and documentation surfaces.

## Complexity Tracking

No constitution violations or justified complexity exceptions are currently required.
