# V2 Phase 3 — Development Plan

> Feature branch: `feature/v2-phase3`
> Umbrella issue: #9
> Canonical root: `docs/feature/v2-phase3/`
> Dependency: Phase 1 (issue #8) must be complete

## Context

With the V1 architecture fully removed (Phase 2 complete), the CLI still carries dead commands (`run`, `status`, `report`, `ingest`, `research`) that either print stubs or import from preserved-but-not-CLI-facing modules. Phase 3 simplifies the CLI to the three commands the V2 architecture actually needs, creates the Obsidian notes directory structure, updates `.gitignore` to track experiment outputs properly, and updates `program.md` with Obsidian note format instructions for the agent.

## Current State (Pre-Phase 3)

### cli.py
| Command | Status | Action |
| --- | --- | --- |
| `run` | Stub ("not available in V2") | REMOVE |
| `status` | Stub ("coming soon") | REMOVE |
| `report` | Stub ("not available in V2") | REMOVE |
| `fetch` | Working — uses DataConnector | KEEP |
| `ingest` | Working — uses DataConnector | REMOVE |
| `setup_data` | Working — uses prepare_all_data | KEEP |
| `research` | Working — imports from core.research | REMOVE |

### .gitignore
Currently ignores `*.tsv` globally but has `!results.tsv` exception. The upgrade plan says to ignore `results.tsv` and `run.log` explicitly in `experiments/`.

### program.md
Root `program.md` does not exist yet. The upgrade plan (Section 5) defines its full content including Obsidian note instructions (Section 4).

### experiments/notes/
Does not exist yet. Needs `experiments/notes/.gitkeep` to anchor the directory.

## Target State (Post-Phase 3)

### CLI Commands
| Command | Purpose |
| --- | --- |
| `setup_data` | Download default market data symbols |
| `fetch SYMBOL` | Fetch specific symbol data |
| `backtest` | Run backtester on active_strategy.py |

### Directory Additions
```
experiments/
├── notes/
│   └── .gitkeep
```

### .gitignore Additions
```
experiments/results.tsv
experiments/run.log
```

### program.md
Root-level `program.md` with full V2 research instructions including Section 4 Obsidian note format.

## Files to Modify

| File | Change | Sprint |
| --- | --- | --- |
| `cli.py` | Remove 5 commands, add `backtest` command | Sprint 1 |
| `experiments/notes/.gitkeep` | Create empty directory anchor | Sprint 1 |
| `.gitignore` | Add `experiments/results.tsv` and `experiments/run.log` | Sprint 1 |
| `program.md` | Create with full V2 instructions including Obsidian notes | Sprint 2 |

## Files to Create

| File | Purpose | Sprint |
| --- | --- | --- |
| `program.md` | Root-level agent instructions | Sprint 2 |
| `tests/unit/test_cli.py` | CLI command tests | Sprint 2 |

## Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 1 | CLI simplification + directory structure + gitignore | 3 commands, notes dir, gitignore updated | pending | proceed to program.md |
| Sprint 2 | program.md + tests | Root program.md, test_cli.py | pending | merge readiness |

## Task Table

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| CLI-01 | Create `feature/v2-phase3` branch | Dev | Phase 1 done | 0.1d | branch exists, tests green on base |
| CLI-02 | Remove `run` command from cli.py | Dev | CLI-01 | 0.05d | command gone, no references |
| CLI-03 | Remove `status` command from cli.py | Dev | CLI-01 | 0.05d | command gone, no references |
| CLI-04 | Remove `report` command from cli.py | Dev | CLI-01 | 0.05d | command gone, no references |
| CLI-05 | Remove `ingest` command from cli.py | Dev | CLI-01 |  | 0.05d | command gone, no references |
| CLI-06 | Remove `research` command from cli.py | Dev | CLI-01 | 0.05d | command gone, no references |
| CLI-07 | Add `backtest` command to cli.py | Dev | CLI-02..06 | 0.1d | command invokes backtester.py |
| CLI-08 | Clean imports — remove unused DataConnector imports if only used by removed commands | Dev | CLI-07 | 0.05d | no dead imports |
| DIR-01 | Create `experiments/notes/.gitkeep` | Dev | CLI-01 | 0.02d | directory exists |
| GIT-01 | Update `.gitignore` with `results.tsv` and `run.log` entries | Dev | CLI-01 | 0.02d | entries added |
| PROG-01 | Create root `program.md` with full V2 instructions | Dev | CLI-07 | 0.2d | file exists, Section 4 has Obsidian format |
| TEST-01 | Create `tests/unit/test_cli.py` with command tests | Dev | CLI-07 | 0.2d | tests pass |
| VERIFY-01 | Run full test suite and CLI smoke test | Dev | PROG-01, TEST-01 | 0.1d | all green |

## Acceptance Criteria

- [ ] `feature/v2-phase3` branch exists
- [ ] `cli.py` has exactly 3 commands: `setup_data`, `fetch`, `backtest`
- [ ] `run`, `status`, `report`, `ingest`, `research` commands are gone
- [ ] `backtest` command invokes `src/core/backtester.py`
- [ ] `experiments/notes/.gitkeep` exists
- [ ] `.gitignore` includes entries for experiment output files
- [ ] Root `program.md` exists with Obsidian note format (Section 4)
- [ ] `tests/unit/test_cli.py` exists and passes
- [ ] `pytest` passes with 0 failures
- [ ] `uv run python cli.py --help` shows only the 3 commands

## Verification Commands

```bash
# Verify CLI has only 3 commands
uv run python cli.py --help 2>&1 | grep -E "setup_data|fetch|backtest"
uv run python cli.py --help 2>&1 | grep -E "run|status|report|ingest|research" || echo "REMOVED COMMANDS GONE"

# Verify backtest command works (should fail gracefully without data)
uv run python cli.py backtest 2>&1 || true

# Verify directory exists
test -f experiments/notes/.gitkeep && echo "NOTES DIR OK"

# Verify gitignore
grep "results.tsv\|run.log" .gitignore && echo "GITIGNORE OK"

# Verify program.md exists
test -f program.md && echo "PROGRAM.MD OK"

# Verify tests
pytest tests/unit/test_cli.py -v
```

## Risks

| Risk | Mitigation |
| --- | --- |
| `backtest` command needs to handle missing data gracefully | CLI-07 should catch ImportError / FileNotFoundError |
| `program.md` content overlaps with upgrade-plan-v2.md Section 5 | Use upgrade-plan-v2.md Section 5 as the source template |
| `.gitignore` change may conflict with existing `*.tsv` pattern | Review existing patterns before adding; use path-specific entries |
| `research` command removal removes last CLI import of core.research | core.research is preserved for skill use, just not exposed via CLI |
