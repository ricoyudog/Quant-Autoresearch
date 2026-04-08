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
- [ ] Confirm Sprint 1 backend and infra outcomes are recorded before starting Sprint 2 work.
- [ ] Re-read `sprint2-infra.md` so API-key fallback and local data assumptions stay aligned.
- [ ] Verify the Sprint 1 vault writer and `setup_vault` surface still behave as expected.
- [ ] Record any inherited constraints that shape CLI arguments or output formats.

### Step 2 -- Build the deterministic analysis helpers
- [ ] Create `src/analysis/__init__.py`.
- [ ] Implement `src/analysis/technical.py` with momentum, volatility, volume, and key-level
      helpers.
- [ ] Implement `src/analysis/regime.py` with bull / bear and quiet / volatile classification
      outputs.
- [ ] Implement `src/analysis/market_context.py` with SPY-correlation and moving-average context
      helpers.
- [ ] Keep helper outputs structured and deterministic so the CLI and tests can consume them
      directly.

### Step 3 -- Finalize the `research` CLI surface
- [ ] Add `research` to `cli.py` with `query`, `--depth`, and `--output` controls.
- [ ] Reuse the Sprint 1 research helpers for formatting, dedup, and vault writes.
- [ ] Make shallow ArXiv-only behavior work even when deep web-search credentials are absent.
- [ ] Make operator-visible output clear when the command reuses an existing research note or
      skips deep web search due to missing credentials.

### Step 4 -- Implement the `analyze` CLI surface
- [ ] Add `analyze` to `cli.py` with ticker, date-range, and output controls.
- [ ] Load the local market-data surface validated in `sprint2-infra.md` instead of preserving a
      stale path assumption in code.
- [ ] Fail clearly when the local runtime data prerequisite is unavailable.
- [ ] Compose report sections for momentum, volatility, regime, price structure, and market context.
- [ ] Support both stdout output and vault-note output.

### Step 5 -- Add knowledge notes and `program.md` guidance
- [ ] Write the four knowledge notes with YAML frontmatter into the vault `knowledge/` surface.
- [ ] Add a `Research Capabilities` section to `program.md` that explains when and how to use the
      CLI tools and knowledge notes.
- [ ] Add a `Memory Access Patterns` section to `program.md` that matches the implemented vault and
      `results.tsv` workflow.
- [ ] Keep note topics and terminology aligned with `docs/research-capabilities-v2.md`.

### Step 6 -- Add Sprint 2 test coverage
- [ ] Create `tests/unit/test_technical.py`, `tests/unit/test_regime.py`, and
      `tests/unit/test_market_context.py`.
- [ ] Create `tests/unit/test_cli_research.py`, `tests/unit/test_cli_analyze.py`, and
      `tests/unit/test_cli_setup_vault.py`.
- [ ] Update `tests/unit/test_cli.py` so registration assertions match the new command surface.
- [ ] Add `tests/integration/test_research_pipeline.py` and
      `tests/integration/test_analyze_pipeline.py`.

### Step 7 -- Verify Sprint 2 and prepare closeout evidence
- [ ] Run the targeted helper, CLI, and integration tests after implementation lands.
- [ ] Run `uv run python cli.py research ...` in shallow mode and capture the output.
- [ ] Run `uv run python cli.py analyze ...` and capture the output or the clear failure mode if
      infra prerequisites are still blocking.
- [ ] Run `pytest --tb=short -v` before calling Sprint 2 complete.
- [ ] Record any follow-up work that should stay out of the current sprint scope.

## 4) Test Plan

- [ ] `tests/unit/test_technical.py`, `tests/unit/test_regime.py`, and
      `tests/unit/test_market_context.py` cover the deterministic analysis helpers.
- [ ] `tests/unit/test_cli_research.py`, `tests/unit/test_cli_analyze.py`, and
      `tests/unit/test_cli_setup_vault.py` cover the new CLI surface.
- [ ] `tests/unit/test_cli.py` reflects the registered command surface after Sprint 2 lands.
- [ ] `tests/integration/test_research_pipeline.py` and `tests/integration/test_analyze_pipeline.py`
      prove vault writes and report structure.
- [ ] `program.md` includes the final `Research Capabilities` and `Memory Access Patterns` sections.
- [ ] `pytest --tb=short -v` passes before the sprint is called complete.

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

- leave blank until implemented

### Command Results

- leave blank until implemented

### Blockers / Deviations

- leave blank until implemented

### Follow-ups

- leave blank until implemented
