# Issue Draft D — Optional Factor-Mining Lane

**Publication Status**

- Published on GitHub as [#21](https://github.com/ricoyudog/Quant-Autoresearch/issues/21)
- Applied label: `workflow::in-progress`

**Feature Branch**

- `feature/21-optional-factor-mining`

**Goal**

- Define factor mining as an optional autoresearch sub-mode; the current Sprint 4 slice narrows to the Step 2 candidate-integration boundary for canonical factor proposals.

**Scope**

- Step 2 promotion boundary from raw factor packets into the existing candidate-generation path
- canonical proposal storage and traceability requirements before promotion
- honest lineage limits from proposal creation through current keep/revert artifacts

**Out of Scope**

- Sprint 4 Step 3 result-based judgment semantics
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
| Sprint 4 | define the Step 2 candidate-integration boundary for optional factor mining | sprint4 backend/infra docs | in progress | execute Sprint 4 Step 3 result-judgment semantics |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| D-01 | Define trigger criteria for factor mining | BE | none | 0.1d | factor mining is clearly optional |
| D-02 | Define the Step 2 canonical proposal promotion boundary | BE | D-01 | 0.2d | raw `candidate_hooks` stay research input only until a canonical proposal passes gating |
| D-03 | Define Step 2 storage / lineage guardrails | Infra | D-02 | 0.1d | only current persisted lineage surfaces are claimed |

**Detailed Todo**

- [x] define when factor mining should be invoked
- [x] define the Step 2 canonical proposal record and promotion gating before candidate generation
- [ ] define how factors are judged by results

**Dependencies / Risks**

- factor mining could bloat the main loop if not kept optional
- factor quality could be misread as success without backtester validation

**Verification Plan**

- sprint4 docs preserve the Step 2 `packet -> canonical proposal -> candidate` boundary
- docs and focused tests confirm the stated hook/seed gating plus current lineage ceiling

**Current Slice Status**

- Sprint 4 Step 2 closeout is complete and verified on `feature/21-optional-factor-mining`; Sprint 4 Step 3 remains open
- Sprint 4 backend/infra docs now define the optional trigger criteria, the Step 2 canonical proposal record, promotion blocking rules, and the current lineage ceiling for the factor-mining lane
- Step 2 explicitly keeps factor mining subordinate to the existing autoresearch candidate/backtest path instead of introducing a second candidate lane

**Verification Evidence**

- `rg -n "canonical proposal|hook_id|seed_type|candidate_hooks|traceability|contrarian_observations|candidate_id|idea_trace|analysis_context|results_tsv|experiment_note" docs/feature/v2-minute-autoresearch/sprint4 docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md -S` → matched the new Step 2 canonical proposal wording, hook/seed gating, and honest lineage limits
- `rg -n "candidate_hooks|traceability|contrarian_observations|hook_id|seed_type|build_candidate_strategy_hypothesis|idea_context\\.path|idea_context\\.source|idea_context\\.title|market_context\\.source|market_context\\.summary|idea_trace|analysis_context|results_tsv|experiment_note" src tests -S` → matched the code-backed field names and current persisted lineage surfaces referenced by the docs
- `uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_candidate_generation.py tests/unit/test_idea_keep_revert.py -q` → `11 passed`

**Acceptance Criteria**

- [x] sprint4 Step 2 docs are execution-ready
- [x] factor mining remains optional and research-input-only at promotion time
- [x] Step 2 lineage claims stop at current persisted candidate/backtest artifacts

**References**

- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-infra.md`
