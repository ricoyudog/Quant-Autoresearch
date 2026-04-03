# Sprint 2 — Backend Plan

> Feature: `v2-phase3`
> Role: Backend
> Derived from: #9 (program.md update + CLI tests)
> Last Updated: 2026-04-03

## 0) Governing Specs

1. `docs/upgrade-plan-v2.md` — Section 5 (lines 233-371: program.md complete design)
2. `docs/upgrade-plan-v2.md` — Section 4 (lines 162-228: Obsidian experiment note format)
3. `docs/upgrade-plan-v2.md` — Section 8 (lines 547-586: test plan — test_cli.py)

## 1) Sprint Mission

Create the root `program.md` with full V2 research instructions including the Obsidian note format template, and write `tests/unit/test_cli.py` to verify all CLI commands (kept, new, and removed) work correctly.

## 2) Scope / Out of Scope

**Scope**
- Create root `program.md` with complete V2 agent instructions
- Include Section 4 Obsidian experiment note format in program.md
- Include experiment loop, decision rules, constraints, output format
- Create `tests/unit/test_cli.py` with tests for all 3 commands + removal verification
- Verify all tests pass

**Out of Scope**
- `CLAUDE.md` update — Phase 4
- Changes to backtester.py or other source files
- Any changes to the CLI commands themselves (Sprint 1 responsibility)

## 3) Step-by-Step Plan

### Step 1 — Create root program.md (PROG-01)
- [x] Create `program.md` at repository root
- [x] Use `docs/upgrade-plan-v2.md` Section 5 as the source template
- [x] Include all sections:
  - Setup (branch creation, data verification, file initialization)
  - Experimentation (what you CAN and CANNOT do)
  - The goal (maximize SCORE)
  - Output format (SCORE, SORTINO, CALMAR, etc.)
  - Decision rules (KEEP/DISCARD criteria, simplicity criterion)
  - Logging results (results.tsv format)
  - Obsidian experiment notes (note format with Hypothesis/Changes/Results/Per-Symbol/Observations/Next Ideas)
  - The experiment loop (LOOP FOREVER instructions)
- [x] Verify: `grep "Obsidian experiment notes" program.md`
- [x] Verify: `grep "Hypothesis" program.md`
- [x] Verify: `grep "LOOP FOREVER" program.md`

### Step 2 — Create tests/unit/test_cli.py (TEST-01)
- [x] Create `tests/unit/test_cli.py`
- [x] Test cases:
  - `test_setup_data_command_exists` — verify `setup-data` is registered
  - `test_fetch_command_exists` — verify `fetch` is registered with symbol argument
  - `test_backtest_command_exists` — verify `backtest` is registered
  - `test_run_command_removed` — verify `run` is NOT registered
  - `test_status_command_removed` — verify `status` is NOT registered
  - `test_report_command_removed` — verify `report` is NOT registered
  - `test_ingest_command_removed` — verify `ingest` is NOT registered
  - `test_research_command_removed` — verify `research` is NOT registered
  - `test_backtest_invokes_backtester` — mock backtester, verify backtest command calls it
  - `test_fetch_creates_connector` — verify fetch command instantiates DataConnector
  - `test_fetch_with_custom_start_date` — verify fetch forwards explicit start date
  - `test_fetch_handles_failure` — verify fetch reports connector failures cleanly
- [x] Use `typer.testing.CliRunner` for command testing
- [x] Verify: `uv run pytest tests/unit/test_cli.py -q` passes

### Step 3 — Run full test suite (VERIFY-01)
- [x] `uv run pytest --tb=short -q` — all tests pass
- [x] `uv run python cli.py --help` — shows exactly 3 commands
- [x] `uv run python cli.py setup-data --help` — works
- [x] `uv run python cli.py fetch --help` — works
- [x] `uv run python cli.py backtest --help` — works

### Step 4 — Commit sprint 2 changes
- [x] `git add program.md tests/unit/test_cli.py`
- [x] `git commit -m "feat(v2): add program.md with Obsidian notes format, add CLI tests"`

## 4) Test Plan

- [x] After Step 1: `program.md` exists, contains all required sections
- [x] After Step 2: `uv run pytest tests/unit/test_cli.py -q` — all 12 test cases pass
- [x] After Step 3: `uv run pytest --tb=short -q` — full suite green, no regressions

## 5) Verification Commands

```bash
# program.md content checks
test -f program.md && echo "PROGRAM.MD EXISTS"
grep "Obsidian experiment notes" program.md && echo "OBSIDIAN SECTION OK"
grep "Hypothesis" program.md && echo "NOTE FORMAT OK"
grep "LOOP FOREVER" program.md && echo "LOOP SECTION OK"
grep "results.tsv" program.md && echo "RESULTS LOGGING OK"

# CLI tests
pytest tests/unit/test_cli.py -v

# Full suite
pytest --tb=short -v

# CLI smoke test
uv run python cli.py --help
```

## 6) Implementation Update Space

### Completed Work

- Created the root `program.md` with the full V2 execution loop and Obsidian note template
- Added `tests/unit/test_cli.py` with 12 command-registration and behavior tests
- Re-verified the CLI and test suite on 2026-04-03 during closeout sync
- Closed out in commit `fa68734`

### Command Results

- `grep -n "Obsidian experiment notes\\|Hypothesis\\|LOOP FOREVER\\|results.tsv" program.md` -> matched lines 17, 92, 97, 116, 154, 156, 163, 177
- `uv run pytest tests/unit/test_cli.py -q` -> `12 passed in 0.33s`
- `uv run pytest tests/unit/test_cli.py tests/unit/test_data.py tests/unit/test_runner.py tests/unit/test_security.py --tb=short -q` -> `21 passed in 0.81s`
- `uv run pytest --tb=short -q` -> `96 passed in 1.01s`
- `uv run python cli.py --help` -> commands are `fetch`, `setup-data`, and `backtest`

### Blockers / Deviations

- None on closeout re-verification.

### Follow-ups

- All sprints complete — issue ready for review
- Phase 4: update `CLAUDE.md` to reflect V2 architecture
