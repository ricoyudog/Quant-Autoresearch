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
- [x] run `git check-ignore -v results.tsv run.log`
- [x] run `git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"`
- [x] keep `.gitignore` unchanged because the observed behavior matches the V2 notes/output split

### Step 2 — Resolve config drift
- [x] inspect `config/quant-autoresearch.service`
- [x] inspect `config/supervisord.conf`
- [x] explicitly mark both files obsolete instead of forcing daemon semantics onto the one-shot V2 `backtest` command

### Step 3 — Run full closeout verification
- [x] `uv sync --all-extras --dev`
- [x] `uv run pytest --tb=short -q`
- [x] `uv run python cli.py --help`
- [x] `uv run python cli.py setup-data --help`
- [x] `uv run python cli.py fetch --help`
- [x] `uv run python cli.py backtest --help`

### Step 4 — Record evidence and commit sprint 3 changes
- [x] update this sprint doc with command results, blockers, and follow-ups
- [x] `git add config/quant-autoresearch.service config/supervisord.conf docs/feature/v2-phase4/README.md docs/feature/v2-phase4/sprint3/sprint3-infra.md docs/feature/v2-phase4/v2-phase4-development-plan.md docs/feature/v2-phase4/v2-phase4-infra.md docs/feature/v2-phase4/v2-phase4-test-plan.md`
- [x] `git commit -m "chore(v2-phase4): verify closeout surfaces and final checks"`

## 4) Test Plan

- [x] ignore rules behave as intended
- [x] config drift decision is explicit and documented
- [x] dependency sync, tests, and CLI smoke checks succeed

## 5) Verification Commands

```bash
git check-ignore -v results.tsv run.log
git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"
! rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md config src/__init__.py
uv sync --all-extras --dev
uv run pytest --tb=short -q
uv run python cli.py --help
uv run python cli.py setup-data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
```

## 6) Implementation Update Space

### Completed Work

- Confirmed the current `.gitignore` behavior already matches the intended V2
  split: output artifacts (`results.tsv`, `run.log`) are ignored while
  markdown notes under `experiments/notes/` stay tracked.
- Reworked `config/quant-autoresearch.service` and `config/supervisord.conf`
  into inert `/bin/true` placeholders so the retired `cli.py run` surface and
  stale `GROQ_API_KEY` injection cannot accidentally run or fail if the old
  templates are started.
- Re-ran the full closeout verification set after the config cleanup.

### Command Results

- `git check-ignore -v results.tsv run.log`
  - `.gitignore:34:*.tsv  results.tsv`
  - `.gitignore:33:*.log  run.log`
- `git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"`
  - `notes markdown is tracked`
- `! rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md config src/__init__.py`
  - exit code `0` with no matches
- `uv sync --all-extras --dev`
  - `Resolved 134 packages in 3ms`
  - `Checked 117 packages in 2ms`
- `uv run pytest --tb=short -q`
  - `97 passed in 1.22s`
- `uv run python cli.py --help`
  - exit code `0`
  - commands shown: `fetch`, `setup-data`, `backtest`
- `uv run python cli.py setup-data --help`
  - exit code `0`
- `uv run python cli.py fetch --help`
  - exit code `0`
  - required argument: `SYMBOL`
  - option shown: `--start` (default `2020-01-01`)
- `uv run python cli.py backtest --help`
  - exit code `0`
  - options shown: `--strategy/-s`, `--symbols/-y`

### Blockers / Deviations

- The two legacy operator config files were marked obsolete instead of being
  re-pointed to `backtest`. V2 does not expose a long-running daemon command, so
  swapping in a one-shot batch command under restart-oriented service managers
  would still be misleading.

### Follow-ups

- None; the Sprint 3 closeout note exists and issue #10 now sits in `workflow::review`.
