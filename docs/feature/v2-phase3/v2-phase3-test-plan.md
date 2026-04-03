# V2 Phase 3 — Test Plan

> Feature branch: `feature/v2-phase3`
> Umbrella issue: #9

## Objective

Verify that CLI simplification is correct, directory structure is created, experiment outputs remain ignored by `.gitignore`, `program.md` has proper Obsidian instructions, and new CLI tests pass.

## Pre-change Baseline

Before any modification, confirm the current state is green:

```bash
uv sync --all-extras --dev
pytest --tb=short -q
```

Record the test count and result as baseline.

## Test Categories

### 1. CLI Command Tests (new: `tests/unit/test_cli.py`)

| Test | What it verifies |
| --- | --- |
| `test_setup_data_command_exists` | `setup-data` command registered in Typer app |
| `test_fetch_command_exists` | `fetch` command registered, accepts `--symbol` arg |
| `test_backtest_command_exists` | `backtest` command registered in Typer app |
| `test_run_command_removed` | `run` command not in registered commands |
| `test_status_command_removed` | `status` command not in registered commands |
| `test_report_command_removed` | `report` command not in registered commands |
| `test_ingest_command_removed` | `ingest` command not in registered commands |
| `test_research_command_removed` | `research` command not in registered commands |
| `test_backtest_invokes_backtester` | `backtest` command calls backtester module |
| `test_fetch_creates_connector` | `fetch` command instantiates DataConnector |

### 2. Directory Structure Tests (manual / smoke)

| Check | Command |
| --- | --- |
| `experiments/notes/` exists | `test -d experiments/notes/` |
| `.gitkeep` anchors directory | `test -f experiments/notes/.gitkeep` |

### 3. .gitignore Verification (manual / smoke)

| Check | Command |
| --- | --- |
| Global `*.tsv` pattern present | `grep -n "^\*\.tsv$" .gitignore` |
| Global `*.log` pattern present | `grep -n "^\*\.log$" .gitignore` |

### 4. program.md Verification (manual / smoke)

| Check | Command |
| --- | --- |
| File exists at root | `test -f program.md` |
| Contains Obsidian note format | `grep "Obsidian experiment notes" program.md` |
| Contains experiment note template fields | `grep -E "Hypothesis|Changes|Results|Observations|Next Ideas" program.md` |
| Contains experiment loop instructions | `grep "LOOP FOREVER" program.md` |

## Verification Steps

### Step 1: After CLI simplification (Sprint 1)
```bash
# Verify removed commands are gone
uv run python cli.py --help 2>&1 | grep -cE "run|status|report|ingest|research"
# Expected: 0 matches (or only in descriptions, not as commands)

# Verify kept/new commands present
uv run python cli.py --help 2>&1 | grep -E "setup.data|fetch|backtest"

# Smoke test each command
uv run python cli.py setup-data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
```

### Step 2: After directory + gitignore (Sprint 1)
```bash
test -f experiments/notes/.gitkeep && echo "NOTES DIR OK"
grep -n "^\*\.log$|^\*\.tsv$" .gitignore && echo "GITIGNORE OK"
```

### Step 3: After program.md creation (Sprint 2)
```bash
test -f program.md && echo "PROGRAM.MD EXISTS"
grep "Obsidian experiment notes" program.md && echo "OBSIDIAN SECTION OK"
grep "Hypothesis" program.md && echo "NOTE FORMAT OK"
```

### Step 4: Full test run (Sprint 2)
```bash
uv run pytest --tb=short -q
```
All tests must pass, including new `tests/unit/test_cli.py`.

### Step 5: Import cleanliness
```bash
# Verify cli.py doesn't import removed modules
grep -n "from core.engine\|from core.research\|from safety\|from tools\|from models\|from context" cli.py || echo "CLI IMPORTS CLEAN"

# Verify cli.py only imports what it needs
grep "^from\|^import" cli.py
# Expected: typer, sys, pathlib, data.connector, data.preprocessor, core.backtester (for backtest cmd)
```

## Acceptance Criteria

- [x] `tests/unit/test_cli.py` exists with 12 test cases
- [x] All CLI tests pass
- [x] `experiments/notes/.gitkeep` exists
- [x] `.gitignore` keeps experiment output files ignored via `*.log` and `*.tsv`
- [x] `program.md` exists with Obsidian note format section
- [x] `uv run pytest --tb=short -q` passes with 0 failures
- [x] `cli.py --help` shows exactly 3 commands

## Latest Verification Result

- `uv run pytest tests/unit/test_cli.py -q` -> `12 passed in 0.33s`
- `uv run pytest --tb=short -q` -> `96 passed in 1.01s`
- `uv run python cli.py --help` -> commands are `fetch`, `setup-data`, and `backtest`
- `test -f experiments/notes/.gitkeep && echo "NOTES DIR OK"` -> `NOTES DIR OK`
- `grep -n "^\*\.log$|^\*\.tsv$" .gitignore` -> lines 33-34 match
- `grep -n "Obsidian experiment notes\|Hypothesis\|LOOP FOREVER\|results.tsv" program.md` -> required sections present
