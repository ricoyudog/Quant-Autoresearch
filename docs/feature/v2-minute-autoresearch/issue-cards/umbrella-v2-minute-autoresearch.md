# Umbrella Draft — V2 Minute Autoresearch Architecture

**Publication Status**

- Published on GitHub as [#17](https://github.com/ricoyudog/Quant-Autoresearch/issues/17)
- Applied label: `workflow::todo`

**Feature Branch**

- `feature/v2-minute-autoresearch`

**Goal**

- Turn the clarified deep-interview architecture into a canonical, spec-driven V2 planning package for minute-level autoresearch.

**Scope**

- autoresearch core
- minute-level runtime/validation alignment
- strategy-facing stock discussion lane
- optional factor-mining lane
- merge-ready planning docs for `main-dev`

**Out of Scope**

- full TradingAgents / LangGraph decision runtime
- generic daily-investment research mode
- immediate implementation from this draft

**Docs Workspace**

- `docs/feature/v2-minute-autoresearch/README.md`
- `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-development-plan.md`
- `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-backend.md`
- `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-infra.md`
- `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-test-plan.md`
- `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-merge-test-plan.md`

**Governing Specs**

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/research-karpathy-autoresearch.md`
- `docs/research-tradingagents.md`
- `docs/research-capabilities-v2.md`
- `docs/data-pipeline-v2.md`
- `program.md`

**Phase Plan**

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Phase 0 — Spec Alignment | keep one canonical V2 architecture brief | deep-interview spec, branch choice, root choice | completed | preserve this workspace as source of truth |
| Sprint 1 — Autoresearch Core | define core loop + idea intake lane | issue #18 + sprint1 docs | pending | execute sprint1 docs later |
| Sprint 2 — Minute Runtime | define minute-level runtime and validation lane | issue #19 + sprint2 docs | pending | execute sprint2 docs later |
| Sprint 3 — Stock Discussion Lane | define strategy-facing stock discussion lane | issue #20 + sprint3 docs + packet contract | completed | move issue #20 into review / PR |
| Sprint 4 — Factor Mining Lane | define optional factor-mining lane | issue #21 + sprint4 docs | in progress | complete Sprint 4 Step 3 result-judgment semantics |
| Phase 5 — Verification / Merge | verify docs + merge readiness | test docs, merge-test plan, published issue links | in progress | merge planning package into `main-dev` |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| UMB-01 | Create canonical workspace | Planning | none | 0.1d | root exists under `docs/feature/` only |
| UMB-02 | Draft child issues A-D | Planning | UMB-01 | 0.2d | four workstream issue drafts exist |
| UMB-03 | Create sprint docs | Planning | UMB-02 | 0.3d | each child issue maps to sprint docs |
| UMB-04 | Record GitLab blocker honestly | Infra | UMB-01 | 0.05d | no artifact falsely claims publication |

**Detailed Todo**

- [x] publish umbrella and child drafts to GitHub
- [x] add real issue IDs/URLs back into this umbrella card
- [ ] use the sprint docs as the execution handoff surface

**Dependencies / Risks**

- keep local draft and GitHub issue #17 synchronized
- current implementation may still drift from target V2
- merge should target `main-dev`, not the stale `feature/v2-research` branch

**Verification Plan**

- see `v2-minute-autoresearch-test-plan.md`
- see `v2-minute-autoresearch-merge-test-plan.md`

**Acceptance Criteria**

- [x] canonical workspace exists
- [x] umbrella draft exists
- [x] child issue drafts exist
- [x] sprint docs exist
- [x] GitHub publication completed

**References**

- `docs/feature/v2-minute-autoresearch/v2-minute-autoresearch-development-plan.md`
- `docs/feature/v2-minute-autoresearch/issue-cards/issue-a-autoresearch-core-idea-intake.md`
- `docs/feature/v2-minute-autoresearch/issue-cards/issue-b-minute-runtime-validation.md`
- `docs/feature/v2-minute-autoresearch/issue-cards/issue-c-strategy-stock-discussion.md`
- `docs/feature/v2-minute-autoresearch/issue-cards/issue-d-optional-factor-mining.md`
- [#17](https://github.com/ricoyudog/Quant-Autoresearch/issues/17)
- [#18](https://github.com/ricoyudog/Quant-Autoresearch/issues/18)
- [#19](https://github.com/ricoyudog/Quant-Autoresearch/issues/19)
- [#20](https://github.com/ricoyudog/Quant-Autoresearch/issues/20)
- [#21](https://github.com/ricoyudog/Quant-Autoresearch/issues/21)
