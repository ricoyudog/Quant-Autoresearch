# Issue Draft D — Optional Factor-Mining Lane

**Publication Status**

- Published on GitHub as [#21](https://github.com/ricoyudog/Quant-Autoresearch/issues/21)
- Applied label: `workflow::todo`

**Feature Branch**

- `feature/v2-minute-autoresearch`

**Goal**

- Define factor mining as an optional autoresearch sub-mode that can be invoked when the main loop needs new alpha primitives/features.

**Scope**

- factor mining trigger criteria
- relationship to autoresearch idea generation
- result-based evaluation of factor usefulness

**Out of Scope**

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
| Sprint 4 | define optional factor-mining sub-mode | sprint4 backend/infra docs | pending | execute sprint4 docs later |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| D-01 | Define trigger criteria for factor mining | BE | none | 0.1d | factor mining is clearly optional |
| D-02 | Define how factor mining feeds candidate generation | BE | D-01 | 0.2d | factor ideas stay under autoresearch |
| D-03 | Define runtime/data assumptions and failure boundaries | Infra | D-01 | 0.1d | assumptions are explicit |

**Detailed Todo**

- [ ] define when factor mining should be invoked
- [ ] define how factors become strategy candidates
- [ ] define how factors are judged by results

**Dependencies / Risks**

- factor mining could bloat the main loop if not kept optional
- factor quality could be misread as success without backtester validation

**Verification Plan**

- sprint4 docs exist and preserve the optional-submode rule

**Acceptance Criteria**

- [ ] sprint4 docs are execution-ready
- [ ] factor mining is optional and results-first

**References**

- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint4/sprint4-infra.md`
