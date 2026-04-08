# Sprint 1 -- Infra Plan

> Feature: `v2-research`
> Role: Infra
> Derived from: `#13` -- vault path + setup runtime validation
> Last Updated: 2026-04-08

## 0) Governing Specs

1. `docs/research-capabilities-v2.md` -- Sections 1-2 for vault layout and note destinations
2. `docs/upgrade-plan-v2.md` -- V2 decisions 12-13 and 17 for Obsidian integration and CLI
   expectations
3. `docs/feature/v2-research/v2-research-development-plan.md` -- Sprint 1 infra tasks and
   verification expectations
4. `docs/feature/v2-research/v2-research-infra.md` -- cross-sprint runtime contract
5. `docs/feature/v2-research/sprint1/sprint1-backend.md` -- backend deliverables that depend on
   runtime validation

## 1) Sprint Mission

Make Sprint 1 executable on a real machine. This lane validates the vault root, the
`OBSIDIAN_VAULT_PATH` override, directory permissions, baseline environment sync, and the smoke
commands that prove `setup_vault` works outside unit tests.

## 2) Scope / Out of Scope

**Scope**
- Validate the default vault path and the env-override behavior
- Confirm repo environment sync and record any pre-existing runtime drift
- Validate the directories created by `setup_vault`
- Record machine-specific requirements that backend implementation must respect

**Out of Scope**
- Implementing backend code in `config/vault.py` or `cli.py`
- Final API-key fallback behavior for deep research mode
- Final market-data dependency validation for `analyze`, which belongs to Sprint 2 infra

## 3) Step-by-Step Plan

### Step 1 -- Confirm the runtime baseline on the feature branch
- [ ] Confirm `feature/v2-research` is the active branch before runtime validation starts.
- [ ] Run `uv sync --all-extras --dev` and record any dependency or interpreter problems.
- [ ] Note the current repo-remote divergence (`origin` vs the live issue host) in the update space
      if it affects closeout.
- [ ] Capture any environment prerequisites that backend work must not assume implicitly.

### Step 2 -- Validate the vault root and override behavior
- [ ] Check whether the default vault root `~/Documents/Obsidian Vault` exists on the current
      machine.
- [ ] Test the planned `OBSIDIAN_VAULT_PATH` override behavior with a controlled path if the default
      root is absent or unsuitable.
- [ ] Confirm the process can create and write `quant-autoresearch/` under the resolved root.
- [ ] Record the exact operator setup required if the default path is unavailable.

### Step 3 -- Validate `setup_vault` runtime behavior
- [ ] Run `uv run python cli.py setup_vault` once the backend command exists.
- [ ] Confirm the command creates `experiments/`, `research/`, and `knowledge/` under the resolved
      root.
- [ ] Re-run the command to confirm the path creation is idempotent and the operator output stays
      clear.
- [ ] Capture the command output needed for issue or PR evidence.

### Step 4 -- Hand off Sprint 1 runtime findings
- [ ] Record any path, permission, or machine-specific deviations in the update space.
- [ ] Note the unresolved market-data prerequisite that Sprint 2 infra must lock down for
      `analyze`.
- [ ] Link the smoke evidence location back to the umbrella issue or review summary.

## 4) Test Plan

- [ ] `uv sync --all-extras --dev` completes successfully on the implementation machine.
- [ ] The default vault root or the override path is validated explicitly.
- [ ] `setup_vault` creates the planned directories once backend implementation lands.
- [ ] A second `setup_vault` run proves the command is idempotent.
- [ ] The resolved target path and directory results are recorded for closeout evidence.

## 5) Verification Commands

```bash
uv sync --all-extras --dev

python -c "
from pathlib import Path
import os
root = Path(os.getenv('OBSIDIAN_VAULT_PATH', Path.home() / 'Documents' / 'Obsidian Vault'))
print(root)
print(root.exists())
"

uv run python cli.py setup_vault
uv run python cli.py setup_vault
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
