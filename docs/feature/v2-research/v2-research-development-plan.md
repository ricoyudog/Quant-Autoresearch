# V2 Research -- Development Plan

> Feature branch: `feature/v2-research`
> Umbrella issue: #13
> Canonical root: `docs/feature/v2-research/`

## Context

The V2 architecture replaces the Python-controlled OPENDEV loop with a program.md-driven approach. This issue redesigns the research capabilities:

- **Remove** SQLite Playbook (`src/memory/playbook.py`) -- replaced by Obsidian Markdown notes + results.tsv
- **Create** Obsidian vault subdirectory structure under `quant-autoresearch/`
- **Refactor** research.py to output to Obsidian vault instead of SQLite
- **Add** multi-agent stock analysis CLI (TradingAgents style, pure computation)
- **Add** static knowledge base notes (overfit defense, strategy patterns, microstructure, methodology)
- **Implement** 4-layer memory architecture (short/working/persistent/long-term)

## Files to Remove

| File | Size estimate | Key references to clean |
| --- | --- | --- |
| `src/memory/playbook.py` | ~550 LOC | `Playbook` class, TF-IDF similarity, SQLite |
| `src/memory/__init__.py` | ~10 LOC | module exports |
| `tests/unit/test_playbook_memory.py` | ~70 LOC | tests for Playbook |

## Files to Create

### Obsidian vault structure (directory creation, not versioned)

| Path | Purpose |
| --- | --- |
| `quant-autoresearch/experiments/` | Experiment notes (one per backtest run) |
| `quant-autoresearch/research/` | Research results (CLI generated) |
| `quant-autoresearch/knowledge/` | Static knowledge base notes |

### New source modules

| File | Purpose |
| --- | --- |
| `config/vault.py` | Vault path configuration + directory initialization |
| `src/analysis/__init__.py` | Stock analysis module |
| `src/analysis/technical.py` | Technical indicator calculations |
| `src/analysis/regime.py` | Regime classification (reuses validation logic) |
| `src/analysis/market_context.py` | Market context analysis (SPY correlation, sector) |

### Knowledge base notes (written to vault)

| File | Purpose |
| --- | --- |
| `knowledge/overfit-defense.md` | Overfit defense reference for agent |
| `knowledge/market-microstructure.md` | Minute-level data characteristics |
| `knowledge/strategy-pattern-catalog.md` | Strategy pattern catalog with vault wikilinks |
| `knowledge/experiment-methodology.md` | Experiment design methodology |

## Files to Modify

| File | Changes |
| --- | --- |
| `src/core/research.py` | Refactor: output to Obsidian vault, add vault writer, add dedup |
| `cli.py` | Add subcommands: `research`, `analyze`, `setup_vault` |
| `program.md` | Add research capabilities guidance section |
| `src/core/engine.py` (if exists) | Clean Playbook references |
| Any surviving file importing Playbook | Remove imports, replace with vault reads |

## Files that MUST survive

- `src/core/backtester.py` -- V2 evaluation harness
- `src/core/research.py` -- refactored, not deleted
- `src/data/connector.py` -- data loading
- `src/data/preprocessor.py` -- data preprocessing
- `src/strategies/active_strategy.py` -- the strategy file
- `src/utils/logger.py` -- logging
- `src/utils/telemetry.py` -- W&B telemetry
- `src/utils/iteration_tracker.py` -- iteration tracking
- `src/utils/retries.py` -- retry logic
- `cli.py` -- CLI entry point (modified, not deleted)

## Sprint Plan

| Sprint | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 1 | Obsidian vault structure + Playbook removal | vault dirs created, playbook.py deleted, imports cleaned, test deleted | pending | Sprint 2 |
| Sprint 2 | Multi-agent research CLI + knowledge base | research/analyze CLI, knowledge notes, 4-layer memory | pending | merge readiness |

## Task Table

### Sprint 1 tasks

| Task ID | Task | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- |
| RES-01 | Create `feature/v2-research` branch from `feature/v2-cleanup` | v2-cleanup complete | 0.1d | branch exists |
| RES-02 | Create `config/vault.py` with path configuration and `ensure_dirs()` | RES-01 | 0.2d | module imports, dirs created |
| RES-03 | Create Obsidian vault subdirectories via `setup_vault` command | RES-02 | 0.1d | `quant-autoresearch/{experiments,research,knowledge}/` exist |
| RES-04 | Remove `src/memory/playbook.py` | RES-01 | 0.1d | file deleted |
| RES-05 | Clean all Playbook imports in surviving files | RES-04 | 0.1d | zero references to Playbook class |
| RES-06 | Update `research.py` to output to Obsidian vault | RES-03, RES-04 | 0.3d | research results written to vault |
| RES-07 | Delete `tests/unit/test_playbook_memory.py` | RES-04 | 0.05d | file deleted |
| RES-08 | Verify surviving tests pass | RES-07 | 0.1d | pytest green |

### Sprint 2 tasks

| Task ID | Task | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- |
| RES-09 | Create `src/analysis/` module with technical indicators | RES-03 | 0.3d | module imports, functions work |
| RES-10 | Implement regime classification in `src/analysis/regime.py` | RES-09 | 0.2d | regime classification produces valid results |
| RES-11 | Implement market context analysis | RES-09 | 0.2d | SPY correlation, sector analysis works |
| RES-12 | Add `research` CLI subcommand to `cli.py` | RES-06 | 0.2d | `cli.py research "query"` works |
| RES-13 | Add `analyze` CLI subcommand to `cli.py` | RES-09 | 0.3d | `cli.py analyze AAPL` works |
| RES-14 | Add `setup_vault` CLI subcommand to `cli.py` | RES-02 | 0.1d | `cli.py setup_vault` creates dirs |
| RES-15 | Create static knowledge base notes (4 files) | RES-03 | 0.3d | knowledge/*.md written to vault |
| RES-16 | Implement 4-layer memory architecture documentation | RES-15 | 0.2d | memory access patterns documented in program.md |
| RES-17 | Update `program.md` with research capabilities guidance | RES-12, RES-13 | 0.2d | program.md has research section |
| RES-18 | Write tests for all new modules | RES-09 through RES-13 | 0.4d | all new tests pass |
| RES-19 | Full integration test | RES-18 | 0.2d | end-to-end: research + analyze + vault write |

## Acceptance Criteria

- [ ] `feature/v2-research` branch exists
- [ ] `src/memory/playbook.py` is deleted
- [ ] `tests/unit/test_playbook_memory.py` is deleted
- [ ] No surviving file imports from `src.memory.playbook`
- [ ] Obsidian vault has `quant-autoresearch/{experiments,research,knowledge}/` directories
- [ ] `cli.py setup_vault` creates vault structure
- [ ] `cli.py research "query"` writes results to vault
- [ ] `cli.py analyze AAPL` produces structured analysis report
- [ ] 4 knowledge base notes exist in vault
- [ ] `program.md` has research capabilities guidance section
- [ ] `uv sync` succeeds
- [ ] `pytest` passes with 0 failures
- [ ] No surviving file imports from removed modules

## Verification Commands

```bash
# Verify Playbook removal
test ! -f src/memory/playbook.py && echo "playbook.py GONE"
grep -rn "from src.memory.playbook\|import.*Playbook" src/ tests/ cli.py || echo "PLAYBOOK REFS CLEAN"

# Verify vault structure
uv run python cli.py setup_vault
ls ~/Documents/Obsidian\ Vault/quant-autoresearch/experiments/ && echo "EXPERIMENTS DIR OK"
ls ~/Documents/Obsidian\ Vault/quant-autoresearch/research/ && echo "RESEARCH DIR OK"
ls ~/Documents/Obsidian\ Vault/quant-autoresearch/knowledge/ && echo "KNOWLEDGE DIR OK"

# Verify new CLI commands
uv run python cli.py research "test query" --depth shallow
uv run python cli.py analyze SPY --start 2025-01-01

# Verify tests
pytest --tb=short -v

# Verify no broken imports
python -c "
from config.vault import get_vault_paths, ensure_dirs
from src.analysis.technical import calc_momentum
from src.analysis.regime import classify_regime
from src.analysis.market_context import calc_market_context
print('ALL NEW IMPORTS OK')
"
```

## Risks

| Risk | Mitigation |
| --- | --- |
| Vault path does not exist on machine | `setup_vault` creates dirs; path configurable via env var |
| research.py has BM25 dependency (`bm25s`) | Keep BM25 for local search; only remove SQLite Playbook |
| `openai` package needed for research web search | Evaluate during Sprint 1; keep if research.py uses it |
| `arxiv` package still needed | Keep -- research.py ArXiv search preserved |
| Playbook referenced in surviving engine.py code | Sprint 1 will clean all references |
| Knowledge notes duplicate vault strategy content | Notes are curated summaries with wikilinks to full notes |
