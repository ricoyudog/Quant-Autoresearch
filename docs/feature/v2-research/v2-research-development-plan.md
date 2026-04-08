# V2 Research -- Development Plan

> Feature branch: `feature/v2-research`
> Umbrella issue: #13
> Canonical root: `docs/feature/v2-research/`
> Last updated: 2026-04-08
> Planning status: Phase 0 complete; execution ready to start on the feature branch

## 1. Context

The V2 architecture already moved the autonomous experiment loop out of the old Python OPENDEV
controller and into `program.md`. Issue #13 now owns the research capabilities around that loop:

- remove the SQLite Playbook and replace it with vault-native notes plus `results.tsv`
- formalize Obsidian vault configuration and directory creation
- expose research and analysis flows through the CLI
- add the static knowledge notes and memory guidance that the agent can consume during research

The governing designs for this work already exist in `docs/research-capabilities-v2.md` and
`docs/upgrade-plan-v2.md`. On 2026-04-08, the upstream V2 dependency issues `#8`, `#9`, `#11`, and
`#12` were confirmed closed on the live umbrella repo, so the remaining blocker for implementation
is feature-branch setup plus baseline capture.

## 2. Root And Branch Decision

- Active docs root: `docs/`
- Canonical workspace: `docs/feature/v2-research/`
- Canonical branch: `feature/v2-research`

Repo drift note: the generic planning skill expects `docs/beta/` and `docs/dev/` roots, but the
current repository snapshot does not contain those trees. Planning granularity therefore follows the
live V2 workspace precedents under `docs/feature/` plus the governing specs in
`docs/research-capabilities-v2.md` and `docs/upgrade-plan-v2.md`.

`docs/feature/v2-research/` is the right root instead of `docs/issue/13/` because this work is a
persistent feature-scoped V2 session, not a one-off issue-local hotfix. The branch name keeps the
repo's current V2 naming convention.

## 3. Scope

- Add `config/vault.py` and a stable vault-directory contract for
  `quant-autoresearch/{experiments,research,knowledge}/`
- Add a `setup_vault` CLI command and refactor the research surface to write Markdown reports to the
  vault
- Remove `src/memory/playbook.py`, its exports, and its dedicated unit tests
- Add `src/analysis/` helpers for momentum, volatility, regime, and market-context analysis
- Add `research` and `analyze` CLI flows aligned with the V2 research spec
- Add the static knowledge notes plus `program.md` memory / research guidance
- Add unit and integration coverage for the new vault, CLI, and analysis surfaces

## 4. Out Of Scope

- Reworking the backtester foundation, strategy interface, or `program.md` loop semantics from `#8`
- Reopening the CLI simplification and experiment-note integration work from `#9`
- Re-scoping the data-pipeline architecture from `#11`
- Re-implementing the overfit-defense session itself from `#12`
- Building a true multi-LLM orchestration runtime; the planned stock-analysis flow is
  TradingAgents-style in structure, but remains a deterministic CLI surface unless later specs say
  otherwise

## 5. Lane Ownership

| Lane | Responsibility | Primary Docs | Runtime Surface |
| --- | --- | --- | --- |
| Planning | Keep the umbrella issue and workspace aligned | this plan, README | issue #13, docs workspace |
| Backend | Deliver vault config, Playbook removal, research / analyze CLI, and knowledge / memory hooks | `v2-research-backend.md`, sprint backend docs | `config/`, `src/core/`, `src/analysis/`, `cli.py`, `program.md` |
| Infra | Validate vault path, env overrides, API fallbacks, data prerequisites, and smoke commands | `v2-research-infra.md` | local vault, env vars, CLI runtime |
| QA | Define baseline, unit, integration, and merge gates | `v2-research-test-plan.md` | `tests/`, CLI smoke runs, final issue evidence |

## 6. Delivery Surface

### Files To Create

| File | Lane | Purpose |
| --- | --- | --- |
| `config/vault.py` | Backend | vault-path resolution, env override, and directory bootstrap helpers |
| `src/analysis/__init__.py` | Backend | public exports for the analysis helpers |
| `src/analysis/technical.py` | Backend | momentum, volatility, volume, and key-level helpers |
| `src/analysis/regime.py` | Backend | market-regime classification helpers |
| `src/analysis/market_context.py` | Backend | SPY correlation and moving-average context helpers |
| `tests/unit/test_vault_config.py` | QA | unit coverage for vault-path and directory helpers |
| `tests/unit/test_vault_writer.py` | QA | unit coverage for report formatting and vault writes |
| `tests/unit/test_technical.py` | QA | unit coverage for technical-analysis helpers |
| `tests/unit/test_regime.py` | QA | unit coverage for regime classification |
| `tests/unit/test_market_context.py` | QA | unit coverage for market-context helpers |
| `tests/unit/test_cli_research.py` | QA | CLI-level coverage for the `research` command |
| `tests/unit/test_cli_analyze.py` | QA | CLI-level coverage for the `analyze` command |
| `tests/unit/test_cli_setup_vault.py` | QA | CLI-level coverage for the `setup_vault` command |
| `tests/integration/test_research_pipeline.py` | QA | end-to-end vault-write coverage for research flow |
| `tests/integration/test_analyze_pipeline.py` | QA | end-to-end vault-write coverage for analysis flow |

### Files To Modify

| File | Lane | Change |
| --- | --- | --- |
| `cli.py` | Backend | add `setup_vault`, `research`, and `analyze` commands; retire legacy "research removed" expectations |
| `src/core/research.py` | Backend | keep cache and search helpers, add vault-output formatting, dedup, and report writing |
| `program.md` | Backend | add research-capability guidance and memory-access patterns once behavior is implemented |
| `tests/unit/test_cli.py` | QA | replace "command removed" assertions with the new command contract |
| `tests/unit/test_research.py` | QA | expand around vault-writing helpers and dedup behavior |
| `tests/conftest.py` | QA | add vault tmp-path fixtures and any analysis-input fixtures |
| `CLAUDE.md` | Planning | update repo-runtime notes if implementation meaningfully changes the documented operator flow |

### Files To Remove

| File | Lane | Reason |
| --- | --- | --- |
| `src/memory/playbook.py` | Backend | replaced by vault-native notes and persistent markdown artifacts |
| `src/memory/__init__.py` | Backend | remove or simplify exports after Playbook retirement |
| `tests/unit/test_playbook_memory.py` | QA | dedicated Playbook coverage is invalid once the module is removed |

## 7. Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Phase 0 -- Spec Alignment + Baseline | Confirm docs root, branch convention, dependency state, and umbrella references | refreshed workspace index, lane docs, test plan, rewritten issue card | completed | create or switch to `feature/v2-research` and capture the baseline |
| Sprint 1 -- Vault Foundation + Playbook Removal | Add vault config, setup CLI support, and remove the legacy Playbook surface | `config/vault.py`, updated `cli.py`, updated `src/core/research.py`, deleted Playbook files, vault tests | pending | start once the branch baseline is recorded |
| Sprint 2 -- Research CLI + Analysis + Knowledge | Add research / analyze CLI flows, analysis helpers, knowledge notes, and memory guidance | `src/analysis/`, CLI commands, knowledge notes, `program.md` updates, new unit + integration coverage | pending | start after Sprint 1 verification |
| Phase 3 -- Verification + Closeout | Run the full gate and prepare review evidence | green dependency sync, green tests, CLI smoke results, issue or PR evidence update | pending | execute after Sprint 2 implementation finishes |

## 8. Task Tables

### Phase 0 -- Planning And Spec Alignment

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| PLAN-01 | Confirm the live docs root and keep `docs/feature/v2-research/` as the single canonical workspace | Planning | none | 0.1d | completed | no new planning root is introduced under `docs/issue/13/` or legacy paths |
| PLAN-02 | Preserve the repo's V2 branch convention and record the closed dependency set on issues `#8`, `#9`, `#11`, and `#12` | Planning | PLAN-01 | 0.05d | completed | branch name and dependency status appear in the README, plan, and issue |
| PLAN-03 | Expand the workspace with backend, infra, and QA planning surfaces | Planning | PLAN-01 | 0.1d | completed | lane docs and refreshed test plan are linked from the workspace index |
| PLAN-04 | Rewrite issue `#13` as the umbrella index card | Planning | PLAN-02, PLAN-03 | 0.1d | completed | issue contains the required sections, a phase table with status, and workspace references |

### Sprint 1 -- Vault Foundation + Playbook Removal

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| INFRA-01 | Validate vault root, env override, directory permissions, and the current market-data prerequisite for `analyze` | Infra | Phase 0 complete | 0.1d | completed | commands confirm the vault root is writable and the chosen data source is present or explicitly documented |
| VAULT-01 | Create or switch to `feature/v2-research` and capture the pre-change baseline | Backend | Phase 0 complete | 0.1d | completed | branch is active and baseline `uv sync --all-extras --dev` plus `pytest --tb=short` evidence is recorded |
| VAULT-02 | Add `config/vault.py` with path resolution, env override, and idempotent directory creation | Backend | VAULT-01, INFRA-01 | 0.3d | completed | helper module imports cleanly and creates the planned directory tree |
| VAULT-03 | Add `setup_vault` to `cli.py` and expose clear operator output | Backend | VAULT-02 | 0.2d | completed | `uv run python cli.py setup_vault` creates the directories and reports the target paths |
| CLEAN-01 | Remove Playbook source files and their dedicated tests, then clean surviving imports | Backend + QA | VAULT-01 | 0.2d | completed | no surviving file imports `Playbook` and the removed test/module paths are gone |
| RES-01 | Refactor `src/core/research.py` to write vault-native research notes while preserving cache reuse and optional web search | Backend | VAULT-02, VAULT-03, CLEAN-01 | 0.5d | completed | research reports render with frontmatter, dedup works, and vault writes succeed |
| QA-01 | Add vault-config / vault-writer coverage and replace stale CLI expectations that still assert `research` is removed | QA | VAULT-02, VAULT-03, RES-01 | 0.3d | completed | new vault tests pass and `tests/unit/test_cli.py` matches the intended CLI surface |

### Sprint 2 -- Research CLI + Analysis + Knowledge

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| INFRA-02 | Define fallback behavior for missing `EXA_API_KEY` / `SERPAPI_KEY` and document the `analyze` data prerequisite | Infra | Sprint 1 complete | 0.1d | completed | runtime docs explain what still works without API keys and what local data the analysis flow needs |
| ANA-01 | Create the `src/analysis/` helpers for technical, regime, and market-context calculations | Backend | Sprint 1 complete | 0.5d | completed | helper modules import cleanly and return stable structured outputs |
| CLI-01 | Add the `research` command to `cli.py` with depth and output controls | Backend | RES-01, INFRA-02 | 0.3d | completed | `cli.py research "<query>"` supports stdout or vault output and uses the refactored research writer |
| CLI-02 | Add the `analyze` command to `cli.py` using the new analysis helpers | Backend | ANA-01, INFRA-02 | 0.4d | completed | `cli.py analyze <ticker>` produces a structured report without requiring an LLM runtime |
| KB-01 | Create the four knowledge notes and add `program.md` guidance for research and 4-layer memory access | Backend | CLI-01, CLI-02 | 0.3d | completed | vault knowledge notes exist and `program.md` documents how the agent should use them |
| QA-02 | Add analysis-helper, CLI, and integration coverage for research and analyze flows | QA | ANA-01, CLI-01, CLI-02, KB-01 | 0.5d | completed | targeted suites pass and the new integration tests prove vault writes and report shapes |

### Phase 3 -- Verification + Closeout

| Task ID | Task | Lane | Dependency | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| VER-01 | Run dependency sync, targeted suites, and the full `pytest` gate | QA | Sprint 2 complete | 0.2d | completed | `uv sync --all-extras --dev` and `pytest --tb=short -v` pass without unresolved failures |
| VER-02 | Run CLI smoke tests for `setup_vault`, `research`, and `analyze` | Infra | VER-01 | 0.2d | completed | smoke commands succeed and their outputs are captured as review evidence |
| VER-03 | Update the umbrella issue or PR with evidence, remaining risks, and review notes | Planning | VER-01, VER-02 | 0.1d | completed | review-ready summary links to docs, commands, and residual risks |

## 9. Execution Handoff

This document is the planning-layer summary. Execution must move through the sprint docs instead of
turning the umbrella issue into the task queue:

- `sprint1/sprint1-backend.md` for vault config, Playbook removal, and research-output migration
- `sprint1/sprint1-infra.md` for vault path validation, env override checks, and `setup_vault`
  smoke evidence
- `sprint2/sprint2-backend.md` for `research`, `analyze`, knowledge-note creation, and memory docs
- `sprint2/sprint2-infra.md` for API fallback rules, analysis data prerequisites, and final smoke
  evidence

The backend and infra lane docs define cross-sprint contracts. The test plan defines the evidence
expected before a sprint can be considered complete.

## 10. Acceptance Criteria

- [x] The live docs root is confirmed as `docs/` and reused consistently
- [x] The canonical workspace choice is explicit: `docs/feature/v2-research/`
- [x] The feature branch is explicitly named as `feature/v2-research`
- [x] The workspace has a local index, a main development plan, backend lane doc, infra lane doc,
      and a refreshed test plan
- [x] Issue `#13` is defined as the umbrella index rather than the execution queue
- [x] `config/vault.py` exists and `setup_vault` creates the planned directory tree
- [x] `src/memory/playbook.py` and `tests/unit/test_playbook_memory.py` are removed with no stale
      imports
- [x] `src/core/research.py` writes vault-native research notes with frontmatter and dedup behavior
- [x] `research` and `analyze` CLI commands exist and work as documented
- [x] The four knowledge notes exist and `program.md` documents the research / memory workflow
- [x] Unit, integration, and full regression gates pass with recorded evidence

## 11. Verification And Evidence Expectations

The detailed gate list lives in `v2-research-test-plan.md`. The minimum verification families are:

```bash
# Baseline / dependency sync
uv sync --all-extras --dev
pytest --tb=short

# Vault surface
uv run python cli.py setup_vault
python -c "
from config.vault import get_vault_paths
print(get_vault_paths())
"

# Playbook cleanup
test ! -f src/memory/playbook.py
test ! -f tests/unit/test_playbook_memory.py
grep -rn "from src.memory.playbook\|from memory.playbook\|Playbook" src/ tests/ cli.py || echo "CLEAN"

# Feature-specific tests
pytest tests/unit/test_vault_config.py tests/unit/test_vault_writer.py -v
pytest tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py -v
pytest tests/unit/test_cli_research.py tests/unit/test_cli_analyze.py tests/unit/test_cli_setup_vault.py -v
pytest tests/integration/test_research_pipeline.py tests/integration/test_analyze_pipeline.py -v

# CLI smoke
uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output stdout
uv run python cli.py analyze SPY --start 2025-01-01 --output stdout
```

## 12. Dependencies / Risks

| Risk | Mitigation |
| --- | --- |
| The checked-out repo remote and the live umbrella issue repo are different | Keep issue updates pointed at `ricoyudog/Quant-Autoresearch#13` unless repo governance changes |
| The local vault path is absent or differs from the default | make `OBSIDIAN_VAULT_PATH` the documented override and validate path permissions in `INFRA-01` |
| Deep web research requires credentials that may be missing on some machines | document graceful fallback to ArXiv-only mode and make the fallback visible in CLI output |
| The analysis CLI may depend on data-surface assumptions that differ from the final Session 2 runtime | capture the actual dependency in `INFRA-01` / `INFRA-02` before implementation proceeds |
| Old CLI tests still assert that `research` is intentionally removed | treat `tests/unit/test_cli.py` as a planned update, not as a fixed legacy contract |
