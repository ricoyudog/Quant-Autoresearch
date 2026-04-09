# Issue Draft B — Minute Runtime + Validation Alignment

**Publication Status**

- Published on GitHub as [#19](https://github.com/ricoyudog/Quant-Autoresearch/issues/19)
- Applied label: `workflow::todo`

**Feature Branch**

- `feature/v2-minute-autoresearch`

**Goal**

- Converge the runtime architecture on the clarified minute-level mission while preserving the backtester as a hard invariant.

**Scope**

- minute-level mission enforcement
- data/runtime alignment
- backtester invariants
- keep/revert authority

**Out of Scope**

- stock discussion UX or discussion structure
- factor-mining mode details

**Docs Workspace**

- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-infra.md`

**Governing Specs**

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/data-pipeline-v2.md`
- `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md`

**Phase Plan**

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 2 | define minute runtime and validation alignment | sprint2 backend/infra docs | pending | execute sprint2 docs later |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| B-01 | Define minute-level runtime contract | BE | none | 0.2d | minute mission is explicit in runtime docs |
| B-02 | Define backtester invariants and keep/revert gate | BE | B-01 | 0.2d | validation engine remains non-negotiable |
| B-03 | Define environment/data prerequisites for minute pipeline | Infra | B-01 | 0.2d | prerequisites and merge assumptions are explicit |

**Detailed Todo**

- [ ] define minute-level mission enforcement
- [ ] define how current runtime drifts from target runtime
- [ ] define invariant-preserving implementation constraints

**Dependencies / Risks**

- current branch/runtime drift
- minute-pipeline complexity could push design away from autoresearch simplicity

**Verification Plan**

- sprint2 docs exist and link back to canonical spec

**Acceptance Criteria**

- [ ] sprint2 docs are execution-ready
- [ ] backtester invariants are treated as hard requirements

**References**

- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-infra.md`
