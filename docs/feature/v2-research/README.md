# V2 Research -- Research Capabilities Redesign

## Overview

Issue #13. This workspace is the canonical planning surface for the V2 research-capabilities
redesign: Obsidian vault integration, research and analysis CLI flows, static knowledge-base notes,
4-layer memory guidance, and removal of the legacy SQLite Playbook.

The V2 architecture already moved the experiment loop into `program.md` and closed the upstream
foundation sessions. This umbrella now focuses on the research surface that surrounds that loop:
where research artifacts are stored, how the CLI exposes research workflows, and how the project
replaces Playbook-era memory with vault-native notes plus `results.tsv`.

## Planning Status

- Planning-layer alignment refreshed on 2026-04-08
- Upstream dependency issues `#8`, `#9`, `#11`, and `#12` were confirmed closed on 2026-04-08
- The issue-level phase table is the umbrella summary only; execution belongs in the referenced
  `sprintN/` docs
- Sprint 1, Sprint 2, and Phase 3 verification were completed on 2026-04-08
- On 2026-04-11, the remaining branch-only repair diff was reviewed during V2 closeout and the
  branch was explicitly retired as a superseded historical branch rather than kept as a live merge
  target

## Canonical Decisions

| Item | Decision | Why |
| --- | --- | --- |
| Docs root | `docs/` | The live repo tree uses `docs/`; there is no active `document/`, `docs/beta/`, or `docs/dev/` root to reuse |
| Canonical workspace | `docs/feature/v2-research/` | Issue #13 is a persistent V2 feature workspace, consistent with the existing `docs/feature/v2-*` layout |
| Feature branch | `feature/v2-research` | Preserves the repo's current V2 branch naming convention |
| Execution handoff | `sprint1/` -> `sprint2/` backend docs, plus cross-sprint backend / infra / QA lane docs | Keeps the umbrella issue as a planning index instead of an execution queue |
| Live issue host | `ricoyudog/Quant-Autoresearch#13` | Existing workspace links and the active umbrella issue currently point to the fork, not the checked-out `origin` remote |

## Dependency Status

- [#8](https://github.com/ricoyudog/Quant-Autoresearch/issues/8) -- confirmed closed on 2026-04-08
- [#9](https://github.com/ricoyudog/Quant-Autoresearch/issues/9) -- confirmed closed on 2026-04-08
- [#11](https://github.com/ricoyudog/Quant-Autoresearch/issues/11) -- confirmed closed on 2026-04-08
- [#12](https://github.com/ricoyudog/Quant-Autoresearch/issues/12) -- confirmed closed on 2026-04-08

Execution is no longer blocked by those umbrella dependencies. The current branch state includes
completed Sprint 1 + Sprint 2 implementation, fresh regression evidence, and an updated issue note
capturing the closeout summary.

## Docs Workspace

- [v2-research-development-plan.md](./v2-research-development-plan.md) -- main phase plan, task
  tables, acceptance criteria, and verification expectations
- [v2-research-backend.md](./v2-research-backend.md) -- backend lane contract across vault config,
  research CLI, analysis helpers, and program updates
- [v2-research-infra.md](./v2-research-infra.md) -- vault path, API env, runtime prerequisites, and
  smoke-command assumptions
- [v2-research-test-plan.md](./v2-research-test-plan.md) -- QA gates, coverage matrix, and merge
  evidence expectations
- [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md) -- execution handoff for vault
  foundation, Playbook removal, and research-output migration
- [sprint1/sprint1-infra.md](./sprint1/sprint1-infra.md) -- execution handoff for vault path,
  env override, and setup smoke validation
- [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md) -- execution handoff for research CLI,
  analysis CLI, knowledge notes, and memory guidance
- [sprint2/sprint2-infra.md](./sprint2/sprint2-infra.md) -- execution handoff for API fallback,
  analysis runtime prerequisites, and closeout smoke evidence

## Governing Specs

- [research-capabilities-v2.md](../../research-capabilities-v2.md) -- full research-capabilities
  design for Obsidian integration, CLI behavior, and memory layers
- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) -- umbrella V2 design decisions and sequencing
- [v2-data-pipeline-development-plan.md](../v2-data-pipeline/v2-data-pipeline-development-plan.md)
  -- closest current planning precedent for explicit Phase 0 alignment and lane-based task tables
- [v2-cleanup-development-plan.md](../v2-cleanup/v2-cleanup-development-plan.md) -- precedent for
  removal-heavy execution planning and verification gates

## Scope Snapshot

- Replace the SQLite Playbook with vault-native notes and import cleanup
- Add vault configuration plus `setup_vault` CLI support
- Refactor `src/core/research.py` into a vault-writing research surface that reuses the existing
  paper and web-search helpers
- Add TradingAgents-style, multi-perspective stock analysis helpers under `src/analysis/`
- Create the static knowledge notes and 4-layer memory guidance expected by `program.md`
- Add the test coverage and smoke evidence needed to make the new research runtime reviewable

## Out Of Scope

- New backtester architecture work from `#8`
- CLI simplification and experiment-note integration from `#9`
- New data-pipeline architecture from `#11`
- Overfit-defense implementation work from `#12`
- True multi-LLM orchestration or LangGraph-style debate runtime; the planned `analyze` surface is a
  TradingAgents-style CLI with deterministic computations and structured outputs
