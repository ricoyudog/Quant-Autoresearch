# Sprint 1 — Backend Plan

> Feature: `v2-phase3`
> Role: Backend
> Derived from: #9 (CLI simplification + directory structure + gitignore)
> Last Updated: 2026-04-03

## 0) Governing Specs

1. `docs/upgrade-plan-v2.md` — V2 Phase 3 section (lines 616-624: CLI simplification)
2. `docs/upgrade-plan-v2.md` — Section 4 (lines 162-228: Obsidian experiment notes directory)
3. `docs/upgrade-plan-v2.md` — Section 6 (lines 375-392: file changes — cli.py, experiments/notes/)

## 1) Sprint Mission

Simplify `cli.py` from 7 commands to 3 working commands (`setup-data`, `fetch`, `backtest`), create the `experiments/notes/` directory with `.gitkeep`, and update `.gitignore` to properly track experiment runtime outputs (`results.tsv`, `run.log`).

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
- [x] `git checkout -b feature/v2-phase3 main`
- [x] Run `pytest --tb=short -q` and record test count as baseline
- [x] Run `uv run python cli.py --help` and record current command list

### Step 2 — Remove dead commands from cli.py (CLI-02..06)
- [x] Remove `run` command function and decorator
- [x] Remove `status` command function and decorator
- [x] Remove `report` command function and decorator
- [x] Remove `ingest` command function and decorator
- [x] Remove `research` command function and decorator (including the `from core.research` import)

### Step 3 — Clean imports (CLI-08)
- [x] Review remaining imports — `DataConnector` is still needed for `fetch`
- [x] Review remaining imports — `prepare_data` is still needed for `setup_data`
- [x] Remove any imports only used by removed commands
- [x] Verify: `python -c "import cli; print('IMPORTS OK')"` or `uv run python cli.py --help`

### Step 4 — Add backtest command (CLI-07)
- [x] Add `backtest` command function with typer decorator
- [x] Import `src/core/backtester.py` or invoke via subprocess: `uv run python src/core/backtester.py`
- [x] Handle missing data gracefully (catch errors, show helpful message)
- [x] Verify: `uv run python cli.py backtest --help` shows command

### Step 5 — Create experiments/notes/ directory (DIR-01)
- [x] `mkdir -p experiments/notes/`
- [x] `touch experiments/notes/.gitkeep`
- [x] Verify: `test -f experiments/notes/.gitkeep && echo "OK"`

### Step 6 — Update .gitignore (GIT-01)
- [x] Review current `.gitignore` patterns: note existing global `*.tsv` and `*.log` coverage
- [x] Decide to keep the existing global ignore rules instead of adding redundant path-specific entries
- [x] Confirm experiment output files are still covered by ignore rules
- [x] Verify: `grep -n "^\*\.log$|^\*\.tsv$" .gitignore`

### Step 7 — Commit sprint 1 changes
- [x] `git add cli.py experiments/notes/.gitkeep .gitignore`
- [x] `git commit -m "feat(v2): simplify CLI to setup_data/fetch/backtest, create notes dir, update gitignore"`

## 4) Test Plan

- [x] After Step 2-3: `uv run python cli.py --help` shows only 3 commands
- [x] After Step 4: `uv run python cli.py backtest --help` works
- [x] After Step 5: `test -f experiments/notes/.gitkeep` succeeds
- [x] After Step 6: `.gitignore` keeps experiment outputs ignored via existing `*.log` and `*.tsv` rules
- [x] Full suite: `uv run pytest --tb=short -q` — 97 passed, no regressions on closeout re-check

## 5) Verification Commands

```bash
# CLI commands
uv run python cli.py --help
uv run python cli.py setup-data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help

# Directory
test -f experiments/notes/.gitkeep && echo "NOTES DIR OK"

# Gitignore
grep -n "^\*\.log$|^\*\.tsv$" .gitignore && echo "GITIGNORE OK"

# No removed command references
grep -n "def run\|def status\|def report\|def ingest\|def research" cli.py || echo "REMOVED COMMANDS GONE"

# Imports clean
grep "^from\|^import" cli.py

# Test suite
pytest --tb=short -q
```

## 6) Implementation Update Space

### Completed Work

- Simplified `cli.py` to the three V2 commands: `setup-data`, `fetch`, `backtest`
- Removed legacy `run`, `status`, `report`, `ingest`, and `research` command entry points
- Added `experiments/notes/.gitkeep` to anchor the experiment notes directory
- Kept experiment runtime outputs ignored via the existing global `.gitignore` rules for `*.log` and `*.tsv`
- Closed out in commit `9cfc899`

### Command Results

- `uv run python cli.py --help` shows only `fetch`, `setup-data`, and `backtest`
- `uv run python cli.py backtest --help` renders successfully
- `grep -n "def run\\|def status\\|def report\\|def ingest\\|def research" cli.py || echo "REMOVED COMMANDS GONE"` -> `REMOVED COMMANDS GONE`
- `test -f experiments/notes/.gitkeep && echo "NOTES DIR OK"` -> `NOTES DIR OK`
- `grep -n "^\\*\\.log$\\|^\\*\\.tsv$" .gitignore` -> lines 33-34 contain the active ignore coverage
- `uv run pytest --tb=short -q` -> `97 passed in 0.94s`

### Blockers / Deviations

- Path-specific `experiments/results.tsv` and `experiments/run.log` entries were not added because the existing global `*.tsv` and `*.log` patterns already covered the files.

### Follow-ups

- Sprint 2 is complete; issue is ready for review after doc sync.
