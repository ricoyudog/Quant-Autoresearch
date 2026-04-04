# V2 Data Pipeline -- DuckDB + Minute-Level Backtesting

## Overview

Session 2 of the V2 upgrade. This workspace is the canonical planning surface for umbrella issue
[#11](https://github.com/ricoyudog/Quant-Autoresearch/issues/11) and covers the data-pipeline
redesign built on the local `massive-minute-aggs` dataset, a DuckDB daily cache, and minute-level
walk-forward backtesting.

## Planning Status

- Planning-layer alignment completed on 2026-04-04
- Dependency gate on [#8](https://github.com/ricoyudog/Quant-Autoresearch/issues/8) is closed
- Sprint 1 backend and infra execution completed on 2026-04-04
- Next execution target is `sprint2/sprint2-backend.md`
- The issue-level phase table is the umbrella summary only; implementation belongs in the
  referenced `sprintN/` docs

## Canonical Decisions

| Item | Decision | Why |
| --- | --- | --- |
| Docs root | `docs/` | The live repo tree uses `docs/`; there is no active `document/`, `docs/beta/`, or `docs/dev/` root to reuse |
| Canonical workspace | `docs/feature/v2-data-pipeline/` | Issue #11 is a feature-scoped V2 session, consistent with the existing `docs/feature/v2-*` workspaces |
| Feature branch | `feature/v2-data-pipeline` | Preserves the repo's current V2 branch naming convention (`feature/v2-cleanup`, `feature/v2-phase1`, ...) |
| Execution handoff | `sprint1/` -> `sprint3/` backend docs | Keeps the umbrella issue as planning index instead of the execution queue |

## Dependency Gate

- [#8](https://github.com/ricoyudog/Quant-Autoresearch/issues/8) was the required dependency gate
  for Sprint 1 and is now complete
- `src/data/connector.py` and `src/data/preprocessor.py` were removed during Sprint 1 closeout
- DuckDB cache smoke evidence is recorded on issue #11:
  <https://github.com/ricoyudog/Quant-Autoresearch/issues/11#issuecomment-4186599914>
- Runtime-facing documentation updates in `program.md` and `CLAUDE.md` land in Sprint 3, after the
  implementation contracts stabilize

## Docs Workspace

- [v2-data-pipeline-development-plan.md](./v2-data-pipeline-development-plan.md) -- main phase plan,
  task table, acceptance criteria, and verification expectations
- [v2-data-pipeline-backend.md](./v2-data-pipeline-backend.md) -- backend lane contract across
  DuckDB, backtester, strategy, and CLI changes
- [v2-data-pipeline-infra.md](./v2-data-pipeline-infra.md) -- data-path, CLI binary, DuckDB
  storage, and runtime environment assumptions
- [v2-data-pipeline-test-plan.md](./v2-data-pipeline-test-plan.md) -- QA gates, coverage matrix,
  and final merge verification
- [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md) -- execution handoff for DuckDB
  integration and daily cache build
- [sprint1/sprint1-infra.md](./sprint1/sprint1-infra.md) -- runtime validation for dataset paths,
  CLI visibility, and DuckDB cache prerequisites
- [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md) -- execution handoff for strategy
  interface and minute-level backtester integration
- [sprint3/sprint3-backend.md](./sprint3/sprint3-backend.md) -- execution handoff for CLI,
  integration tests, and runtime docs
- [sprint3/sprint3-infra.md](./sprint3/sprint3-infra.md) -- final smoke verification for CLI
  commands and cache refresh behavior

## Governing Specs

- [data-pipeline-v2.md](../../data-pipeline-v2.md) -- full data-pipeline design specification
- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) -- umbrella V2 design decisions and sequencing
- [v2-phase1-development-plan.md](../v2-phase1/v2-phase1-development-plan.md) -- closest completed
  planning precedent for V2 phase structure
- [v2-cleanup-development-plan.md](../v2-cleanup/v2-cleanup-development-plan.md) -- precedent for
  explicit Phase 0 planning and dependency gating
