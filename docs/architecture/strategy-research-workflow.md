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
The current workflow is not a fully live autonomous multi-round strategy
mutation loop.

What the runtime does support:
- `omx` as the default strategy research lane
- dry-run artifact generation from the outer-loop runner
- deterministic backtest / validation after candidate work
- explicit continuation context and experiment-memory refresh
- human review before promotion of research outcomes

What the runtime does **not** support by default:
- unsupervised promotion from runner draft artifacts into validated strategy
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

The current default posture is **dry-run-first**:
- build iteration context
- snapshot the current strategy surface
- emit machine-first audit artifacts
- prepare a candidate iteration bundle for review

At this stage the runner may write iteration artifacts such as:
- `context.json`
- `context.md`
- `decision.json`
- `iteration_record.json`
- `experiment_note_draft.md`

These are rebuildable audit artifacts, not raw experiment notes and not the
canonical continuation manifest.

### 4. Review generated artifacts
Review the emitted dry-run artifacts before treating the round as promotable
knowledge.

In particular:
- `experiment_note_draft.md` is a derived draft
- it is **not** raw evidence
- it must not replace a raw experiment note
- only an explicit finalize flow may materialize a real vault experiment note

This review step is mandatory because the runner output is scaffolded for
auditability, not automatic promotion.

### 5. Run deterministic backtest and validation
After the candidate lane is reviewed, use the deterministic evaluator surfaces
from `program.md` and `cli.py`:
- `backtest`
- `validate --method cpcv`
- `validate --method regime`
- `validate --method stability`

`src/core/backtester.py` remains the evaluation boundary for sandboxed strategy
execution, enforced lag, metric computation, and score logging.

### 6. Decide keep / revert
Keep/revert authority is **evaluator/backtester-led**, not runner-led and not
draft-artifact-led.

The current decision rule is tied to the backtester outcome:
- keep only when score beats both baseline and previous best
- otherwise revert or continue follow-up work

Human review remains required before a result is treated as promotable
knowledge. A runner draft or simulated dry-run record is not final evidence.

### 7. Record outcomes and continue the next iteration
After evaluation and review:
- preserve raw experiment evidence in the vault experiment lane
- keep `experiments/results.tsv` aligned with accepted results
- refresh the canonical continuation manifest as needed
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
  `iteration_record.json`, `experiment_note_draft.md`
- rebuildable audit layer under `experiments/iterations/...`
- not raw notes
- not the canonical continuation manifest

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
