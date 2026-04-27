# Strategy Research Workflow

> Status: current

This page documents the default operating lane for starting and continuing
stock-strategy research in Quant Autoresearch.

The default lane is **`omx`**.

Older references to `autoresearch-first` are legacy transitional wording for
this same default lane.

Use this page for the ordered workflow. Use `docs/architecture/index.md` for
stable architecture knowledge and `program.md` for the runtime / agent
operating contract.

## Canonical References
- Runtime contract: `program.md`
- Architecture knowledge: `docs/architecture/index.md`
- Knowledge-loop artifact contract:
  `.omx/specs/strategy-knowledge-loop-artifact-contract.md`
- Current outer-loop runner: `scripts/autoresearch_runner.py`

## Current Boundary
What the runtime supports:
- `omx` as the default strategy research lane
- dry-run artifact generation from the outer-loop runner for preview/review
- live bounded multi-round execution through the outer-loop runner
- deterministic backtest / validation after candidate work
- explicit continuation context and experiment-memory refresh after live raw-note
  materialization
- first-class stock/ETF universe-selection audit artifacts
- run-level rejection memory for reverted/failed candidate families
- human review before promotion of research outcomes

What the runtime does **not** support by default:
- unsupervised promotion from one improved backtest into `validated` strategy
  knowledge
- treating dry-run runner output as final evidence
- silent continuation-memory loading during generic research intake

## Ordered Current Workflow

### 1. Gather research and knowledge context
Start with generic intake from the research surfaces described in `program.md`.

Generic intake stays anchored to:
- `quant-autoresearch/research/`
- `quant-autoresearch/knowledge/`

This stage is where the repo gathers:
- research notes
- knowledge notes
- deterministic analysis context
- the current baseline from `program.md`, `src/strategies/active_strategy.py`,
  and recent `experiments/results.tsv`

Generic intake must not silently absorb experiment continuation state.

### 2. Build or refresh continuation context
Enter continuation mode explicitly.

Use the continuation and experiment-memory surfaces when the loop is continuing
from prior experiment evidence rather than starting from generic research
intake.

The canonical continuation source is:

```text
experiments/continuation/current_research_base.json
```

This layer is refreshed through the repo’s continuation tooling, including the
`refresh_research_base` CLI surface in `cli.py` and the rebuild logic in
`src/memory/experiment_memory.py`.

### 3. Run or prepare autoresearch dry-run artifacts
Use `scripts/autoresearch_runner.py` as the current outer-loop runner.

The runner supports two clear modes.

Dry-run / preview mode:
- build iteration context
- snapshot the current strategy surface
- emit machine-first audit artifacts
- prepare a candidate iteration bundle for review

Dry-run may write iteration artifacts such as:
- `context.json`
- `context.md`
- `decision.json`
- `iteration_record.json`
- `experiment_note_draft.md`

These dry-run artifacts are rebuildable audit artifacts, not raw experiment
notes and not the canonical continuation manifest.

Live mode additionally:
- requires worker output fields `hypothesis`, `strategy_change_summary`,
  `universe_selection_summary`, `proofable_idea_sources`, and `files_touched`
- writes `universe_selection.json` from raw `select_universe(daily_data)` output
  before minute-data validation
- runs the deterministic backtest
- applies evaluator-led keep/revert/failed decisions
- materializes a canonical raw experiment note only after the worker has
  produced candidate strategy/universe evidence
- refreshes the continuation manifest when the notes directory maps to the
  configured Obsidian vault
- updates run-level `rejection_map.json` for reverted or candidate-level failed
  strategy families

Pre-evidence operational blocks, such as persistent model rate limits before the
worker returns a candidate, remain runtime audit artifacts and are not promoted
into canonical Obsidian experiment memory.

### 4. Review generated artifacts
Review emitted dry-run artifacts before treating the round as promotable
knowledge. For live runs, review the raw note plus machine artifacts before
human promotion.

In particular:
- `experiment_note_draft.md` is a derived draft
- it is **not** raw evidence
- it appears only in dry-run/operator-preview paths
- live raw notes are materialized directly by the runner after evaluator
  decision

This review step is mandatory because live materialization records evidence; it
does not by itself promote the strategy to validated status.

### 5. Run deterministic backtest and validation
After the candidate lane is reviewed, use the deterministic evaluator surfaces
from `program.md` and `cli.py`:
- `backtest`
- `validate --method cpcv`
- `validate --method regime`
- `validate --method stability`

`src/core/backtester.py` remains the evaluation boundary for sandboxed strategy
execution, enforced lag, metric computation, and score logging.
It also writes `universe_selection.json` when requested by the runner. That
artifact records raw per-window selected tickers and any `--universe-size` cap;
`PER_SYMBOL` remains evaluation output, not screener proof.

### 6. Decide keep / revert
Keep/revert authority is **evaluator/backtester-led**, not runner-led and not
draft-artifact-led.

The current decision rule is tied to the backtester outcome:
- keep only when score beats both baseline and previous best
- otherwise revert or continue follow-up work

Human review remains required before a result is treated as promotable
knowledge. A simulated dry-run record is not final evidence; a live raw note is
canonical evidence but still only `candidate` / `follow_up_required` unless
promotion rules validate it.

### 7. Record outcomes and continue the next iteration
After evaluation and review:
- preserve raw experiment evidence in the vault experiment lane
- link proofable idea sources, stock/ETF selection thesis, strategy change,
  backtest output, and keep/revert/failed decision in the raw note
- keep `experiments/results.tsv` aligned with accepted results
- refresh the canonical continuation manifest as needed
- persist rejected candidate families in `rejection_map.json`
- regenerate derived summaries and indexes without replacing raw evidence
- continue the next bounded experiment from the updated baseline

## Artifact Hierarchy
The current workflow depends on keeping these layers distinct.

### 1. Raw experiment notes / raw evidence
- stored under `quant-autoresearch/experiments/`
- first-class evidence
- append-only from the workflow’s perspective

### 2. Canonical continuation manifest
- path: `experiments/continuation/current_research_base.json`
- stable machine-readable continuation source

### 3. Derived summaries and indexes
- examples: `experiment-index.md`, branch summaries, kickoff summaries
- rebuildable views that must point back to raw evidence and the manifest

### 4. Ephemeral runner iteration artifacts
- examples: `context.md`, `context.json`, `decision.json`,
  `iteration_record.json`, `universe_selection.json`, `rejection_map.json`,
  `experiment_note_draft.md`
- rebuildable audit layer under `experiments/iterations/...`
- not raw notes
- not the canonical continuation manifest
- `experiment_note_draft.md` is dry-run/operator-preview only
- `universe_selection.json` is the machine evidence for the strategy-owned
  stock/ETF screener

## Generic Intake vs Continuation Mode
This distinction is part of the workflow contract.

### Generic intake
- default mode
- reads research and knowledge notes
- does not silently load continuation state

### Explicit continuation mode
- entered only when the operator or runner is intentionally continuing a branch
- may consume raw experiment notes, the canonical manifest, and derived
  summaries
- must still preserve the distinction between candidate, follow-up, and
  validated outcomes

## Secondary Manual Lane
The repository still supports direct manual use of `research`, `analyze`,
`backtest`, and `validate`, but that is a secondary lane for targeted work,
debugging, or focused follow-up. It is not the default documented starting path
for the current project.
