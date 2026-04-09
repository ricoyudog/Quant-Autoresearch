# Issue Draft A — Autoresearch Core + Idea Intake

**Publication Status**

- Published on GitHub as [#18](https://github.com/ricoyudog/Quant-Autoresearch/issues/18)
- Applied label: `workflow::todo`

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
| Sprint 1 | define autoresearch core loop and idea intake | sprint1 backend/infra docs | pending | execute sprint1 docs later |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| A-01 | Define idea-ingestion sources and trigger points | BE | none | 0.2d | Obsidian + self-search roles are explicit |
| A-02 | Define loop semantics for candidate generation and strategy update | BE | A-01 | 0.3d | loop contract is explicit |
| A-03 | Define infra/runtime assumptions for the loop | Infra | A-01 | 0.1d | environment and data prerequisites are documented |

**Detailed Todo**

- [ ] finalize the exact idea-ingestion contract
- [ ] finalize the autoresearch iteration contract
- [ ] define keep/revert flow boundaries

**Dependencies / Risks**

- unclear coupling to current CLI surfaces
- drift between `program.md` and future runtime orchestration

**Verification Plan**

- sprint1 docs exist and stay aligned to the canonical spec

**Acceptance Criteria**

- [ ] sprint1 backend/infra docs are execution-ready
- [ ] idea ingestion and candidate generation are unambiguous

**References**

- `docs/feature/v2-minute-autoresearch/sprint1/sprint1-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint1/sprint1-infra.md`
