# Sprint 1 — Backend Plan

> Feature: `v2-phase3`
> Role: Backend
> Derived from: #9 (CLI simplification + directory structure + gitignore)
> Last Updated: 2026-04-02

## 0) Governing Specs

1. `docs/upgrade-plan-v2.md` — V2 Phase 3 section (lines 616-624: CLI simplification)
2. `docs/upgrade-plan-v2.md` — Section 4 (lines 162-228: Obsidian experiment notes directory)
3. `docs/upgrade-plan-v2.md` — Section 6 (lines 375-392: file changes — cli.py, experiments/notes/)

## 1) Sprint Mission

Simplify `cli.py` from 7 commands to 3 working commands (`setup_data`, `fetch`, `backtest`), create the `experiments/notes/` directory with `.gitkeep`, and update `.gitignore` to properly track experiment runtime outputs (`results.tsv`, `run.log`).

## 2) Scope / Out of Scope

**Scope**
- Remove 5 commands from `cli.py`: `run`, `status`, `report`, `ingest`, `research`
- Add `backtest` command to `cli.py` that invokes `src/core/backtester.py`
- Clean imports in `cli.py` — remove unused imports after command removal
- Create `experiments/notes/.gitkeep` to anchor the Obsidian notes directory
- Update `.gitignore` to add experiment output file patterns

**Out of Scope**
- Root `program.md` creation — Sprint 2
- `tests/unit/test_cli.py` creation — Sprint 2
- `CLAUDE.md` update — Phase 4
- Changes to `src/core/backtester.py` itself — Phase 1 scope

## 3) Step-by-Step Plan

### Step 1 — Create feature branch + baseline
- [ ] `git checkout -b feature/v2-phase3 main`
- [ ] Run `pytest --tb=short -q` and record test count as baseline
- [ ] Run `uv run python cli.py --help` and record current command list

### Step 2 — Remove dead commands from cli.py (CLI-02..06)
- [ ] Remove `run` command function and decorator
- [ ] Remove `status` command function and decorator
- [ ] Remove `report` command function and decorator
- [ ] Remove `ingest` command function and decorator
- [ ] Remove `research` command function and decorator (including the `from core.research` import)

### Step 3 — Clean imports (CLI-08)
- [ ] Review remaining imports — `DataConnector` is still needed for `fetch`
- [ ] Review remaining imports — `prepare_data` is still needed for `setup_data`
- [ ] Remove any imports only used by removed commands
- [ ] Verify: `python -c "import cli; print('IMPORTS OK')"` or `uv run python cli.py --help`

### Step 4 — Add backtest command (CLI-07)
- [ ] Add `backtest` command function with typer decorator
- [ ] Import `src/core/backtester.py` or invoke via subprocess: `uv run python src/core/backtester.py`
- [ ] Handle missing data gracefully (catch errors, show helpful message)
- [ ] Verify: `uv run python cli.py backtest --help` shows command

### Step 5 — Create experiments/notes/ directory (DIR-01)
- [ ] `mkdir -p experiments/notes/`
- [ ] `touch experiments/notes/.gitkeep`
- [ ] Verify: `test -f experiments/notes/.gitkeep && echo "OK"`

### Step 6 — Update .gitignore (GIT-01)
- [ ] Review current `.gitignore` patterns: note existing `*.tsv` and `!results.tsv` entries
- [ ] Decide: use path-specific entries (`experiments/results.tsv`, `experiments/run.log`) or update existing patterns
- [ ] Add entries for experiment output files per upgrade-plan-v2.md
- [ ] Verify: `grep -E "results\.tsv|run\.log" .gitignore`

### Step 7 — Commit sprint 1 changes
- [ ] `git add cli.py experiments/notes/.gitkeep .gitignore`
- [ ] `git commit -m "feat(v2): simplify CLI to setup_data/fetch/backtest, create notes dir, update gitignore"`

## 4) Test Plan

- [ ] After Step 2-3: `uv run python cli.py --help` shows only 3 commands
- [ ] After Step 4: `uv run python cli.py backtest --help` works
- [ ] After Step 5: `test -f experiments/notes/.gitkeep` succeeds
- [ ] After Step 6: `.gitignore` has new entries
- [ ] Full suite: `pytest --tb=short -q` — same count as baseline (no regressions)

## 5) Verification Commands

```bash
# CLI commands
uv run python cli.py --help
uv run python cli.py setup_data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help

# Directory
test -f experiments/notes/.gitkeep && echo "NOTES DIR OK"

# Gitignore
grep -E "results\.tsv|run\.log" .gitignore && echo "GITIGNORE OK"

# No removed command references
grep -n "def run\|def status\|def report\|def ingest\|def research" cli.py || echo "REMOVED COMMANDS GONE"

# Imports clean
grep "^from\|^import" cli.py

# Test suite
pytest --tb=short -q
```

## 6) Implementation Update Space

### Completed Work

_(to be filled during implementation)_

### Command Results

_(to be filled during implementation)_

### Blockers / Deviations

_(to be filled during implementation)_

### Follow-ups

- Sprint 2: create root `program.md`, create `tests/unit/test_cli.py`
