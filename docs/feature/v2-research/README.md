# V2 Research — Redesign Research Capabilities

## Overview

Issue #13. Redesigns research capabilities for the V2 architecture: Obsidian vault integration, multi-agent research CLI, static knowledge base, 4-layer memory architecture, and removal of SQLite Playbook.

The V2 architecture replaces the Python-controlled 6-Phase OPENDEV loop with a program.md-driven approach where Claude Code/Codex autonomously runs the experiment loop. Research capabilities shift from SQLite-backed episodic memory (Playbook) to Obsidian vault Markdown notes, and from embedded research functions to standalone CLI skills.

## Branch

`feature/v2-research`

## Dependency

- Phase 1 and Phase 3 must be complete (backtester + CLI + Obsidian directories)
- Phase 2 (v2-cleanup) must be complete (old architecture removed)

## Issues

| Issue | Scope | Status |
| --- | --- | --- |
| [#13](https://github.com/ricoyudog/Quant-Autoresearch/issues/13) | Umbrella: Research capabilities redesign | pending |

## Execution Order

```
Sprint 1 → Sprint 2
```

Sprint 1 handles structural foundation (vault directories + Playbook removal). Sprint 2 builds the new research capabilities on top.

## Sprints

| Sprint | Scope | Status | Docs |
| --- | --- | --- | --- |
| Sprint 1 | Obsidian vault structure + Playbook removal | pending | [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md) |
| Sprint 2 | Multi-agent research CLI + knowledge base | pending | [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md) |

## Docs

- [v2-research-development-plan.md](./v2-research-development-plan.md) -- Main development plan with task detail
- [v2-research-test-plan.md](./v2-research-test-plan.md) -- Verification and test plan

## Governing Specs

- [research-capabilities-v2.md](../../research-capabilities-v2.md) -- Complete V2 research capabilities design
- [upgrade-plan-v2.md](../../upgrade-plan-v2.md) -- V2 upgrade plan (Section 1.3, 4.6, 11.1)
- [CLAUDE.md](../../../CLAUDE.md) -- Current architecture reference

## Key Design Decisions

1. **Playbook removal**: SQLite Playbook replaced by Obsidian Markdown notes + results.tsv
2. **Obsidian integration**: `quant-autoresearch/` subdirectory in existing vault
3. **Research CLI**: Preserved from V1 research.py, output redirected to vault
4. **Stock analysis CLI**: New TradingAgents-style multi-dimensional analysis (pure computation, no LLM)
5. **Knowledge base**: Four static Markdown notes (overfit defense, strategy patterns, microstructure, methodology)
6. **4-layer memory**: Short (session context), working (session files), persistent (vault), long-term (results.tsv)
