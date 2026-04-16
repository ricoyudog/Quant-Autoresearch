> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Sprint 1 -- Backend Plan

> Feature: `v2-research`
> Role: Backend
> Derived from: `#13` -- vault foundation + Playbook removal
> Last Updated: 2026-04-08

## 0) Governing Specs

1. `docs/research-capabilities-v2.md` -- Sections 1-2 for vault layout, research outputs, and note
   structure
2. `docs/upgrade-plan-v2.md` -- V2 decisions 11-13 and 17 for Playbook retirement and CLI scope
3. `docs/feature/v2-research/v2-research-development-plan.md` -- Sprint 1 task table and
   verification expectations
4. `docs/feature/v2-research/v2-research-backend.md` -- cross-sprint backend contract
5. `docs/feature/v2-research/sprint1/sprint1-infra.md` -- runtime prerequisites for vault path and
   `setup_vault` smoke validation

## 1) Sprint Mission

Build the vault foundation for the V2 research workflow and remove the legacy SQLite Playbook
surface. This sprint creates the `quant-autoresearch/` directory contract, adds a testable
`setup_vault` CLI surface, refactors `src/core/research.py` so it can format and write vault-native
notes, and deletes the Playbook module and its dedicated tests without leaving stale imports behind.

## 2) Scope / Out of Scope

**Scope**
- Create `config/vault.py` with path resolution, env override support, and idempotent directory
  creation
- Add `setup_vault` to `cli.py`
- Remove `src/memory/playbook.py`, simplify `src/memory/__init__.py` as needed, and delete
  `tests/unit/test_playbook_memory.py`
- Refactor `src/core/research.py` so it can format Markdown reports, deduplicate existing notes, and
  write to the vault or stdout
- Add Sprint 1 vault and research-writer test coverage

**Out of Scope**
- The `analyze` command and `src/analysis/` helpers
- Knowledge-note creation
- `program.md` research-guidance updates beyond what is required to keep Sprint 1 code coherent
- Final API-fallback and analysis-runtime validation, which belongs to Sprint 2 infra

## 3) Step-by-Step Plan

### Step 1 -- Activate the branch and capture the backend baseline
- [x] Confirm `feature/v2-research` is the active branch before coding starts.
- [x] Run `uv sync --all-extras --dev` and record any environment drift before changing code.
- [x] Run `pytest --tb=short` and record the baseline result in the update space.
- [x] Re-read `sprint1-infra.md` and note any vault-path constraints that affect the implementation.

### Step 2 -- Add the vault configuration module
- [x] Create `config/vault.py`.
- [x] Implement vault-root resolution with `OBSIDIAN_VAULT_PATH` overriding the default
      `~/Documents/Obsidian Vault`.
- [x] Expose helpers that return the planned `root`, `experiments`, `research`, and `knowledge`
      paths.
- [x] Implement idempotent directory creation so the CLI can call it safely more than once.
- [x] Keep path formatting and write logic importable so they can be covered directly in unit tests.

### Step 3 -- Add `setup_vault` to the CLI
- [x] Add a `setup_vault` command to `cli.py`.
- [x] Print the resolved vault target and whether each directory was created or already existed.
- [x] Fail clearly when the root cannot be created or written.
- [x] Keep the command thin by delegating path and write behavior to helper functions.

### Step 4 -- Remove the Playbook surface cleanly
- [x] Delete `src/memory/playbook.py`.
- [x] Remove or simplify `src/memory/__init__.py` so surviving imports stay valid.
- [x] Delete `tests/unit/test_playbook_memory.py`.
- [x] Search `src/`, `tests/`, and `cli.py` for `Playbook` imports or references and clean them.
- [x] Verify no surviving runtime or test surface still depends on the removed module.

### Step 5 -- Refactor `src/core/research.py` for vault-native output
- [x] Keep the existing search and cache helpers (`search_arxiv`, optional web search, cache load /
      save) reusable.
- [x] Add Markdown report formatting with YAML frontmatter for research notes.
- [x] Add a dedup helper that can detect previously written notes before repeating expensive work.
- [x] Add write helpers that support both vault output and stdout output.
- [x] Remove any remaining Playbook-era logic or assumptions from the research surface.

### Step 6 -- Add Sprint 1 test coverage and update stale expectations
- [x] Create `tests/unit/test_vault_config.py` for path resolution, env overrides, and idempotent
      directory creation.
- [x] Create `tests/unit/test_vault_writer.py` for frontmatter, report formatting, and vault-file
      creation.
- [x] Update `tests/unit/test_cli.py` so it validates the Sprint 1 CLI surface without hard-coding
      future `research` / `analyze` removal assumptions.
- [x] Expand `tests/unit/test_research.py` around the new formatting, dedup, and write helpers.

### Step 7 -- Verify Sprint 1 and prepare the handoff
- [x] Run the targeted Sprint 1 tests after the code changes land.
- [x] Run a Playbook-import grep scan and save the result in the update space.
- [x] Run `uv run python cli.py setup_vault` and capture the smoke output.
- [x] Run `pytest --tb=short -v` before calling Sprint 1 ready.
- [x] Record any constraints that Sprint 2 backend must inherit from the final Sprint 1 shape.

## 4) Test Plan

- [x] `tests/unit/test_vault_config.py` covers default path, env override, and idempotent directory
      creation.
- [x] `tests/unit/test_vault_writer.py` covers frontmatter, markdown structure, and file creation.
- [x] `tests/unit/test_cli.py` reflects the Sprint 1 command surface instead of stale legacy
      assumptions.
- [x] `tests/unit/test_research.py` covers vault formatting, dedup, and write behavior.
- [x] A global grep confirms no surviving `Playbook` imports remain.
- [x] `uv run python cli.py setup_vault` succeeds and the created paths match the config helper.
- [x] `pytest --tb=short -v` passes before Sprint 1 is marked complete.

## 5) Verification Commands

```bash
uv sync --all-extras --dev

pytest tests/unit/test_vault_config.py tests/unit/test_vault_writer.py -v
pytest tests/unit/test_cli.py tests/unit/test_research.py -v

grep -rn "from src.memory.playbook\|from memory.playbook\|Playbook" src/ tests/ cli.py || echo "CLEAN"

uv run python cli.py setup_vault

pytest --tb=short -v
```

## 6) Implementation Update Space

### Completed Work

- Captured the clean Sprint 1 baseline on the dedicated `feature/v2-research` worktree after
  fixing a pre-existing logger directory bug that blocked test collection.
- Added `config/vault.py` with `OBSIDIAN_VAULT_PATH` support, path helpers, and idempotent
  directory creation.
- Added the `setup_vault` CLI command with explicit resolved-root and per-directory status output.
- Removed the legacy Playbook module and its dedicated unit test, then verified the repo is free of
  surviving `Playbook` imports.
- Refactored `src/core/research.py` to format vault-native Markdown reports with YAML frontmatter,
  note dedup, vault writes, and stdout rendering helpers.
- Added Sprint 1 unit coverage for vault config, vault writing, CLI registration/behavior, and the
  logger import regression.

### Command Results

- `git branch --show-current` -> `feature/v2-research`
- `uv sync --all-extras --dev` -> succeeded; clean environment created in `.venv`
- `uv run pytest --tb=short` (baseline after logger fix) -> `95 passed`
- `uv run python -m pytest tests/unit/test_vault_config.py tests/unit/test_vault_writer.py tests/unit/test_cli.py tests/unit/test_research.py tests/unit/test_logger_setup.py -q` -> `25 passed`
- `rg -n "from src.memory.playbook|from memory.playbook|Playbook" src tests cli.py -S` -> no matches
- `uv run python cli.py setup_vault` -> created the real vault directories under
  `/Users/chunsingyu/Documents/Obsidian Vault/quant-autoresearch`
- `uv run pytest --tb=short -v` -> `95 passed`

### Blockers / Deviations

- The initial baseline failed because `src/utils/logger.py` created a rotating file handler before
  ensuring `experiments/logs/` existed. The fix is now covered by `tests/unit/test_logger_setup.py`
  and the baseline gate is green again.
- Typer auto-kebab-cased `setup_vault` to `setup-vault`; the CLI command name was explicitly pinned
  back to `setup_vault` so the runtime command matches the issue docs and verification commands.

### Follow-ups

- Sprint 2 should reuse `render_research_report(...)` instead of rebuilding frontmatter, dedup, or
  vault-write logic in the new CLI command.
- Sprint 2 should continue using `config.vault` as the only path-resolution surface; do not inline
  vault paths in `cli.py`, `program.md`, or the future analysis helpers.
