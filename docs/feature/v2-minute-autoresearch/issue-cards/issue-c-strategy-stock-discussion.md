# Issue Draft C — Strategy-Facing Stock Discussion Lane

**Publication Status**

- Published on GitHub as [#20](https://github.com/ricoyudog/Quant-Autoresearch/issues/20)
- Applied label: `workflow::review`

**Feature Branch**

- `feature/20-strategy-stock-discussion`

**Goal**

- Define how TradingAgents-inspired stock discussion should support strategy refinement without turning the system into a full TradingAgents clone.

**Scope**

- strategy-facing stock discussion inside autoresearch
- boundary with lightweight deterministic `analyze`
- structure of discussion outputs and their role in strategy refinement

**Out of Scope**

- generic stock-picking assistant behavior
- full debate-orchestration runtime

**Docs Workspace**

- `docs/feature/v2-minute-autoresearch/sprint3/sprint3-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint3/sprint3-infra.md`

**Governing Specs**

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/research-tradingagents.md`
- `docs/research-capabilities-v2.md`

**Phase Plan**

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 3 | define stock-discussion lane and its boundary with analyze | sprint3 backend/infra docs plus discussion packet contract | completed | open PR / review the branch |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| C-01 | Define strategy-facing stock-discussion structure | BE | none | 0.2d | structure supports strategy refinement |
| C-02 | Define boundary with `analyze` snapshot helper | BE | C-01 | 0.1d | snapshot vs loop boundary is explicit |
| C-03 | Define runtime/data assumptions for this lane | Infra | C-01 | 0.1d | prerequisites are documented |

**Detailed Todo**

- [x] define where stock discussion enters the loop
- [x] define what stays in lightweight analyze
- [x] define how discussion feeds candidate strategies

**Dependencies / Risks**

- scope creep into generic investing analysis
- over-borrowing from TradingAgents

**Verification Plan**

- sprint3 docs exist and preserve the boundary decisions from deep-interview

**Current Slice Status**

- Sprint 3 Step 1 and Step 2 are complete on `feature/20-strategy-stock-discussion`
- Current branch includes `src/analysis/discussion_routing.py`
- Current branch includes `src/analysis/discussion_packet.py`
- Current branch includes `tests/unit/test_discussion_routing.py`
- Current branch includes `tests/unit/test_discussion_packet.py`
- Sprint 3 backend/infra docs now reflect the routing boundary, packet contract, non-decision guardrails, and traceability surface

**Verification Evidence**

- `uv run pytest tests/unit/test_discussion_packet.py -q` → `3 passed`
- `uv run pytest tests/unit/test_discussion_packet.py tests/unit/test_discussion_routing.py tests/unit/test_cli_analyze.py tests/integration/test_analyze_pipeline.py -q` → `13 passed`
- `uv run pytest tests/unit/test_discussion_routing.py tests/unit/test_cli_analyze.py tests/unit/test_market_context.py tests/unit/test_regime.py tests/unit/test_technical.py tests/integration/test_analyze_pipeline.py -q` → `28 passed`
- `uv run python -m compileall src cli.py` → completed without compile errors

**Acceptance Criteria**

- [x] sprint3 docs are execution-ready
- [x] stock discussion is clearly strategy-facing only

**References**

- `docs/feature/v2-minute-autoresearch/sprint3/sprint3-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint3/sprint3-infra.md`
