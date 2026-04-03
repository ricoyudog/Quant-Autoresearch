# V2 Phase 4 — Development Plan

> Feature branch: `feature/v2-phase4`
> Umbrella issue: #10
> Canonical root: `docs/feature/v2-phase4/`
> Base branch: `main-dev`
> Planning baseline: `uv run pytest --tb=short -q` -> `97 passed`

## Context

Issue #10 was still a phase-level index card with one reference to `docs/upgrade-plan-v2.md` and no execution docs, no dedicated feature root, and no feature branch/worktree in place. Phase 4 is the final V2 closeout slice: it does not add new product behavior, but it does need to bring operator-facing docs, repo guidance, service/config surfaces, and verification instructions into alignment with the post-cleanup V2 architecture that now exists on `main-dev`.

## Canonical Root Decision

Use `docs/feature/v2-phase4/`.

Reason:
- existing V2 phase work already lives under `docs/feature/v2-phase1/`, `docs/feature/v2-phase3/`, and `docs/feature/v2-cleanup/`
- this issue is feature-scoped closeout work for the V2 upgrade, not a one-off issue-only patch
- the live repo tree has `docs/feature/*` and no active `docs/beta/*` or `docs/dev/*` planning surface

## Repo Drift Notes

- The skill reference expects beta-plan and dev-spec surfaces, but the live tree does not contain `docs/beta/` or `docs/dev/`.
- The real governing spec is `docs/upgrade-plan-v2.md` plus the already-landed V2 feature workspaces under `docs/feature/`.
- Downstream execution should use `sprintN/` docs under `docs/feature/v2-phase4/` instead of treating the umbrella phase table as the execution queue.

## Audit Snapshot

| Surface | Current drift found on `main-dev` | Planned action |
| --- | --- | --- |
| `CLAUDE.md` | Still describes OPENDEV, `src/core/engine.py`, `run/status/report`, `GROQ_API_KEY`, `MOONSHOT_API_KEY` | rewrite around V2 `program.md` + `backtest` + notes workflow |
| `README.md` | Still presents OPENDEV, prompt constitution path, old commands, old setup flow | update or archive as current V2 entrypoint |
| `architecture.md` | Entirely V1 OPENDEV deep-dive | either rewrite to V2 or mark clearly historical / archive out of primary path |
| `src/__init__.py` | Package banner still says OPENDEV | update package description text |
| `config/quant-autoresearch.service` | launches `cli.py run --iterations 100 --safety high` | align to supported V2 command surface or mark obsolete |
| `config/supervisord.conf` | launches `cli.py run` and injects `GROQ_API_KEY` | align or archive together with service unit |
| `.gitignore` | already ignores `*.log` / `*.tsv`; notes markdown is currently tracked | confirm behavior instead of changing blindly |

## Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Phase 0 — Spec Alignment | create branch, worktree, canonical docs root, and stale-surface inventory | `feature/v2-phase4`, docs workspace, audit snapshot, rewritten issue index | completed | hand off to sprint planning |
| Phase 1 — Agent Guidance Rewrite | replace V1 agent/operator guidance with V2 instructions | updated `CLAUDE.md`, command examples, environment section, architecture summary | completed | execute Sprint 2 backend docs cleanup |
| Phase 2 — Docs Surface Cleanup | update or archive user-facing V1 docs still on the main path | refreshed `README.md`, `architecture.md` decision, doc cleanup notes | pending | execute after Phase 1 lands |
| Phase 3 — Repo Hygiene & Verification | align service/config surfaces, confirm `.gitignore`, and run full checks | config decisions, verification evidence, closeout note | pending | execute after docs cleanup settles |

## Task Table

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| PLAN-01 | Create `feature/v2-phase4` branch and isolated worktree from `main-dev` | Dev | none | 0.1d | branch exists, worktree clean, baseline recorded |
| PLAN-02 | Create canonical `docs/feature/v2-phase4/` workspace | Dev | PLAN-01 | 0.1d | README + plan + lane docs exist |
| PLAN-03 | Rewrite issue #10 as an index card pointing to the workspace | Dev | PLAN-02 | 0.1d | issue contains docs workspace, phase table, task table, references |
| DOC-01 | Rewrite `CLAUDE.md` to describe V2 architecture and supported commands only | BE | PLAN-03 | 0.3d | no OPENDEV / engine / removed-command guidance remains in `CLAUDE.md` |
| DOC-02 | Audit `README.md` and decide update vs structural trim for V2 entrypoint | BE | DOC-01 | 0.2d | README reflects V2 commands, setup, and architecture |
| DOC-03 | Audit `architecture.md` and choose rewrite, archive, or removal path | BE | DOC-01 | 0.2d | file is either V2-correct or clearly removed from primary guidance surface |
| DOC-04 | Clean residual V1 wording in package/doc entrypoints (`src/__init__.py`, selected docs) | BE | DOC-02 | 0.1d | no misleading V1 banner remains in primary entrypoints |
| INFRA-01 | Confirm `.gitignore` behavior for `results.tsv`, `run.log`, and `experiments/notes/*.md` | Infra | PLAN-03 | 0.05d | behavior is verified and only changed if incorrect |
| INFRA-02 | Audit service/supervisor configs referencing `cli.py run` or old env vars | Infra | DOC-01 | 0.1d | config files are either aligned to V2 or marked obsolete with a documented decision |
| VERIFY-01 | Run dependency, test, and CLI smoke verification | QA | DOC-04, INFRA-02 | 0.1d | `uv sync --all-extras --dev`, `pytest`, and supported CLI help commands succeed |
| CLOSE-01 | Add execution evidence to sprint/update docs and prepare merge readiness | QA | VERIFY-01 | 0.05d | results, deviations, and follow-ups recorded |

## Detailed Todo

### Phase 0 — Planning Package
- [x] confirm `main-dev` includes the other feature branches needed before Phase 4 starts
- [x] create `feature/v2-phase4` from `main-dev`
- [x] establish `docs/feature/v2-phase4/` as the canonical root
- [x] rewrite issue #10 away from a single-phase prose card toward a docs-backed index

### Phase 1 — Agent Guidance Rewrite
- [x] replace the OPENDEV overview in `CLAUDE.md` with the current V2 workflow centered on `program.md`, `cli.py`, `src/core/backtester.py`, and `src/strategies/active_strategy.py`
- [x] remove obsolete command examples (`run`, `status`, `report`) and keep only supported V2 commands
- [x] update environment-variable guidance to remove `GROQ_API_KEY` and `MOONSHOT_API_KEY`
- [x] reconcile `CLAUDE.md` command examples with actual current CLI help output

### Phase 2 — Docs Surface Cleanup
- [ ] update `README.md` to stop advertising OPENDEV-only architecture and unsupported commands
- [ ] decide whether `architecture.md` becomes a V2 architecture doc, an archived historical note, or is removed
- [ ] scan top-level docs for stale V1 language that still sits on the main user-facing path
- [ ] update `src/__init__.py` banner text to match V2 wording

### Phase 3 — Repo Hygiene & Verification
- [ ] verify `.gitignore` already handles `results.tsv` and `run.log`
- [ ] verify `experiments/notes/*.md` is intentionally tracked
- [ ] decide whether `config/quant-autoresearch.service` and `config/supervisord.conf` should be updated or explicitly marked obsolete
- [ ] run full verification and record evidence in the lane docs

## Dependencies / Risks

| Risk | Mitigation |
| --- | --- |
| Scope creep into adjacent instruction files such as `AGENTS.md` | keep the initial execution queue focused on issue #10 scope; record adjacent cleanup candidates separately if needed |
| `architecture.md` may be useful as historical context even if inaccurate for runtime | decide explicitly between rewrite vs archive instead of silently deleting |
| Service config changes can affect non-dev deployments | document whether configs are active, stale, or example-only before editing them |
| Broad `.gitignore` patterns already cover the requested files | verify behavior first; do not churn ignore rules just to satisfy the checklist |
| Issue table could be mistaken for the execution queue again | create `sprintN/` docs before implementation and link them back from the issue |

## Verification Plan

- Record baseline on `feature/v2-phase4`: `uv run pytest --tb=short -q` -> `97 passed`
- Re-run dependency sync before closeout: `uv sync --all-extras --dev`
- Re-run full suite: `uv run pytest --tb=short -q`
- Smoke-test supported commands:
  - `uv run python cli.py --help`
  - `uv run python cli.py setup-data --help`
  - `uv run python cli.py fetch --help`
  - `uv run python cli.py backtest --help`
- Grep for stale guidance in touched docs before closeout:
  - `rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md config src/__init__.py`

## Acceptance Criteria

- [x] `feature/v2-phase4` branch exists from `main-dev`
- [x] `docs/feature/v2-phase4/` exists with an index plus planning docs
- [ ] issue #10 references the new docs workspace and exposes a phase table with status
- [ ] a downstream `sprintN/` execution queue is created before implementation starts
- [ ] `CLAUDE.md` is V2-correct and no longer references removed commands or removed OPENDEV components
- [ ] user-facing docs on the main path no longer advertise V1 architecture as current
- [ ] `.gitignore` behavior is verified and documented
- [ ] verification commands and outcomes are recorded in the workspace
