# Architecture Index

> Status: current

This is the canonical architecture and project-knowledge entrypoint for the
repository.

Use this page to understand the system shape, where truth lives, and the
runtime boundaries.

- For the runtime / agent operating contract, use `program.md`.
- For the current ordered strategy-iteration lane, use
  `docs/architecture/strategy-research-workflow.md`.
- For planning and long-horizon initiative tracking, use `docs/program/index.md`.

## Project Intent
Quant Autoresearch is a local-first quantitative research system for iterating
stock strategies on minute-level US equities data with explicit overfit
defenses.

The project is organized around four core concerns:
- a runtime contract and CLI surface
- a local market-data pipeline
- a strategy evaluation and validation stack
- a knowledge / memory loop that supports continuation across experiments

## Active Truth Surfaces
- `program.md` — runtime / agent operating contract
- `cli.py` — supported CLI command surface for data setup, research, analysis,
  backtest, validation, and continuation refresh
- `src/data/duckdb_connector.py` — DuckDB daily-cache build / refresh and
  bounded minute-data queries
- `src/core/backtester.py` — strategy sandboxing, enforced lag, walk-forward
  evaluation, metrics, and `results.tsv` writes
- `src/core/research.py` and `src/analysis/` — research retrieval, market
  analysis, and report rendering surfaces
- `src/strategies/active_strategy.py` — current strategy-under-iteration surface
- `src/memory/idea_intake.py` — generic research / knowledge intake boundary
- `src/memory/candidate_generation.py` — candidate hypothesis construction from
  idea, market, and baseline context
- `src/memory/idea_keep_revert.py` — keep / revert handoff and
  evaluator/backtester-led decision logic
- `src/memory/experiment_memory.py` — continuation manifest refresh, derived
  summaries, and experiment-memory rebuild logic
- `.omx/specs/strategy-knowledge-loop-artifact-contract.md` — artifact and
  continuation boundary contract
- `scripts/autoresearch_runner.py` — current outer-loop runner and dry-run
  artifact surface

## Architecture Layers

### 1. Runtime Contract and CLI Surface
`program.md` is the normative runtime description for the current repo. It owns
the canonical statements about:
- the minute-data pipeline and cache paths
- supported CLI commands
- the strategy interface
- the walk-forward backtest flow
- validation rules and score interpretation
- memory-access expectations and current runner boundaries

`cli.py` is the executable surface that exposes the contract in operational
form, including:
- `setup-data` / `update-data`
- `setup_vault`
- `refresh_research_base`
- `research`
- `analyze`
- `backtest`
- `validate`

### 2. Data and Market Access Layer
The project uses a local-first market-data model:
- daily bars are materialized into `data/daily_cache.duckdb`
- minute bars are queried on demand through the external `minute-aggs` CLI
- `src/data/duckdb_connector.py` owns daily-cache build / refresh and bounded
  minute-window access

This architecture keeps large source data outside the repo runtime while making
the backtester and analysis stack deterministic against a local cache.

### 3. Strategy and Evaluation Layer
`src/strategies/active_strategy.py` is the strategy-under-iteration surface.

`src/core/backtester.py` owns the evaluation boundary:
- sandbox / security checks
- strategy loading
- enforced 1-bar signal lag
- walk-forward metric computation
- score logging to `experiments/results.tsv`

Validation remains part of the architecture, not an optional afterthought. The
runtime uses overfit-defense checks such as CPCV, regime validation, stability
checks, and adjusted Sharpe framing from `program.md`.

### 4. Research and Analysis Layer
`src/core/research.py` and `src/analysis/` provide external-context and
market-context surfaces before strategy mutation:
- research note retrieval and reuse
- market analysis report generation
- deterministic ticker-level analysis from local data

This layer exists so new hypotheses are grounded before the strategy surface is
edited.

### 5. Knowledge, Memory, and Continuation Layer
Generic research intake and explicit continuation state are separate.

- `src/memory/idea_intake.py` keeps default intake anchored to vault
  `research/` and `knowledge/` notes
- `src/memory/candidate_generation.py` turns structured idea context into one
  bounded candidate hypothesis against the current baseline
- `src/memory/idea_keep_revert.py` preserves evaluator/backtester-led
  keep/revert decisions
- `src/memory/experiment_memory.py` rebuilds the continuation manifest and
  derived summaries from raw experiment evidence

The artifact hierarchy is defined by
`.omx/specs/strategy-knowledge-loop-artifact-contract.md`:
1. raw experiment notes under `quant-autoresearch/experiments/`
2. the canonical continuation manifest at
   `experiments/continuation/current_research_base.json`
3. derived summaries such as `experiment-index.md` and branch summaries

Outside that hierarchy, the runtime may emit rebuildable iteration artifacts
under `experiments/iterations/...`; those files are audit artifacts, not raw
notes and not the canonical continuation manifest.

### 6. Autoresearch Orchestration Boundary
`scripts/autoresearch_runner.py` is the current outer-loop orchestration surface.

Its current role is to manage:
- run state
- continuation context loading
- strategy snapshots
- context bundles and per-iteration audit artifacts
- deterministic evaluation handoff

Its current boundary matters:
- the current default lane is `omx`
- the runner is still **dry-run-first**
- `experiment_note_draft.md` is a derived draft, not raw evidence
- keep/revert authority remains evaluator/backtester-led
- the current system should not be described as a fully live autonomous
  multi-round mutation loop

## Canonical Boundaries
- `program.md` owns the runtime contract and command-level operational truth.
- `docs/architecture/index.md` owns stable architecture, truth-surface mapping,
  and boundary explanations.
- `docs/architecture/strategy-research-workflow.md` owns the ordered current
  strategy-iteration lane.
- `docs/program/index.md` remains the planning and long-horizon hub, not the
  current default operating workflow page.

## Current Default Operating Direction
The project’s default operating direction is the **`omx` lane**. The current
implementation still relies on dry-run artifact generation,
deterministic evaluator/backtester output, and human review before a branch is
promotable knowledge.

Older references to `autoresearch-first` should be treated as legacy wording
for this same default lane.

Use `docs/architecture/strategy-research-workflow.md` for the current ordered
lane. This architecture page should stay structural and non-procedural.

## Historical Note
The root `architecture.md` file remains a compatibility stub while this page is
the canonical architecture entrypoint.
