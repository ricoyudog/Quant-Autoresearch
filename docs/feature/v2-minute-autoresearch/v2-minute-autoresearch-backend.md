# V2 Minute Autoresearch — Backend Plan

## Goal

Define the runtime/architecture work needed so implementation later converges on:

- a minute-level autoresearch core
- strategy-facing stock discussion under autoresearch
- optional factor mining under the same loop
- backtester-driven keep/revert

## Scope

- autoresearch loop semantics
- idea intake from Obsidian + self-search
- integration boundaries for stock discussion
- optional factor-mining sub-mode
- validation-engine invariants

## Out Of Scope

- UI work
- GitLab publication mechanics
- full execution details beyond the sprint docs

## Workstream Mapping

- Sprint 1: autoresearch core + idea intake
- Sprint 2: minute runtime + validation alignment
- Sprint 3: strategy-facing stock discussion
- Sprint 4: optional factor mining

## Backend Deliverables

- canonical loop contract
- minute-level mission enforcement contract
- stock-discussion integration contract
- factor-mining trigger contract
- keep/revert outcome contract

## References

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/research-karpathy-autoresearch.md`
- `docs/research-tradingagents.md`
- `docs/data-pipeline-v2.md`
- `program.md`

