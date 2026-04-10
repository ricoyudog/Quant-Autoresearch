# V2 Minute Autoresearch — Development Plan

> Feature branch: `feature/v2-minute-autoresearch`
> Merge target: `main-dev`
> Canonical root: `docs/feature/v2-minute-autoresearch/`
> Source brief: `.omx/specs/deep-interview-spec-vs-impl.md`
> Planning status: Phase 0 complete; GitHub issue package published; merge handoff targets `main-dev`

## 1. Context

The V2 architecture is now clarified:

- The system is **not** a full TradingAgents-style decision engine
- The system **is** a minute-level autoresearch platform
- Obsidian ideas + new search produce candidate ideas
- Strategy-facing stock discussion belongs inside autoresearch
- Snapshot analysis may remain lightweight in `analyze`
- Optional factor mining exists under the same autoresearch loop
- The backtester remains the final keep/revert authority

This workspace turns that clarified architecture into a merge-ready planning package under one canonical docs root.

## 2. Root And Branch Decision

- Active docs root: `docs/`
- Canonical workspace: `docs/feature/v2-minute-autoresearch/`
- Canonical branch: `feature/v2-minute-autoresearch`
- Merge target: `main-dev`

Repo note:

- local `main-dev` existed but was fast-forwarded to match `fork/main-dev`
- GitHub issues were published on 2026-04-09 as `#17` through `#21`

## 3. Scope

- define the canonical V2 architecture package
- split the work into the required issue-sized workstreams
- create sprint docs for each child issue
- publish the issue package and keep docs aligned to the live issue set
- keep the package ready to merge into `main-dev`

## 4. Out Of Scope

- implementing the V2 architecture itself
- reopening unrelated prior feature closeout work
- reopening issue publication structure that already exists on GitHub

## 5. Workstream / Issue Topology

| Draft ID | Workstream | Purpose |
| --- | --- | --- |
| UMB | Umbrella — V2 minute autoresearch architecture | index card and planning umbrella |
| A | Autoresearch core + idea intake | Obsidian intake, self-search, loop semantics |
| B | Minute runtime + validation alignment | minute mission, data/runtime alignment, backtester invariants |
| C | Strategy-facing stock discussion lane | TradingAgents-inspired structure under autoresearch |
| D | Optional factor-mining lane | on-demand factor discovery under autoresearch |

## 6. Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Phase 0 — Architecture Alignment | lock canonical V2 shape and workspace root | deep-interview spec, branch decision, workspace root choice | completed | keep this workspace as the single planning root |
| Sprint 1 — Autoresearch Core | define loop semantics and idea-ingestion lane | issue #18, sprint1 backend/infra docs | pending | execute sprint1 docs later |
| Sprint 2 — Minute Runtime | align runtime/data/validation to the minute-level mission | issue #19, sprint2 backend/infra docs | pending | execute sprint2 docs later |
| Sprint 3 — Stock Discussion Lane | define strategy-facing stock discussion under autoresearch | issue #20, sprint3 backend/infra docs | in progress | execute Sprint 3 Step 2 discussion-output slice next |
| Sprint 4 — Factor Mining Lane | define optional factor-mining sub-mode | issue #21, sprint4 backend/infra docs | pending | execute sprint4 docs later |
| Phase 5 — Verification + Merge | verify docs coherence and merge-readiness for `main-dev` | test plan, merge-test plan, published issue links | in progress | merge planning package into `main-dev` |

## 7. Task Table

| Task ID | Task | Lane | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| PLAN-01 | Create canonical feature workspace | Planning | none | 0.1d | workspace exists under one root only |
| PLAN-02 | Draft umbrella issue card | Planning | PLAN-01 | 0.1d | issue draft has required sections and references |
| PLAN-03 | Draft child issue cards A-D | Planning | PLAN-02 | 0.2d | each workstream has a structured issue draft |
| PLAN-04 | Create sprint docs for issues A-D | Planning | PLAN-03 | 0.3d | each child issue has at least one sprint doc |
| PLAN-05 | Publish the issue package to GitHub and record live issue links | Infra | PLAN-02 | 0.1d | live issue links replace provisional draft-only status |
| PLAN-06 | Verify the full docs package against `main-dev` | QA | PLAN-04, PLAN-05 | 0.1d | references, roots, and branch targets are coherent |

## 8. Detailed Todo

- [x] create branch `feature/v2-minute-autoresearch`
- [x] create canonical docs workspace under `docs/feature/v2-minute-autoresearch/`
- [x] write README and main development plan
- [x] write backend / infra / test / merge-test planning docs
- [x] write local issue-card drafts for umbrella + four child issues
- [x] create `sprint1/` through `sprint4/` execution docs
- [x] publish the issue-card drafts to GitHub
- [x] replace provisional issue references with real issue URLs/IDs
- [ ] merge the planning package into `main-dev`

## 9. Dependencies / Risks

| Risk | Mitigation |
| --- | --- |
| GitHub issue set could drift from local docs if manually edited later | keep local issue-card drafts synced with the published cards |
| Future implementation might drift from the clarified spec | treat `.omx/specs/deep-interview-spec-vs-impl.md` as the governing brief |
| Workstreams could be too coarse or too fine | use umbrella + four child issues only |
| Merge-to-`main-dev` could accidentally mix unrelated work | keep this planning package on a dedicated feature branch |

## 10. Verification Plan

- verify branch name and target base
- verify one canonical docs root
- verify every child issue has sprint docs
- verify issue-card drafts have required sections
- verify published issue links and local draft sync

## 11. Acceptance Criteria

- [x] `docs/feature/v2-minute-autoresearch/` exists
- [x] `feature/v2-minute-autoresearch` exists and is based on `main-dev`
- [x] umbrella issue draft exists
- [x] four child issue drafts exist
- [x] `sprint1/` … `sprint4/` docs exist
- [x] GitHub issue links are published
- [x] merge target is documented as `main-dev`
- [x] real GitHub issue URLs replace draft references

## 12. References

- [README.md](./README.md)
- [v2-minute-autoresearch-backend.md](./v2-minute-autoresearch-backend.md)
- [v2-minute-autoresearch-infra.md](./v2-minute-autoresearch-infra.md)
- [v2-minute-autoresearch-test-plan.md](./v2-minute-autoresearch-test-plan.md)
- [v2-minute-autoresearch-merge-test-plan.md](./v2-minute-autoresearch-merge-test-plan.md)
- [issue-cards/umbrella-v2-minute-autoresearch.md](./issue-cards/umbrella-v2-minute-autoresearch.md)
- [issue-cards/issue-a-autoresearch-core-idea-intake.md](./issue-cards/issue-a-autoresearch-core-idea-intake.md)
- [issue-cards/issue-b-minute-runtime-validation.md](./issue-cards/issue-b-minute-runtime-validation.md)
- [issue-cards/issue-c-strategy-stock-discussion.md](./issue-cards/issue-c-strategy-stock-discussion.md)
- [issue-cards/issue-d-optional-factor-mining.md](./issue-cards/issue-d-optional-factor-mining.md)
- [#17](https://github.com/ricoyudog/Quant-Autoresearch/issues/17)
- [#18](https://github.com/ricoyudog/Quant-Autoresearch/issues/18)
- [#19](https://github.com/ricoyudog/Quant-Autoresearch/issues/19)
- [#20](https://github.com/ricoyudog/Quant-Autoresearch/issues/20)
- [#21](https://github.com/ricoyudog/Quant-Autoresearch/issues/21)
- `.omx/specs/deep-interview-spec-vs-impl.md`
