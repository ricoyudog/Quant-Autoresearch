# V2 Phase 3 — CLI Simplification + Obsidian Notes

## Overview

Phase 3 of the V2 upgrade. Simplifies the CLI to three working commands (`setup_data`, `fetch`, `backtest`), creates the Obsidian directory structure for experiment notes, updates `.gitignore` with runtime output files, and updates `program.md` with Obsidian note format instructions.

## Branch

`feature/v2-phase3`

## Dependency

- **Phase 1 (issue #8)** must be complete before starting.
- Phase 2 (v2-cleanup, issue #1) is already merged.

## Issues

| Issue | Scope | Status |
| --- | --- | --- |
| [#9](https://github.com/ricoyudog/Quant-Autoresearch/issues/9) | Umbrella: Phase 3 — CLI + Obsidian + program.md | pending |

## Execution Order

```
Sprint 1 → Sprint 2
```

Sprint 1 handles CLI simplification + directory/gitignore changes. Sprint 2 handles program.md update + tests.

## Docs

- [v2-phase3-development-plan.md](./v2-phase3-development-plan.md) — Main development plan with task detail
- [v2-phase3-test-plan.md](./v2-phase3-test-plan.md) — Verification and test plan

## Governing Specs

- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) — Phase 3 section (lines 616-624), Section 4 Obsidian notes
- [CLAUDE.md](../../../CLAUDE.md) — Current architecture reference (updated in Phase 4)
