# V2 Phase 4 — Closeout Alignment

## Overview

Phase 4 is the final V2 alignment pass after the Phase 1, Phase 3, and cleanup branches have already landed in `main-dev`. This workspace upgrades issue #10 from a lightweight phase card into a real planning package so the remaining closeout work can be executed from a branch, a canonical docs root, and lane-specific plans instead of from issue prose alone.

## Branch

`feature/v2-phase4`

## Issue

| Issue | Scope | Status |
| --- | --- | --- |
| [#10](https://github.com/ricoyudog/Quant-Autoresearch/issues/10) | Phase 4: CLAUDE.md update + docs cleanup + .gitignore confirmation | in progress |

## Current Phase Summary

| Phase | Goal | Status | Next Step |
| --- | --- | --- | --- |
| Phase 0 | Bootstrap planning workspace and inventory stale V1 references | completed | start Phase 1 execution docs |
| Phase 1 | Rewrite `CLAUDE.md` and align agent/operator command surfaces with V2 | pending | derive sprint steps from backend + infra lane docs |
| Phase 2 | Clean or archive stale V1-facing documentation | pending | execute after Phase 1 command surface is correct |
| Phase 3 | Confirm `.gitignore`, service/config surfaces, and full verification closure | pending | run after docs cleanup settles |

## Docs

- [v2-phase4-development-plan.md](./v2-phase4-development-plan.md) — Umbrella plan, task table, risks, and execution handoff
- [v2-phase4-backend.md](./v2-phase4-backend.md) — Agent-facing and user-facing documentation lane
- [v2-phase4-infra.md](./v2-phase4-infra.md) — `.gitignore`, service config, and command-surface alignment lane
- [v2-phase4-test-plan.md](./v2-phase4-test-plan.md) — Verification matrix and evidence expectations

## Governing Specs

- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) — Phase 4 source scope (`CLAUDE.md`, `.gitignore`, docs cleanup, full verification)
- [program.md](../../../program.md) — Current V2 instruction source that `CLAUDE.md` must align to
- [../v2-phase1/README.md](../v2-phase1/README.md) — Phase 1 outputs now reflected in V2 guidance
- [../v2-phase3/README.md](../v2-phase3/README.md) — CLI and notes-directory changes already merged into `main-dev`
- [../v2-cleanup/README.md](../v2-cleanup/README.md) — V1 OPENDEV removals that Phase 4 docs must stop referencing

## Execution Handoff

This README and the linked phase plan are the planning layer only. Execution should move into `sprintN/` docs under this same root once the next implementation slice is selected.
