# Sprint 1 -- Backend Plan

> Feature: `v2-research`
> Role: Backend
> Derived from: #13 (Research capabilities redesign) -- foundation + Playbook removal
> Last Updated: 2026-04-02

## 0) Governing Specs

1. `docs/research-capabilities-v2.md` -- V2 research design (Sections 1, 6, 8)
2. `docs/upgrade-plan-v2.md` -- V2 upgrade plan (Section 6, items 11-13)
3. `docs/feature/v2-research/v2-research-development-plan.md` -- Task table Sprint 1

## 1) Sprint Mission

Build the Obsidian vault integration foundation and remove the SQLite Playbook. This sprint creates the `quant-autoresearch/` vault subdirectory structure, implements vault path configuration, removes the SQLite-based Playbook and its test file, updates research.py to write to Obsidian instead of SQLite, and cleans all Playbook references from surviving files.

## 2) Scope / Out of Scope

**Scope**
- Create `config/vault.py` with path configuration and `ensure_dirs()`
- Create Obsidian vault subdirectories: `quant-autoresearch/{experiments,research,knowledge}/`
- Add `setup_vault` CLI subcommand to `cli.py`
- Remove `src/memory/playbook.py`
- Remove `src/memory/__init__.py` (if empty after playbook removal)
- Delete `tests/unit/test_playbook_memory.py`
- Update `src/core/research.py` to output to Obsidian vault instead of SQLite
- Clean all Playbook imports in surviving files (cli.py, engine.py if exists, conftest.py)
- Write `tests/unit/test_vault_config.py` and `tests/unit/test_vault_writer.py`

**Out of Scope**
- Multi-agent stock analysis CLI (`analyze` command) -- Sprint 2
- Static knowledge base notes creation -- Sprint 2
- `program.md` research guidance section -- Sprint 2
- 4-layer memory documentation -- Sprint 2

## 3) Step-by-Step Plan

### Step 1 -- Create feature branch + baseline
- [ ] `git checkout -b feature/v2-research main` (or from feature/v2-cleanup if dependency)
- [ ] Run `pytest --tb=short -q` and record test count as baseline
- [ ] Record baseline results

### Step 2 -- Create config/vault.py (RES-02)
- [ ] Create `config/` directory if not exists
- [ ] Write `config/vault.py` with:
  - `VAULT_ROOT` = `os.path.expanduser("~/Documents/Obsidian Vault")`
  - `QUANT_DIR` = `f"{VAULT_ROOT}/quant-autoresearch"`
  - `get_vault_paths()` returning dict with keys: root, experiments, research, knowledge, strategies
  - `ensure_dirs()` creating all subdirectories with `os.makedirs(path, exist_ok=True)`
  - `get_vault_path()` reading from env var `OBSIDIAN_VAULT_PATH` if set, else default
- [ ] Verify: `python -c "from config.vault import get_vault_paths, ensure_dirs; print('OK')"`

### Step 3 -- Create setup_vault CLI subcommand (RES-03, RES-14)
- [ ] Add `setup_vault` subcommand to `cli.py`
- [ ] Command should call `ensure_dirs()` and print created directories
- [ ] Verify: `uv run python cli.py setup_vault` creates dirs under vault root
- [ ] Verify: directories exist: `ls ~/Documents/Obsidian\ Vault/quant-autoresearch/`

### Step 4 -- Remove playbook.py (RES-04)
- [ ] `git rm src/memory/playbook.py`
- [ ] Check if `src/memory/` only has `__init__.py`: `ls src/memory/`
- [ ] If only `__init__.py`: `git rm src/memory/__init__.py && rmdir src/memory/`
- [ ] Search for references: `grep -rn "Playbook\|from src.memory.playbook\|from memory.playbook" src/ tests/ cli.py`
- [ ] Clean any imports found in surviving files
- [ ] Verify: `grep -rn "Playbook" src/ cli.py` returns 0 hits (excluding comments)

### Step 5 -- Delete playbook test (RES-07)
- [ ] `git rm tests/unit/test_playbook_memory.py`
- [ ] Verify: `test ! -f tests/unit/test_playbook_memory.py`

### Step 6 -- Clean conftest.py
- [ ] `grep -n "playbook\|Playbook" tests/conftest.py`
- [ ] Remove any Playbook fixtures or imports if present
- [ ] Verify: conftest.py has no Playbook references

### Step 7 -- Update research.py for vault output (RES-06)
- [ ] Add import of `config.vault` to `src/core/research.py`
- [ ] Modify research output functions to write Markdown files to vault `research/` directory
- [ ] Add YAML frontmatter to output (note_type, research_type, query, date, tags)
- [ ] Add dedup: `check_existing_research()` before searching
- [ ] Keep JSON cache mechanism for API responses (research_cache.json, web_research_cache.json)
- [ ] Remove any Playbook-related logic from research.py
- [ ] Verify: `python -c "from src.core.research import *; print('OK')"`

### Step 8 -- Write vault config tests
- [ ] Create `tests/unit/test_vault_config.py`:
  - `test_get_vault_paths_returns_all_keys`
  - `test_ensure_dirs_creates_all_directories` (using tmp_path)
  - `test_ensure_dirs_idempotent`
  - `test_vault_path_env_override` (tests OBSIDIAN_VAULT_PATH env var)
- [ ] Create `tests/unit/test_vault_writer.py`:
  - `test_format_research_report_has_frontmatter`
  - `test_format_research_report_has_header`
  - `test_write_to_vault_creates_file` (using tmp_path)

### Step 9 -- Verify surviving tests pass (RES-08)
- [ ] `pytest --tb=short -v`
- [ ] All tests pass, 0 failures, 0 errors

### Step 10 -- Commit sprint 1 changes
- [ ] `git add -A && git commit -m "feat(v2-research): add Obsidian vault integration, remove SQLite Playbook"`

## 4) Test Plan

- [ ] After Step 2: `python -c "from config.vault import get_vault_paths, ensure_dirs"` succeeds
- [ ] After Step 3: `uv run python cli.py setup_vault` runs without error, dirs created
- [ ] After Step 4: `grep -rn "Playbook" src/ cli.py` returns 0 hits
- [ ] After Step 5: `test ! -f tests/unit/test_playbook_memory.py` succeeds
- [ ] After Step 6: conftest.py has no Playbook references
- [ ] After Step 7: research.py imports cleanly, vault write logic works
- [ ] After Step 8: new vault tests pass
- [ ] After Step 9: full pytest green

## 5) Verification Commands

```bash
# Confirm Playbook removal
test ! -f src/memory/playbook.py && echo "playbook.py GONE"
test ! -f tests/unit/test_playbook_memory.py && echo "test_playbook_memory.py GONE"
test ! -d src/memory && echo "memory/ GONE" || ls src/memory/

# Import cleanliness
grep -rn "from src.memory.playbook\|import.*Playbook\|Playbook(" src/ cli.py || echo "ALL CLEAN"

# Vault config works
python -c "from config.vault import get_vault_paths, ensure_dirs; print('VAULT CONFIG OK')"

# Vault setup command
uv run python cli.py setup_vault

# Research module still imports
python -c "from src.core.research import *; print('RESEARCH OK')"

# Full test run
pytest --tb=short -v
```

## 6) Implementation Update Space

### Completed Work

*(to be filled during implementation)*

### Command Results

*(to be filled during implementation)*

### Blockers / Deviations

*(to be filled during implementation)*

### Follow-ups

- Sprint 2: multi-agent research CLI, knowledge base notes, program.md research guidance
