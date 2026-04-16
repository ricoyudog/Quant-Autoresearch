> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Research -- Infra Lane Plan

> Feature branch: `feature/v2-research`
> Role: Infra / Runtime
> Historical workspace: `docs/feature/v2-research/`
> Last updated: 2026-04-08

## Mission

Lock the runtime assumptions that make the backend plan executable: the vault root, env overrides,
optional research API credentials, local data prerequisites for `analyze`, and the smoke commands
needed to prove the feature works outside the unit-test suite.

## Environment Contracts

| Item | Current Value | Why It Matters |
| --- | --- | --- |
| Vault root default | `~/Documents/Obsidian Vault` | planned default location for `quant-autoresearch/` |
| Vault root override | `OBSIDIAN_VAULT_PATH` | required so the feature works on machines that store the vault elsewhere |
| Research API env | `EXA_API_KEY`, `SERPAPI_KEY` | deep web-search mode is optional and must degrade cleanly when keys are absent |
| Academic search dependency | `arxiv` package plus outbound network access | `research` must still support paper lookup even without web-search credentials |
| Analysis data prerequisite | existing local market-data surface from Session 2 / current repo runtime | `analyze` needs a clearly documented local data source before implementation begins |
| Dependency tool | `uv` | standard env sync and command runner for the repo |

## Infra Tasks

| Task ID | Task | Dependency | Acceptance |
| --- | --- | --- | --- |
| INFRA-01 | Validate the vault root, env override behavior, directory permissions, and current local data prerequisite before Sprint 1 starts | Phase 0 complete | commands confirm the expected paths exist or the divergence is documented in the workspace |
| INFRA-02 | Define fallback behavior for missing web-search credentials and record the exact data dependency for `analyze` before Sprint 2 starts | Sprint 1 complete | runtime docs describe what still works without API keys and what local data the analysis flow expects |
| INFRA-03 | Capture smoke evidence for `setup_vault`, `research`, and `analyze` during closeout | Phase 3 | issue or PR links prove the runtime path works beyond unit tests |

## Operational Checks

```bash
# Validate repo environment
uv sync --all-extras --dev

# Validate the vault target
python -c "
from pathlib import Path
import os
root = Path(os.getenv('OBSIDIAN_VAULT_PATH', Path.home() / 'Documents' / 'Obsidian Vault'))
print(root)
print(root.exists())
"

# Validate the Sprint 1 CLI surface
uv run python cli.py setup_vault

# Validate the Sprint 2 CLI surface
uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output stdout
uv run python cli.py analyze SPY --start 2025-01-01 --output stdout
```

## Runtime Notes

- The vault directory tree must be safe to create repeatedly.
- Missing `EXA_API_KEY` or `SERPAPI_KEY` must not make `research --depth shallow` unusable.
- If `analyze` depends on a data path or cache that differs from the original spec draft, the plan
  must be updated before backend implementation begins.
- The checked-out local repo points at a different default remote than the live umbrella issue. Keep
  issue updates targeted at the documented fork unless repository ownership changes.

## Execution Handoff

Use the sprint docs as the execution queue for runtime work:

- [sprint1/sprint1-infra.md](./sprint1/sprint1-infra.md)
- [sprint2/sprint2-infra.md](./sprint2/sprint2-infra.md)

This lane doc is the cross-sprint runtime summary. It does not replace the sprint-level execution
checklists.

## Infra Risks

| Risk | Mitigation |
| --- | --- |
| The default vault path is wrong on the implementation machine | validate and document `OBSIDIAN_VAULT_PATH` before writing code that assumes the default |
| Web-search credentials are absent, expired, or intentionally withheld | make shallow ArXiv-only mode the safe fallback and surface that mode in command output |
| `analyze` assumes a market-data source that is not actually present in the branch | document the dependency in `INFRA-01` / `INFRA-02` and refuse to keep it implicit |
