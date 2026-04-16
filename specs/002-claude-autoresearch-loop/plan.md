# Implementation Plan: Claude Code Autoresearch Loop

**Branch**: `002-claude-autoresearch-loop` | **Date**: 2026-04-13 | **Spec**: `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/002-claude-autoresearch-loop/spec.md`
**Input**: Feature specification from `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/002-claude-autoresearch-loop/spec.md`

## Summary

Add a Karpathy-style outer-loop autoresearch runner that uses Claude Code as the research agent while keeping this repository's deterministic evaluator, strategy-under-iteration file, vault-native research surfaces, and results ledger as the authoritative runtime surfaces. The runner will own iteration control, resume state, strategy snapshot/revert, and stop conditions; Claude Code will own hypothesis generation and bounded strategy edits only.

## Technical Context

**Language/Version**: Python 3.12+ for the loop runner and repository tooling; shell wrapper for Claude Code invocation  
**Primary Dependencies**: existing `cli.py` commands, `src/core/backtester.py`, `src/core/research.py`, `src/memory/idea_keep_revert.py`, `src/memory/candidate_generation.py`, Claude Code CLI, git CLI  
**Storage**: Repository files plus persisted run artifacts under `/Users/chunsingyu/softwares/Quant-Autoresearch/experiments/` and optional vault notes under the configured Obsidian path  
**Testing**: `pytest`, focused runner tests, strategy snapshot/revert tests, dry-run loop verification, and full repository regression checks  
**Target Platform**: Local CLI workflow on macOS/Linux-like environments where Claude Code can be invoked from the shell  
**Project Type**: CLI-driven research orchestration for a single-project Python repository  
**Performance Goals**: An operator can launch a bounded run without manual intervention between rounds, and each round records a complete decision artifact before the next round starts  
**Constraints**: keep Claude Code outside the repository runtime, keep deterministic evaluator authority inside the repo, avoid introducing an embedded agent framework, preserve `src/strategies/active_strategy.py` as the bounded strategy target, and keep runs resumable and reversible  
**Scale/Scope**: One bounded autoresearch runner controlling a single strategy-under-iteration file, single-runner execution, multiple rounds, and persisted per-iteration artifacts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This repository no longer carries a separate Spec Kit constitution file, so the repository's active working rules remain the effective provisional gates:

- **Pass**: The design keeps deterministic evaluation and acceptance outside Claude Code's authority.
- **Pass**: No new product-side agent framework is introduced into repository runtime code.
- **Pass**: The loop remains auditable through persisted state, iteration artifacts, and evaluator evidence.
- **Pass**: The first implementation stays single-runner and bounded rather than introducing speculative multi-agent orchestration.

**Post-design re-check**: Phase 1 artifacts preserve the same gates by defining a thin orchestration layer around existing repository primitives instead of replacing them.

## Project Structure

### Documentation (this feature)

```text
/Users/chunsingyu/softwares/Quant-Autoresearch/specs/002-claude-autoresearch-loop/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── autoresearch-runner-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
/Users/chunsingyu/softwares/Quant-Autoresearch/
├── cli.py
├── program.md
├── scripts/
│   ├── autoresearch_runner.py
│   └── run_claude_iteration.sh
├── src/
│   ├── core/
│   │   ├── backtester.py
│   │   └── research.py
│   ├── memory/
│   │   ├── candidate_generation.py
│   │   └── idea_keep_revert.py
│   └── strategies/
│       └── active_strategy.py
├── experiments/
│   ├── results.tsv
│   ├── autoresearch_state.json
│   └── iterations/
└── tests/
    ├── integration/
    └── unit/
```

**Structure Decision**: Keep the loop orchestration outside the repository core runtime by adding a dedicated runner under `/Users/chunsingyu/softwares/Quant-Autoresearch/scripts/` and persisted run artifacts under `/Users/chunsingyu/softwares/Quant-Autoresearch/experiments/`. Reuse existing CLI and evaluator primitives rather than creating a new application surface.

## Phase 0: Research Approach

Research resolves four design decisions:

1. How Claude Code is invoked safely as an external per-iteration agent
2. What the minimal persisted run state and per-iteration artifact schema must contain
3. How strategy snapshot, keep, and revert are applied around the current strategy file
4. How stop conditions and resume behavior remain deterministic and auditable

All decisions are captured in `research.md`.

## Phase 1: Design Approach

Phase 1 converts the research decisions into concrete design artifacts:

- `data-model.md` defines run state, iteration records, strategy snapshots, and decision records
- `contracts/autoresearch-runner-contract.md` defines the runner inputs, outputs, and iteration lifecycle semantics
- `quickstart.md` defines the operator workflow for launching, resuming, and verifying a bounded run

The design keeps Claude Code outside the repository runtime and lets the repository remain the deterministic execution and evidence layer.

## Complexity Tracking

No constitution violations or justified complexity exceptions are currently required.
