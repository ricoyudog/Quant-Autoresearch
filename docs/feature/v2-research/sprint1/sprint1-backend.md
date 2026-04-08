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
- [ ] Confirm `feature/v2-research` is the active branch before coding starts.
- [ ] Run `uv sync --all-extras --dev` and record any environment drift before changing code.
- [ ] Run `pytest --tb=short` and record the baseline result in the update space.
- [ ] Re-read `sprint1-infra.md` and note any vault-path constraints that affect the implementation.

### Step 2 -- Add the vault configuration module
- [ ] Create `config/vault.py`.
- [ ] Implement vault-root resolution with `OBSIDIAN_VAULT_PATH` overriding the default
      `~/Documents/Obsidian Vault`.
- [ ] Expose helpers that return the planned `root`, `experiments`, `research`, and `knowledge`
      paths.
- [ ] Implement idempotent directory creation so the CLI can call it safely more than once.
- [ ] Keep path formatting and write logic importable so they can be covered directly in unit tests.

### Step 3 -- Add `setup_vault` to the CLI
- [ ] Add a `setup_vault` command to `cli.py`.
- [ ] Print the resolved vault target and whether each directory was created or already existed.
- [ ] Fail clearly when the root cannot be created or written.
- [ ] Keep the command thin by delegating path and write behavior to helper functions.

### Step 4 -- Remove the Playbook surface cleanly
- [ ] Delete `src/memory/playbook.py`.
- [ ] Remove or simplify `src/memory/__init__.py` so surviving imports stay valid.
- [ ] Delete `tests/unit/test_playbook_memory.py`.
- [ ] Search `src/`, `tests/`, and `cli.py` for `Playbook` imports or references and clean them.
- [ ] Verify no surviving runtime or test surface still depends on the removed module.

### Step 5 -- Refactor `src/core/research.py` for vault-native output
- [ ] Keep the existing search and cache helpers (`search_arxiv`, optional web search, cache load /
      save) reusable.
- [ ] Add Markdown report formatting with YAML frontmatter for research notes.
- [ ] Add a dedup helper that can detect previously written notes before repeating expensive work.
- [ ] Add write helpers that support both vault output and stdout output.
- [ ] Remove any remaining Playbook-era logic or assumptions from the research surface.

### Step 6 -- Add Sprint 1 test coverage and update stale expectations
- [ ] Create `tests/unit/test_vault_config.py` for path resolution, env overrides, and idempotent
      directory creation.
- [ ] Create `tests/unit/test_vault_writer.py` for frontmatter, report formatting, and vault-file
      creation.
- [ ] Update `tests/unit/test_cli.py` so it validates the Sprint 1 CLI surface without hard-coding
      future `research` / `analyze` removal assumptions.
- [ ] Expand `tests/unit/test_research.py` around the new formatting, dedup, and write helpers.

### Step 7 -- Verify Sprint 1 and prepare the handoff
- [ ] Run the targeted Sprint 1 tests after the code changes land.
- [ ] Run a Playbook-import grep scan and save the result in the update space.
- [ ] Run `uv run python cli.py setup_vault` and capture the smoke output.
- [ ] Run `pytest --tb=short -v` before calling Sprint 1 ready.
- [ ] Record any constraints that Sprint 2 backend must inherit from the final Sprint 1 shape.

## 4) Test Plan

- [ ] `tests/unit/test_vault_config.py` covers default path, env override, and idempotent directory
      creation.
- [ ] `tests/unit/test_vault_writer.py` covers frontmatter, markdown structure, and file creation.
- [ ] `tests/unit/test_cli.py` reflects the Sprint 1 command surface instead of stale legacy
      assumptions.
- [ ] `tests/unit/test_research.py` covers vault formatting, dedup, and write behavior.
- [ ] A global grep confirms no surviving `Playbook` imports remain.
- [ ] `uv run python cli.py setup_vault` succeeds and the created paths match the config helper.
- [ ] `pytest --tb=short -v` passes before Sprint 1 is marked complete.

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

- leave blank until implemented

### Command Results

- leave blank until implemented

### Blockers / Deviations

- leave blank until implemented

### Follow-ups

- leave blank until implemented
