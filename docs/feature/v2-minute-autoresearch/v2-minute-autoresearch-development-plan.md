# V2 Minute Autoresearch — Development Plan

> Feature branch: `feature/v2-minute-autoresearch`
> Merge target: `main-dev`
> Canonical root: `docs/feature/v2-minute-autoresearch/`
> Source brief: `.omx/specs/deep-interview-spec-vs-impl.md`
> Planning status: Phase 0 complete; local issue/doc package created; GitLab publication blocked locally

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
- issue publication is currently blocked because `glab` is unavailable locally

## 3. Scope

- define the canonical V2 architecture package
- split the work into the required issue-sized workstreams
- create sprint docs for each child issue
- document the GitLab publication blocker without losing planning structure
- keep the package ready to merge into `main-dev`

## 4. Out Of Scope

- implementing the V2 architecture itself
- reopening unrelated prior feature closeout work
- posting GitLab cards from this machine
- guessing GitLab board IDs or workflow state without a GitLab-capable environment

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
| Sprint 1 — Autoresearch Core | define loop semantics and idea-ingestion lane | issue A draft, sprint1 backend/infra docs | pending | publish issue A when GitLab is available |
| Sprint 2 — Minute Runtime | align runtime/data/validation to the minute-level mission | issue B draft, sprint2 backend/infra docs | pending | publish issue B when GitLab is available |
| Sprint 3 — Stock Discussion Lane | define strategy-facing stock discussion under autoresearch | issue C draft, sprint3 backend/infra docs | pending | publish issue C when GitLab is available |
| Sprint 4 — Factor Mining Lane | define optional factor-mining sub-mode | issue D draft, sprint4 backend/infra docs | pending | publish issue D when GitLab is available |
| Phase 5 — Verification + Merge | verify docs coherence and merge-readiness for `main-dev` | test plan, merge-test plan, issue publication blocker note | in progress | replace draft issue references with real GitLab IDs later |

## 7. Task Table

| Task ID | Task | Lane | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| PLAN-01 | Create canonical feature workspace | Planning | none | 0.1d | workspace exists under one root only |
| PLAN-02 | Draft umbrella issue card | Planning | PLAN-01 | 0.1d | issue draft has required sections and references |
| PLAN-03 | Draft child issue cards A-D | Planning | PLAN-02 | 0.2d | each workstream has a structured issue draft |
| PLAN-04 | Create sprint docs for issues A-D | Planning | PLAN-03 | 0.3d | each child issue has at least one sprint doc |
| PLAN-05 | Record GitLab publication blocker and merge path | Infra | PLAN-02 | 0.1d | blocker and next publication step are explicit |
| PLAN-06 | Verify the full docs package against `main-dev` | QA | PLAN-04, PLAN-05 | 0.1d | references, roots, and branch targets are coherent |

## 8. Detailed Todo

- [x] create branch `feature/v2-minute-autoresearch`
- [x] create canonical docs workspace under `docs/feature/v2-minute-autoresearch/`
- [x] write README and main development plan
- [x] write backend / infra / test / merge-test planning docs
- [x] write local issue-card drafts for umbrella + four child issues
- [x] create `sprint1/` through `sprint4/` execution docs
- [ ] publish the issue-card drafts to GitLab from a GitLab-capable environment
- [ ] replace provisional issue references with real issue URLs/IDs
- [ ] merge the planning package into `main-dev`

## 9. Dependencies / Risks

| Risk | Mitigation |
| --- | --- |
| GitLab publication cannot happen locally | keep publication-ready drafts in `issue-cards/` and document blocker explicitly |
| Future implementation might drift from the clarified spec | treat `.omx/specs/deep-interview-spec-vs-impl.md` as the governing brief |
| Workstreams could be too coarse or too fine | use umbrella + four child issues only |
| Merge-to-`main-dev` could accidentally mix unrelated work | keep this planning package on a dedicated feature branch |

## 10. Verification Plan

- verify branch name and target base
- verify one canonical docs root
- verify every child issue has sprint docs
- verify issue-card drafts have required sections
- verify blocker note exists for GitLab publication

## 11. Acceptance Criteria

- [x] `docs/feature/v2-minute-autoresearch/` exists
- [x] `feature/v2-minute-autoresearch` exists and is based on `main-dev`
- [x] umbrella issue draft exists
- [x] four child issue drafts exist
- [x] `sprint1/` … `sprint4/` docs exist
- [x] GitLab blocker is documented
- [x] merge target is documented as `main-dev`
- [ ] real GitLab issue URLs replace draft references

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
- `.omx/specs/deep-interview-spec-vs-impl.md`

