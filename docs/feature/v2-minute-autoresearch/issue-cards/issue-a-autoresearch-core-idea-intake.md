> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Issue Draft A — Autoresearch Core + Idea Intake

**Publication Status**

- Published on GitHub as [#18](https://github.com/ricoyudog/Quant-Autoresearch/issues/18)
- Applied label: `workflow::done`
- Merged to `main-dev` via [PR #23](https://github.com/ricoyudog/Quant-Autoresearch/pull/23) on `2026-04-09`

**Feature Branch**

- `feature/v2-minute-autoresearch`

**Goal**

- Define the core autoresearch loop that ingests ideas from Obsidian and self-search, then turns them into candidate strategy refinements.

**Scope**

- idea ingestion from daily Obsidian capture
- self-search for new ideas
- candidate-generation / strategy-refinement semantics
- results-first loop contract

**Out of Scope**

- minute runtime internals
- stock discussion lane specifics
- factor-mining implementation details

**Docs Workspace**

- `docs/feature/v2-minute-autoresearch/sprint1/sprint1-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint1/sprint1-infra.md`

**Governing Specs**

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/research-karpathy-autoresearch.md`
- `program.md`

**Phase Plan**

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 1 | define autoresearch core loop and idea intake | sprint1 backend/infra docs plus merged runtime contracts | completed | none |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| A-01 | Define idea-ingestion sources and trigger points | BE | none | 0.2d | Obsidian + self-search roles are explicit |
| A-02 | Define loop semantics for candidate generation and strategy update | BE | A-01 | 0.3d | loop contract is explicit |
| A-03 | Define infra/runtime assumptions for the loop | Infra | A-01 | 0.1d | environment and data prerequisites are documented |

**Detailed Todo**

- [x] finalize the exact idea-ingestion contract
- [x] finalize the autoresearch iteration contract
- [x] define keep/revert flow boundaries

**Dependencies / Risks**

- unclear coupling to current CLI surfaces
- drift between `program.md` and future runtime orchestration

**Verification Plan**

- sprint1 docs exist and stay aligned to the canonical spec

**Verification Evidence**

- `uv run pytest tests/unit/test_idea_intake.py tests/unit/test_idea_search_policy.py tests/unit/test_idea_keep_revert.py tests/unit/test_candidate_generation.py tests/unit/test_program_guidance.py tests/unit/test_cli.py tests/unit/test_backtester_v2.py -q` → `83 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors

**Implementation Summary**

- Added vault idea-intake helpers in `src/memory/idea_intake.py`
- Added self-search cadence/routing in `src/memory/idea_search_policy.py`
- Added candidate-generation helpers in `src/memory/candidate_generation.py`
- Added keep/revert and iteration-record helpers in `src/memory/idea_keep_revert.py`
- Updated `program.md` and synchronized Sprint 1 backend/infra docs

**Closeout Notes**

- Post-merge review found one latent contract mismatch: `build_candidate_strategy_hypothesis()` returns `idea_reference`, while `build_backtest_handoff()` expects `structured_context`; no current runtime call site wires these helpers together yet, so this remains a follow-up rather than a reopened blocker for Sprint 1.

**Acceptance Criteria**

- [x] sprint1 backend/infra docs are execution-ready
- [x] idea ingestion and candidate generation are unambiguous

**References**

- `docs/feature/v2-minute-autoresearch/sprint1/sprint1-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint1/sprint1-infra.md`
- `src/memory/idea_intake.py`
- `src/memory/idea_search_policy.py`
- `src/memory/candidate_generation.py`
- `src/memory/idea_keep_revert.py`
- `program.md`
- [PR #23](https://github.com/ricoyudog/Quant-Autoresearch/pull/23)
- [Issue #18](https://github.com/ricoyudog/Quant-Autoresearch/issues/18)
