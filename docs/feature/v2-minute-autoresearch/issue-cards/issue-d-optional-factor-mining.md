> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Issue Draft D — Optional Factor-Mining Lane

**Publication Status**

- Published on GitHub as [#21](https://github.com/ricoyudog/Quant-Autoresearch/issues/21)
- Applied label: `workflow::review`

**Feature Branch**

- `feature/21-optional-factor-mining`

**Goal**

- Define factor mining as an optional autoresearch sub-mode; the active Sprint 4 slice focuses on the Step 3 infra result/failure boundary for promoted factor-derived candidates while preserving the verified Step 2 promotion and lineage contract.

**Scope**

- Step 3 infra result/failure boundary for promoted factor-derived candidates
- failure / skip / defer boundaries after canonical promotion
- preserving backtester-owned keep / revert authority without introducing a second evaluation lane
- preserving the verified Step 2 promotion and lineage boundary already closed out

**Out of Scope**

- any new factor-specific scoring, ranking, or approval mechanism ahead of keep / revert
- any new artifact persistence beyond the current keep / revert-facing lineage surfaces
- mandatory factor mining in every loop
- standalone factor-mining product behavior

**Docs Workspace**

- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-infra.md`

**Governing Specs**

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/research-karpathy-autoresearch.md`
- `https://github.com/QuantaAlpha/QuantaAlpha` (reference concept only; publication environment may add a stable archived note later)

**Phase Plan**

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 4 | define the Step 3 result-judgment semantics for optional factor mining without breaking the Step 2 promotion contract | sprint4 backend/infra docs | completed | move issue #21 to review / PR |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| D-01 | Define trigger criteria for factor mining | BE | none | 0.1d | factor mining is clearly optional |
| D-02 | Define the Step 2 canonical proposal promotion boundary | BE | D-01 | 0.2d | raw `candidate_hooks` stay research input only until a canonical proposal passes gating |
| D-03 | Define Step 2 storage / lineage guardrails | Infra | D-02 | 0.1d | only current persisted lineage surfaces are claimed |
| D-04 | Define Step 3 result / failure boundaries | Infra | D-03 | 0.1d | factor-derived candidates are judged by existing backtester-owned keep / revert outcomes only |

**Detailed Todo**

- [x] define when factor mining should be invoked
- [x] define the Step 2 canonical proposal record and promotion gating before candidate generation
- [x] define how factors are judged by results

**Dependencies / Risks**

- factor mining could bloat the main loop if not kept optional
- factor quality could be misread as success without backtester validation

**Verification Plan**

- sprint4 docs preserve the Step 2 `packet -> canonical proposal -> candidate` boundary
- sprint4 docs define Step 3 result-judgment semantics through the existing `pending_backtest` / `backtester_outcome_only` contract
- docs and focused tests confirm skip / defer handling does not redefine the system mission
- docs do not claim any new hook-level or factor-level persistence beyond the current keep / revert-facing artifacts

**Current Slice Status**

- Sprint 4 Step 2 closeout remains complete and verified on `feature/21-optional-factor-mining`
- Sprint 4 Step 3 is now complete across both backend and infra docs
- Sprint 4 now defines promoted factor-derived candidates as normal `pending_backtest` candidates until the existing keep / revert outcome resolves them, and failed factor proposals or candidates are culled through that same keep / revert path instead of a new score
- Sprint 4 now limits failure handling to skip / defer inside the current mission; it does not redefine the mission, add a parallel authority, or claim any new artifact persistence
- Sprint 4 now keeps factor mining subordinate to the existing autoresearch candidate -> backtest -> keep / revert path end-to-end and is ready for review handoff

**Verification Evidence**

- `rg -n "canonical proposal|hook_id|seed_type|candidate_hooks|traceability|contrarian_observations|candidate_id|idea_trace|analysis_context|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S` → matched the canonical proposal wording, hook/seed gating, and honest lineage limits
- `rg -n "pending_backtest|backtester_required|backtester_outcome_only|keep/revert|discard|revert|skip|defer|mission" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S` → matched the Step 3 infra boundary wording that keeps result judgment on the existing keep / revert path and limits failure handling to skip / defer inside the current mission
- `rg -n "candidate_hooks|traceability|contrarian_observations|hook_id|seed_type|build_candidate_strategy_hypothesis|idea_context\\.path|idea_context\\.source|idea_context\\.title|market_context\\.source|market_context\\.summary|idea_trace|analysis_context|results_tsv|experiment_note" src tests -S` → matched the code-backed field names and current persisted lineage surfaces referenced by the docs
- `uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q` → `11 passed`
- `uv run python -m compileall src cli.py` → passed

**Acceptance Criteria**

- [x] sprint4 Step 2 docs are execution-ready
- [x] factor mining remains optional and research-input-only at promotion time
- [x] Step 2 lineage claims stop at current persisted candidate/backtest artifacts
- [x] Step 3 result judgment stays inside the existing `pending_backtest` / `backtester_outcome_only` contract
- [x] weak factor proposals or candidates are eliminated only through the existing keep / revert outcome
- [x] Step 3 failure handling is limited to skip / defer inside the current mission and does not claim new persistence
- [x] Sprint 4 issue work is complete and ready for `workflow::review`

**References**

- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-infra.md`
