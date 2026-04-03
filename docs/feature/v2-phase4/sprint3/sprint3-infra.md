# Sprint 3 — Infra Plan

> Feature: `v2-phase4`
> Role: Infra
> Derived from: #10 (Phase 4: closeout alignment)
> Last Updated: 2026-04-03

## 0) Governing Specs

1. `docs/upgrade-plan-v2.md` — Phase 4 closeout scope
2. `docs/feature/v2-phase4/v2-phase4-development-plan.md` — infra task mapping and verification plan
3. `docs/feature/v2-phase4/v2-phase4-test-plan.md` — final verification matrix

## 1) Sprint Mission

Verify repo hygiene and operator surfaces after the documentation cleanup lands: confirm `.gitignore` behavior, resolve config drift around obsolete `cli.py run` surfaces, and run the full closeout verification set.

## 2) Scope / Out of Scope

**Scope**
- verify `.gitignore` behavior for `results.tsv`, `run.log`, and markdown notes under `experiments/notes/`
- audit `config/quant-autoresearch.service` and `config/supervisord.conf`
- run dependency sync, test suite, and CLI smoke verification
- record closeout evidence and deviations

**Out of Scope**
- rewriting `CLAUDE.md`
- rewriting `README.md`
- broad runtime code refactors

## 3) Step-by-Step Plan

### Step 1 — Confirm ignore behavior
- [ ] run `git check-ignore -v results.tsv run.log`
- [ ] run `git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"`
- [ ] change `.gitignore` only if the observed behavior is wrong

### Step 2 — Resolve config drift
- [ ] inspect `config/quant-autoresearch.service`
- [ ] inspect `config/supervisord.conf`
- [ ] decide whether to align or explicitly mark obsolete any file still pointing to `cli.py run` or old env vars

### Step 3 — Run full closeout verification
- [ ] `uv sync --all-extras --dev`
- [ ] `uv run pytest --tb=short -q`
- [ ] `uv run python cli.py --help`
- [ ] `uv run python cli.py setup_data --help`
- [ ] `uv run python cli.py fetch --help`
- [ ] `uv run python cli.py backtest --help`

### Step 4 — Record evidence and commit sprint 3 changes
- [ ] update this sprint doc with command results, blockers, and follow-ups
- [ ] `git add .gitignore config/quant-autoresearch.service config/supervisord.conf docs/feature/v2-phase4/sprint3/sprint3-infra.md docs/feature/v2-phase4/v2-phase4-test-plan.md`
- [ ] `git commit -m "chore(v2-phase4): verify closeout surfaces and final checks"`

## 4) Test Plan

- [ ] ignore rules behave as intended
- [ ] config drift decision is explicit and documented
- [ ] dependency sync, tests, and CLI smoke checks succeed

## 5) Verification Commands

```bash
git check-ignore -v results.tsv run.log
git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"
rg -n "cli.py run|GROQ_API_KEY|MOONSHOT_API_KEY" config
uv sync --all-extras --dev
uv run pytest --tb=short -q
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
