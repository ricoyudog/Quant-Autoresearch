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
- [x] inspect `CLAUDE.md`, `program.md`, `cli.py`, and current CLI help output together before editing
- [x] replace the OPENDEV overview with the V2 workflow centered on `program.md`, `cli.py`, `src/core/backtester.py`, `src/data/connector.py`, and `src/strategies/active_strategy.py`
- [x] remove references to deleted modules: `src/core/engine.py`, `src/context/*`, `src/tools/registry.py`, `src/models/router.py`, and removed prompt-composition flow
- [x] remove unsupported command examples: `run`, `status`, `report`
- [x] remove obsolete env vars: `GROQ_API_KEY`, `MOONSHOT_API_KEY`
- [x] verify with:
  - `rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md`
  - `uv run python cli.py --help`

### Step 2 — Record sprint evidence and sync issue-facing status
- [x] record the exact verification results in this sprint doc
- [x] update the umbrella plan or issue card next-step wording if the slice outcome changes

### Step 3 — Commit sprint 1 doc + implementation changes
- [x] `git add CLAUDE.md docs/feature/v2-phase4/sprint1/sprint1-backend.md docs/feature/v2-phase4/README.md`
- [x] `git commit -m "docs(v2-phase4): rewrite CLAUDE for current V2 architecture"`

## 4) Test Plan

- [x] grep confirms stale V1 runtime and removed-command references are gone from `CLAUDE.md`
- [x] `uv run python cli.py --help` still shows only supported commands
- [x] no runtime code changes are introduced by the doc rewrite

## 5) Verification Commands

```bash
rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md
uv run python cli.py --help
uv run python cli.py setup-data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
```

## 6) Implementation Update Space

### Completed Work

- Rewrote `CLAUDE.md` around the current V2 workflow instead of the removed legacy runtime
- Aligned the guidance to `program.md`, `cli.py`, `src/core/backtester.py`, `src/data/connector.py`, and `src/strategies/active_strategy.py`
- Removed references to deleted runtime modules, unsupported CLI commands, and obsolete `GROQ_API_KEY` / `MOONSHOT_API_KEY`
- Corrected the command examples to the real Typer command name `setup-data`

### Command Results

- `rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md` -> no matches, exit 1
- `uv run python cli.py --help` -> commands shown: `fetch`, `setup-data`, `backtest`
- `uv run python cli.py setup-data --help` -> exit 0
- `uv run python cli.py fetch --help` -> exit 0
- `uv run python cli.py backtest --help` -> exit 0

### Blockers / Deviations

- Initial verification caught one stale command spelling (`setup_data`) and two negative legacy-term mentions; all were corrected before marking Step 1 complete

### Follow-ups

- None; Sprint 2 and Sprint 3 downstream lanes are complete and issue #10 remains in `workflow::review`.
