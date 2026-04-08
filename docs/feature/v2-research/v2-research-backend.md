# V2 Research -- Backend Lane Plan

> Feature branch: `feature/v2-research`
> Role: Backend
> Canonical workspace: `docs/feature/v2-research/`
> Last updated: 2026-04-08

## Mission

Implement the code-surface changes that move the project from the legacy Playbook-backed research
surface to a vault-native research workspace. This lane owns vault configuration, Playbook removal,
research and analysis CLI behavior, knowledge-note generation, and the program-level documentation
that tells the agent how to use those artifacts.

## Code Surface

| Surface | Sprint | Contract |
| --- | --- | --- |
| `config/vault.py` | Sprint 1 | resolve the vault root, support `OBSIDIAN_VAULT_PATH`, and create the required subdirectories idempotently |
| `src/core/research.py` | Sprint 1 | keep cache and search helpers, but output Markdown reports that can be written to the vault |
| `cli.py` | Sprint 1 + Sprint 2 | expose `setup_vault`, `research`, and `analyze` as the operator-facing research surface |
| `src/memory/playbook.py` | Sprint 1 | remove it cleanly, including exports and stale imports |
| `src/analysis/*.py` | Sprint 2 | provide deterministic technical, regime, and market-context helpers for analysis reports |
| `program.md` | Sprint 2 | document research-capability usage and 4-layer memory access patterns after implementation settles |

## Cross-Sprint Contract Decisions

- Vault writes are part of the feature definition of done, not an optional side effect.
- The default vault root is local-machine specific, so backend code must rely on the config helper
  instead of inlining paths.
- `research` reuses the existing ArXiv and optional web-search helpers; missing web-search
  credentials must degrade gracefully instead of failing the whole command.
- `analyze` is a TradingAgents-style, multi-perspective report surface built from deterministic
  computations, not a true multi-LLM debate runtime.
- Playbook removal includes source deletion, test deletion, and import cleanup across surviving
  files.

## Backend Deliverables

| Task ID | Deliverable | Sprint | Dependency | Acceptance |
| --- | --- | --- | --- | --- |
| VAULT-02 | Add `config/vault.py` | Sprint 1 | INFRA-01, VAULT-01 | helper module imports cleanly and creates the planned directory tree |
| VAULT-03 | Add `setup_vault` command | Sprint 1 | VAULT-02 | CLI output is clear and directory creation is idempotent |
| CLEAN-01 | Remove Playbook files and stale imports | Sprint 1 | VAULT-01 | no surviving file imports `Playbook` |
| RES-01 | Refactor `src/core/research.py` to output vault-native notes | Sprint 1 | VAULT-02, VAULT-03, CLEAN-01 | reports include frontmatter, dedup, and preserved cache reuse |
| ANA-01 | Add `src/analysis/` helpers | Sprint 2 | Sprint 1 complete | helper modules produce stable structured outputs |
| CLI-01 | Add `research` CLI behavior | Sprint 2 | RES-01, INFRA-02 | command supports depth + output controls and uses the vault writer |
| CLI-02 | Add `analyze` CLI behavior | Sprint 2 | ANA-01, INFRA-02 | command emits structured analysis without LLM orchestration |
| KB-01 | Add knowledge notes and `program.md` memory guidance | Sprint 2 | CLI-01, CLI-02 | the vault notes exist and `program.md` matches the final workflow |

## Execution Handoff

Use the sprint docs as the execution queue:

- [sprint1/sprint1-backend.md](./sprint1/sprint1-backend.md)
- [sprint2/sprint2-backend.md](./sprint2/sprint2-backend.md)

This lane doc is the cross-sprint contract summary. It does not replace the sprint-level step-by-
step plans.

## Backend Acceptance

- [x] Vault config is centralized in `config/vault.py`
- [x] Playbook files and imports are fully removed
- [x] `research` writes vault-native Markdown notes with stable metadata
- [x] `analyze` produces deterministic structured reports from the new helper modules
- [x] `program.md` describes the implemented research and memory workflow accurately

## Backend Risks

| Risk | Mitigation |
| --- | --- |
| Vault-write helpers get embedded directly in CLI handlers and become hard to test | keep formatting and write logic factored into importable helpers |
| Playbook deletion leaves stale imports in surviving modules or tests | treat the global grep and targeted test updates as hard Sprint 1 gates |
| `analyze` grows into an implicit agent runtime instead of a bounded report command | keep scope explicit in the task table and reject hidden orchestration requirements until a later spec exists |
