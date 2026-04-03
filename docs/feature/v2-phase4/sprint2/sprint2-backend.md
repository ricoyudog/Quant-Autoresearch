# Sprint 2 — Backend Plan

> Feature: `v2-phase4`
> Role: Backend
> Derived from: #10 (Phase 4: closeout alignment)
> Last Updated: 2026-04-03

## 0) Governing Specs

1. `docs/upgrade-plan-v2.md` — Phase 4 closeout scope
2. `docs/feature/v2-phase4/v2-phase4-development-plan.md` — phase/task mapping
3. `docs/feature/v2-phase4/sprint1/sprint1-backend.md` — Sprint 1 output must land first

## 1) Sprint Mission

Clean the primary documentation path after `CLAUDE.md` is fixed: update `README.md`, resolve the status of `architecture.md`, and remove residual V1 wording from entrypoint-level files.

## 2) Scope / Out of Scope

**Scope**
- update `README.md` to the current V2 architecture and supported commands
- choose and execute the right treatment for `architecture.md`
- update `src/__init__.py` or other primary entrypoint wording still describing OPENDEV as current

**Out of Scope**
- `CLAUDE.md` rewrite
- `.gitignore` changes
- service/supervisor config changes
- final repo-wide verification

## 3) Step-by-Step Plan

### Step 1 — Refresh `README.md` for V2 entrypoint alignment
- [ ] replace OPENDEV-first positioning with current V2 positioning
- [ ] update quick-start and command examples to the supported CLI
- [ ] align project structure with surviving modules and directories

### Step 2 — Resolve `architecture.md`
- [ ] decide whether to rewrite, archive with a clear banner, or remove it from the primary path
- [ ] execute the chosen path so the file no longer misrepresents current runtime truth

### Step 3 — Clean residual entrypoint wording
- [ ] update `src/__init__.py` and any touched primary entrypoint docs that still describe OPENDEV as current
- [ ] verify with:
  - `rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" README.md architecture.md src/__init__.py`

### Step 4 — Commit sprint 2 changes
- [ ] `git add README.md architecture.md src/__init__.py docs/feature/v2-phase4/sprint2/sprint2-backend.md`
- [ ] `git commit -m "docs(v2-phase4): align README and entrypoint docs with V2"`

## 4) Test Plan

- [ ] stale V1 wording is gone from the current/kept primary docs
- [ ] supported CLI commands still match doc examples
- [ ] any historical-doc decision for `architecture.md` is explicit

## 5) Verification Commands

```bash
rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" README.md architecture.md src/__init__.py
uv run python cli.py --help
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
