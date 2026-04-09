# Issue Draft C — Strategy-Facing Stock Discussion Lane

**Publication Status**

- Published on GitHub as [#20](https://github.com/ricoyudog/Quant-Autoresearch/issues/20)
- Applied label: `workflow::todo`

**Feature Branch**

- `feature/v2-minute-autoresearch`

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
| Sprint 3 | define stock-discussion lane and its boundary with analyze | sprint3 backend/infra docs | pending | execute sprint3 docs later |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| C-01 | Define strategy-facing stock-discussion structure | BE | none | 0.2d | structure supports strategy refinement |
| C-02 | Define boundary with `analyze` snapshot helper | BE | C-01 | 0.1d | snapshot vs loop boundary is explicit |
| C-03 | Define runtime/data assumptions for this lane | Infra | C-01 | 0.1d | prerequisites are documented |

**Detailed Todo**

- [ ] define where stock discussion enters the loop
- [ ] define what stays in lightweight analyze
- [ ] define how discussion feeds candidate strategies

**Dependencies / Risks**

- scope creep into generic investing analysis
- over-borrowing from TradingAgents

**Verification Plan**

- sprint3 docs exist and preserve the boundary decisions from deep-interview

**Acceptance Criteria**

- [ ] sprint3 docs are execution-ready
- [ ] stock discussion is clearly strategy-facing only

**References**

- `docs/feature/v2-minute-autoresearch/sprint3/sprint3-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint3/sprint3-infra.md`
