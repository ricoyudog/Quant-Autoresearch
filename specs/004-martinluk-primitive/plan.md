# Implementation Plan: MartinLuk Leader Pullback / ORH Primitive

**Branch**: `[004-martinluk-primitive]` | **Date**: 2026-04-28 | **Spec**: [`specs/004-martinluk-primitive/spec.md`](./spec.md)
**Input**: Validated research artifact from `.omx/specs/autoresearch-martinluk-primitive/`

## Summary

Replace the exhausted broad 20-bar minute momentum research family with a Martin Luk-inspired swing-trading primitive: leader selection, pullback or opening-range breakout entries, tight hard stops, partial trims, and trend-following exits. The first deliverable is not strategy code. It is a source-backed public-operation ledger plus validator contract that prevents overclaiming exact private-ledger replication.

## Technical Context

**Language/Version**: Python 3.12+ for repository tooling and validation scripts
**Primary Dependencies**: Python stdlib JSON validation, existing pytest/uv stack for later strategy work
**Storage**: Repo specs under `specs/004-martinluk-primitive/`; research source artifact under `.omx/specs/autoresearch-martinluk-primitive/`; future Obsidian evidence notes under the quant-autoresearch vault
**Testing**: JSON schema checks first; later public-operation reproduction validator and focused strategy-interface tests
**Target Platform**: Local developer environment running Quant-Autoresearch backtests and validators
**Project Type**: Single-repository research system with strategy module, specs, and experiment artifacts
**Performance Goals**: Establish a public-case reproducibility gate before any broad backtest or live autoresearch mutation
**Constraints**: No exact USIC trade-ledger replication claims without complete broker/VOD/chart data; no live trading; no new dependencies; do not edit `src/strategies/active_strategy.py` until case validator exists
**Scale/Scope**: Phase 0/1 covers documentation and ledger artifacts only; later phases add validator and dry-run primitive

## Constitution Check

There is no separate planning constitution file. Policy follows `AGENTS.md` and the existing project guidance.

Pre-Phase-0 gates:
- **Evidence-first** — PASS. Source ledger records source type, confidence, use, and missing fields.
- **No overclaiming** — PASS. The plan distinguishes public-operation reproducibility from private-ledger cloning.
- **No code-first mutation** — PASS. Active strategy changes are blocked until public cases and validator are in place.
- **No new dependencies** — PASS. Phase 0/1 uses Markdown and JSON only.
- **Keep diffs reversible** — PASS. New spec folder plus index update only.

## Project Structure

```text
specs/004-martinluk-primitive/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── source-ledger.json
├── public-operation-cases.json
├── validate_public_cases.py
├── contracts/
│   └── public-operation-validator-contract.md
└── tasks.md
```

Future code work, not part of this phase:

```text
src/strategies/active_strategy.py
tests/unit/test_strategy_interface.py
experiments/iterations/run-*/
```

## Complexity Tracking

The main complexity is epistemic: public sources do not reveal every fill. The plan resolves this by making exact replication a non-goal until a complete execution ledger exists.
