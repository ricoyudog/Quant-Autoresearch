# Sprint 1 — Backend Plan

> Feature: `v2-phase4`
> Role: Backend
> Derived from: #10 (Phase 4: closeout alignment)
> Last Updated: 2026-04-03

## 0) Governing Specs

1. `docs/upgrade-plan-v2.md` — Phase 4 closeout scope (`CLAUDE.md`, docs cleanup, verification)
2. `docs/feature/v2-phase4/v2-phase4-development-plan.md` — task table and audit snapshot
3. `program.md` — current V2 instruction source that `CLAUDE.md` must align to
4. `cli.py` and current CLI help output — supported command surface (`fetch`, `setup-data`, `backtest`)

## 1) Sprint Mission

Rewrite `CLAUDE.md` so it describes the actual V2 architecture and supported operator workflow on `main-dev`, removing stale OPENDEV-era runtime guidance without changing product behavior.

## 2) Scope / Out of Scope

**Scope**
- rewrite the `CLAUDE.md` project overview around the current V2 architecture
- remove references to deleted V1 runtime components and unsupported commands
- align command examples with the current CLI
- align environment-variable guidance with the surviving V2 surfaces

**Out of Scope**
- `README.md` rewrite
- `architecture.md` rewrite or archival decision
- `.gitignore` changes
- service/supervisor config changes

## 3) Step-by-Step Plan

### Step 1 — Rewrite `CLAUDE.md` to V2 truth surface (DOC-01)
- [ ] inspect `CLAUDE.md`, `program.md`, `cli.py`, and current CLI help output together before editing
- [ ] replace the OPENDEV overview with the V2 workflow centered on `program.md`, `cli.py`, `src/core/backtester.py`, `src/data/connector.py`, and `src/strategies/active_strategy.py`
- [ ] remove references to deleted modules: `src/core/engine.py`, `src/context/*`, `src/tools/registry.py`, `src/models/router.py`, and removed prompt-composition flow
- [ ] remove unsupported command examples: `run`, `status`, `report`
- [ ] remove obsolete env vars: `GROQ_API_KEY`, `MOONSHOT_API_KEY`
- [ ] verify with:
  - `rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md`
  - `uv run python cli.py --help`

### Step 2 — Record sprint evidence and sync issue-facing status
- [ ] record the exact verification results in this sprint doc
- [ ] update the umbrella plan or issue card next-step wording if the slice outcome changes

### Step 3 — Commit sprint 1 doc + implementation changes
- [ ] `git add CLAUDE.md docs/feature/v2-phase4/sprint1/sprint1-backend.md docs/feature/v2-phase4/README.md`
- [ ] `git commit -m "docs(v2-phase4): rewrite CLAUDE for current V2 architecture"`

## 4) Test Plan

- [ ] grep confirms stale V1 runtime and removed-command references are gone from `CLAUDE.md`
- [ ] `uv run python cli.py --help` still shows only supported commands
- [ ] no runtime code changes are introduced by the doc rewrite

## 5) Verification Commands

```bash
rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md
uv run python cli.py --help
uv run python cli.py setup_data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
```

## 6) Implementation Update Space

### Completed Work

- leave blank until implemented

### Command Results

- leave blank until implemented

### Blockers / Deviations

- leave blank until implemented

### Follow-ups

- leave blank until implemented
