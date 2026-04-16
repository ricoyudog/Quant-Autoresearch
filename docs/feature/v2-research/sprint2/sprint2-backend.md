> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Sprint 2 -- Backend Plan

> Feature: `v2-research`
> Role: Backend
> Derived from: `#13` -- research CLI + analysis + knowledge + memory guidance
> Last Updated: 2026-04-08

## 0) Governing Specs

1. `docs/research-capabilities-v2.md` -- Sections 2-5 and 7 for research CLI, analysis reporting,
   knowledge notes, and memory layers
2. `docs/upgrade-plan-v2.md` -- V2 CLI decisions and research-capability scope
3. `docs/feature/v2-research/v2-research-development-plan.md` -- Sprint 2 task table and
   verification expectations
4. `docs/feature/v2-research/v2-research-backend.md` -- cross-sprint backend contract
5. `docs/feature/v2-research/sprint2/sprint2-infra.md` -- runtime assumptions for API fallback and
   `analyze` data prerequisites

## 1) Sprint Mission

Build the operator-facing research surface on top of the Sprint 1 vault foundation. This sprint
adds deterministic analysis helpers under `src/analysis/`, exposes the `research` and `analyze`
commands in `cli.py`, writes the static knowledge notes, and updates `program.md` so the agent can
consume the resulting research and memory artifacts consistently.

## 2) Scope / Out of Scope

**Scope**
- Create `src/analysis/__init__.py`, `technical.py`, `regime.py`, and `market_context.py`
- Add the `research` CLI command with depth and output controls
- Add the `analyze` CLI command with deterministic report generation
- Write the four static knowledge notes
- Update `program.md` with research-capabilities and memory-access guidance
- Add unit, CLI, and integration coverage for the new surfaces

**Out of Scope**
- Re-implementing Sprint 1 vault and Playbook-removal work
- Building a true multi-LLM orchestration runtime
- Vector search, automatic ingestion, or autonomous note curation beyond the scoped knowledge notes

## 3) Step-by-Step Plan

### Step 1 -- Confirm Sprint 2 prerequisites
- [x] Confirm Sprint 1 backend and infra outcomes are recorded before starting Sprint 2 work.
- [x] Re-read `sprint2-infra.md` so API-key fallback and local data assumptions stay aligned.
- [x] Verify the Sprint 1 vault writer and `setup_vault` surface still behave as expected.
- [x] Record any inherited constraints that shape CLI arguments or output formats.

### Step 2 -- Build the deterministic analysis helpers
- [x] Create `src/analysis/__init__.py`.
- [x] Implement `src/analysis/technical.py` with momentum, volatility, volume, and key-level
      helpers.
- [x] Implement `src/analysis/regime.py` with bull / bear and quiet / volatile classification
      outputs.
- [x] Implement `src/analysis/market_context.py` with SPY-correlation and moving-average context
      helpers.
- [x] Keep helper outputs structured and deterministic so the CLI and tests can consume them
      directly.

### Step 3 -- Finalize the `research` CLI surface
- [x] Add `research` to `cli.py` with `query`, `--depth`, and `--output` controls.
- [x] Reuse the Sprint 1 research helpers for formatting, dedup, and vault writes.
- [x] Make shallow ArXiv-only behavior work even when deep web-search credentials are absent.
- [x] Make operator-visible output clear when the command reuses an existing research note or
      skips deep web search due to missing credentials.

### Step 4 -- Implement the `analyze` CLI surface
- [x] Add `analyze` to `cli.py` with ticker, date-range, and output controls.
- [x] Load the local market-data surface validated in `sprint2-infra.md` instead of preserving a
      stale path assumption in code.
- [x] Fail clearly when the local runtime data prerequisite is unavailable.
- [x] Compose report sections for momentum, volatility, regime, price structure, and market context.
- [x] Support both stdout output and vault-note output.

### Step 5 -- Add knowledge notes and `program.md` guidance
- [x] Write the four knowledge notes with YAML frontmatter into the vault `knowledge/` surface.
- [x] Add a `Research Capabilities` section to `program.md` that explains when and how to use the
      CLI tools and knowledge notes.
- [x] Add a `Memory Access Patterns` section to `program.md` that matches the implemented vault and
      `results.tsv` workflow.
- [x] Keep note topics and terminology aligned with `docs/research-capabilities-v2.md`.

### Step 6 -- Add Sprint 2 test coverage
- [x] Create `tests/unit/test_technical.py`, `tests/unit/test_regime.py`, and
      `tests/unit/test_market_context.py`.
- [x] Create `tests/unit/test_cli_research.py`, `tests/unit/test_cli_analyze.py`, and
      `tests/unit/test_cli_setup_vault.py`.
- [x] Update `tests/unit/test_cli.py` so registration assertions match the new command surface.
- [x] Add `tests/integration/test_research_pipeline.py` and
      `tests/integration/test_analyze_pipeline.py`.

### Step 7 -- Verify Sprint 2 and prepare closeout evidence
- [x] Run the targeted helper, CLI, and integration tests after implementation lands.
- [x] Run `uv run python cli.py research ...` in shallow mode and capture the output.
- [x] Run `uv run python cli.py analyze ...` and capture the output or the clear failure mode if
      infra prerequisites are still blocking.
- [x] Run `pytest --tb=short -v` before calling Sprint 2 complete.
- [x] Record any follow-up work that should stay out of the current sprint scope.

## 4) Test Plan

- [x] `tests/unit/test_technical.py`, `tests/unit/test_regime.py`, and
      `tests/unit/test_market_context.py` cover the deterministic analysis helpers.
- [x] `tests/unit/test_cli_research.py`, `tests/unit/test_cli_analyze.py`, and
      `tests/unit/test_cli_setup_vault.py` cover the new CLI surface.
- [x] `tests/unit/test_cli.py` reflects the registered command surface after Sprint 2 lands.
- [x] `tests/integration/test_research_pipeline.py` and `tests/integration/test_analyze_pipeline.py`
      prove vault writes and report structure.
- [x] `program.md` includes the final `Research Capabilities` and `Memory Access Patterns` sections.
- [x] `pytest --tb=short -v` passes before the sprint is called complete.

## 5) Verification Commands

```bash
pytest tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py -v
pytest tests/unit/test_cli_research.py tests/unit/test_cli_analyze.py tests/unit/test_cli_setup_vault.py -v
pytest tests/integration/test_research_pipeline.py tests/integration/test_analyze_pipeline.py -v

uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output stdout
uv run python cli.py analyze SPY --start 2025-01-01 --output stdout

grep -n "Research Capabilities" program.md
grep -n "Memory Access Patterns" program.md

pytest --tb=short -v
```

## 6) Implementation Update Space

### Completed Work

- Re-confirmed Sprint 1 backend and infra checklists are fully complete before resuming Sprint 2.
- Re-read `sprint2-infra.md` and captured the active runtime constraints in Ralph planning
  artifacts under `.omx/plans/`.
- Re-verified `uv run python cli.py setup_vault` on the dedicated `feature/v2-research` worktree;
  all vault directories already existed and the command remained idempotent.
- Re-ran the Sprint 1 targeted verification bundle, fixed one stale `tests/unit/test_cli.py`
  command-registration assertion, and restored the suite to green.
- Confirmed the already-present Sprint 2 helper modules in `src/analysis/` satisfy the deterministic
  contract and are covered by the new helper tests.
- Verified the `research` and `analyze` CLI surfaces, their dedicated unit tests, and integration
  coverage already present in the worktree.
- Captured shallow and deep `research` smoke evidence; deep mode now reports a clear fallback when
  `EXA_API_KEY` / `SERPAPI_KEY` are absent.
- Confirmed all four knowledge notes exist in the vault and that `program.md` contains the required
  `Research Capabilities` and `Memory Access Patterns` guidance sections.
- Re-ran the full regression suite and got a clean `111 passed`.

### Command Results

- `python3 - <<'PY' ...` -> `EXA_API_KEY=missing`, `SERPAPI_KEY=missing`
- `uv run python cli.py setup_vault` -> resolved `/Users/chunsingyu/Documents/Obsidian Vault`,
  all `quant-autoresearch/` directories already existed
- `uv run python -m pytest tests/unit/test_vault_config.py tests/unit/test_vault_writer.py tests/unit/test_cli.py tests/unit/test_research.py tests/unit/test_logger_setup.py -q`
  -> `27 passed in 0.52s`
- `uv run python -m pytest tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py tests/unit/test_cli_research.py tests/unit/test_cli_analyze.py tests/unit/test_cli_setup_vault.py tests/integration/test_research_pipeline.py tests/integration/test_analyze_pipeline.py -q`
  -> `13 passed in 0.44s`
- `uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output stdout`
  -> rendered a vault-native literature report from local BM25 / ArXiv sources
- `uv run python cli.py research "intraday momentum strategy minute bars" --depth deep --output stdout`
  -> printed `Deep web search skipped: EXA_API_KEY / SERPAPI_KEY missing. Returning ArXiv-only report.`
- `uv run python cli.py analyze SPY --start 2025-01-01 --output stdout`
  -> rendered a deterministic stock-analysis report from cached `data/cache/SPY.parquet`
- `python3 - <<'PY' ... get_vault_paths().knowledge ...` -> confirmed
  `experiment-methodology.md`, `market-microstructure.md`, `overfit-defense.md`,
  `strategy-pattern-catalog.md`
- `grep -n "## Research Capabilities\\|## Memory Access Patterns" program.md`
  -> lines `97` and `107`
- `uv run python -m pytest tests/unit/test_cli_analyze.py tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py tests/integration/test_analyze_pipeline.py -q`
  -> `9 passed in 0.45s`
- `uv run python -m pytest --tb=short -v` -> `111 passed in 0.91s`

### Blockers / Deviations

- Deep web-search credentials are still absent locally, so Sprint 2 must keep shallow research mode
  as the default safe path and make deep-mode degradation explicit.
- The `analyze` smoke currently depends on locally cached data (`data/cache/SPY.parquet` on this
  machine); closeout evidence should note that prerequisite explicitly.

### Follow-ups

- Step 2 should inspect and reconcile the already-present Sprint 2 code/test changes in the
  dedicated worktree before adding new helper logic.
- Preserve Sprint 1 vault helper reuse (`config.vault`, research report rendering/writing) when
  finishing `research` and `analyze`.
- Closeout should document that `analyze` currently depends on locally cached market data in
  `data/cache`; this machine now has a successful SPY smoke run to reference.
