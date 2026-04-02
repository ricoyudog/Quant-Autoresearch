# Sprint 2 -- Backend Plan

> Feature: `v2-research`
> Role: Backend
> Derived from: #13 (Research capabilities redesign) -- CLI + knowledge base + memory
> Last Updated: 2026-04-02

## 0) Governing Specs

1. `docs/research-capabilities-v2.md` -- V2 research design (Sections 2-5, 7)
2. `docs/upgrade-plan-v2.md` -- V2 upgrade plan (Section 17, CLI commands)
3. `docs/feature/v2-research/v2-research-development-plan.md` -- Task table Sprint 2

## 1) Sprint Mission

Build the multi-agent research and stock analysis CLI capabilities, create the static knowledge base, and implement the 4-layer memory architecture. The `research` CLI command wraps ArXiv + web search and writes structured Markdown to the Obsidian vault. The `analyze` CLI command runs pure-computation technical analysis (TradingAgents style, no LLM) for stock research. Four curated knowledge base notes provide the agent with overfit defense, microstructure, strategy patterns, and methodology reference.

## 2) Scope / Out of Scope

**Scope**
- Create `src/analysis/__init__.py` module
- Implement `src/analysis/technical.py` with technical indicator calculations
- Implement `src/analysis/regime.py` with regime classification
- Implement `src/analysis/market_context.py` with SPY correlation and MA analysis
- Add `research` CLI subcommand with `--depth` flag
- Add `analyze` CLI subcommand with `--start`, `--end`, `--output` flags
- Create 4 static knowledge base notes in vault `knowledge/` directory
- Update `program.md` with research capabilities guidance section
- Document 4-layer memory architecture in program.md
- Write tests for all new modules (7 test files)
- Integration tests for full research and analysis pipelines

**Out of Scope**
- Playbook removal -- Sprint 1 (must be complete)
- Vault directory creation -- Sprint 1 (must be complete)
- Vector search for vault notes -- future extension
- Multi-agent Bull/Bear debate (true multi-agent) -- future extension
- Automatic ArXiv ingestion -- future extension

## 3) Step-by-Step Plan

### Step 1 -- Create analysis module (RES-09)
- [ ] Create `src/analysis/__init__.py`
- [ ] Create `src/analysis/technical.py` with:
  - `calc_momentum(df)` -- ROC(5), ROC(10), ROC(20)
  - `calc_volatility(df)` -- Realized Vol (5d, 20d, 60d annualized)
  - `analyze_volume(df)` -- relative_volume, volume_trend
  - `find_key_levels(df)` -- support/resistance from 60d high/low
  - `calc_summary_stats(df)` -- Sharpe, max DD, win rate, avg daily range
- [ ] Verify: `python -c "from src.analysis.technical import calc_momentum; print('OK')"`

### Step 2 -- Implement regime classification (RES-10)
- [ ] Create `src/analysis/regime.py` with:
  - `classify_regime(df)` -- returns one of: bull_quiet, bull_volatile, bear_quiet, bear_volatile
  - Uses rolling 20d return + rolling 20d vol vs median
  - Returns dict: `{ current, vol_percentile, regime_distribution }`
- [ ] Reuse logic from `validation/regime.py` if it exists (from Session 3 design)
- [ ] Verify: `python -c "from src.analysis.regime import classify_regime; print('OK')"`

### Step 3 -- Implement market context analysis (RES-11)
- [ ] Create `src/analysis/market_context.py` with:
  - `calc_market_context(ticker, daily_data)` -- SPY correlation, sector positioning
  - `calc_ma_distance(df)` -- distance from 50d and 200d MA
  - Returns dict with correlation, ma_50d_distance, ma_200d_distance
- [ ] Verify: `python -c "from src.analysis.market_context import calc_market_context; print('OK')"`

### Step 4 -- Add research CLI subcommand (RES-12)
- [ ] Add `research` subcommand to `cli.py`:
  - Positional arg: `query` (search query string)
  - `--depth` flag: `shallow` (ArXiv only) or `deep` (ArXiv + web + synthesis)
  - `--output` flag: `vault` (default) or `stdout`
- [ ] Implementation flow:
  1. ArXiv search (reuse V1 `search_arxiv()` from research.py)
  2. Web search (if deep, reuse V1 `search_web()`)
  3. Format as Markdown with YAML frontmatter
  4. Write to vault or print to stdout
- [ ] Add dedup check: search vault `research/` for existing results before querying APIs
- [ ] Verify: `uv run python cli.py research "mean reversion" --depth shallow --output stdout`

### Step 5 -- Add analyze CLI subcommand (RES-13)
- [ ] Add `analyze` subcommand to `cli.py`:
  - Positional arg: `tickers` (one or more ticker symbols)
  - `--start` flag: start date (default: 60 trading days ago)
  - `--end` flag: end date (default: today)
  - `--output` flag: `vault` (default) or `stdout`
- [ ] Implementation flow:
  1. Load daily data from DuckDB/Parquet cache (via DataConnector)
  2. Run technical analysis (calc_momentum, calc_volatility, analyze_volume, find_key_levels)
  3. Run regime classification
  4. Run market context analysis
  5. Format as structured Markdown with YAML frontmatter
  6. Write to vault or print to stdout
- [ ] No LLM calls -- pure computation
- [ ] Verify: `uv run python cli.py analyze SPY --start 2025-01-01 --output stdout`

### Step 6 -- Create knowledge base notes (RES-15)
- [ ] Write `knowledge/overfit-defense.md` to vault:
  - Why overfitting happens (Lopez de Prado summary)
  - Layer 1: Built-in defenses (every backtest): NW Sharpe, Deflated SR, Walk-Forward
  - Layer 2: Advanced validation (on-demand): CPCV, Regime analysis, Parameter stability
  - Red flags: NW_SHARPE_BIAS > 0.3, DEFLATED_SR < 0.5
  - Academic references
- [ ] Write `knowledge/market-microstructure.md` to vault:
  - Bid-ask bounce, non-synchronous trading
  - Newey-West adjustment for minute data
  - Volume patterns (open/close clustering, lunch lull)
  - Overnight gaps handling
  - Data characteristics (source, tickers, bars/day, date range)
- [ ] Write `knowledge/strategy-pattern-catalog.md` to vault:
  - Momentum, Mean Reversion, Regime-Based, Risk Management Overlays
  - Each with: Core Idea, Signals, Works Best, Key Risk, Vault References (wikilinks)
  - Implementation guidelines
- [ ] Write `knowledge/experiment-methodology.md` to vault:
  - How to design a good experiment
  - Common pitfalls
  - Decision framework (SCORE thresholds)
  - Reading results (NW Sharpe, Deflated SR, Per-Symbol)
  - When to pivot
- [ ] All notes must have YAML frontmatter: note_type, topic, last_updated, tags
- [ ] Verify: all 4 files exist in vault `knowledge/` directory

### Step 7 -- Update program.md (RES-16, RES-17)
- [ ] Add "Research Capabilities" section to `program.md`:
  - Reading the Knowledge Base (paths, categories, when to read)
  - Research CLI usage (commands, depth options, when to run)
  - Stock Analysis CLI usage (commands, output sections, when to use)
  - When to Do Research (before starting, every 10 experiments, stuck, after improvement)
- [ ] Add "Memory Access Patterns" section:
  - Layer 1 (short): session context, last 2-3 experiments
  - Layer 2 (working): active_strategy.py, run.log, current session experiments/
  - Layer 3 (persistent): vault knowledge/, research/, trading strategy/
  - Layer 4 (long-term): results.tsv, commit hash tracking
- [ ] Verify: program.md contains both new sections

### Step 8 -- Write analysis module tests (RES-18)
- [ ] Create `tests/unit/test_technical.py`:
  - `test_calc_momentum_basic` -- correct ROC values
  - `test_calc_momentum_short_data` -- returns None for insufficient data
  - `test_calc_volatility` -- annualized vol values
  - `test_analyze_volume` -- relative volume, trend
  - `test_find_key_levels` -- high, low, close, percentages
- [ ] Create `tests/unit/test_regime.py`:
  - `test_classify_regime_bull_quiet` -- positive returns, low vol
  - `test_classify_regime_bear_volatile` -- negative returns, high vol
  - `test_classify_regime_returns_vol_percentile` -- value in [0, 1]
  - `test_classify_regime_all_four_types` -- all four regimes producible
- [ ] Create `tests/unit/test_market_context.py`:
  - `test_calc_market_context_correlation` -- SPY correlation in [-1, 1]
  - `test_calc_market_context_ma_distance` -- MA distances are floats
  - `test_calc_market_context_with_real_data` -- (integration-ish) uses cached data if available
- [ ] Verify: `pytest tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py -v`

### Step 9 -- Write CLI tests (RES-18 continued)
- [ ] Create `tests/unit/test_cli_research.py`:
  - `test_research_command_shallow` -- output has header
  - `test_research_command_outputs_yaml_frontmatter` -- starts with `---`
  - `test_research_command_writes_to_vault` -- file created
  - `test_research_dedup` -- existing research detected
- [ ] Create `tests/unit/test_cli_analyze.py`:
  - `test_analyze_command_single_ticker` -- output has header
  - `test_analyze_command_includes_all_sections` -- all sections present
  - `test_analyze_command_writes_to_vault` -- file created
  - `test_analyze_command_invalid_ticker` -- graceful error
- [ ] Create `tests/unit/test_cli_setup_vault.py`:
  - `test_setup_vault_creates_dirs` -- all 3 dirs created
  - `test_setup_vault_idempotent` -- no error on repeat
- [ ] Verify: `pytest tests/unit/test_cli_*.py -v`

### Step 10 -- Write integration tests (RES-19)
- [ ] Create `tests/integration/test_research_pipeline.py`:
  - `test_research_shallow_pipeline` -- query -> vault write -> file exists -> frontmatter valid
  - `test_research_deep_pipeline` -- (if API keys available)
- [ ] Create `tests/integration/test_analyze_pipeline.py`:
  - `test_analyze_pipeline` -- ticker -> analysis -> vault write -> all sections present
- [ ] Verify: `pytest tests/integration/test_research_pipeline.py tests/integration/test_analyze_pipeline.py -v`

### Step 11 -- Full verification (RES-19 continued)
- [ ] `pytest --tb=short -v` -- all tests pass
- [ ] `uv run python cli.py setup_vault` -- runs without error
- [ ] `uv run python cli.py research "test" --depth shallow --output stdout` -- produces output
- [ ] `uv run python cli.py analyze SPY --start 2025-01-01 --output stdout` -- produces output
- [ ] Knowledge base notes exist: `ls ~/Documents/Obsidian\ Vault/quant-autoresearch/knowledge/`
- [ ] program.md has research capabilities section

### Step 12 -- Commit sprint 2 changes
- [ ] `git add -A && git commit -m "feat(v2-research): add research/analyze CLI, knowledge base, 4-layer memory"`

## 4) Test Plan

- [ ] After Step 1-3: `pytest tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py` passes
- [ ] After Step 4: `pytest tests/unit/test_cli_research.py` passes
- [ ] After Step 5: `pytest tests/unit/test_cli_analyze.py` passes
- [ ] After Step 6: all 4 knowledge notes exist in vault
- [ ] After Step 7: program.md has research + memory sections
- [ ] After Step 8-10: all new tests pass
- [ ] After Step 11: full pytest green, CLI commands work

## 5) Verification Commands

```bash
# New module imports
python -c "
from src.analysis.technical import calc_momentum, calc_volatility, analyze_volume, find_key_levels
from src.analysis.regime import classify_regime
from src.analysis.market_context import calc_market_context
print('ALL ANALYSIS IMPORTS OK')
"

# CLI commands
uv run python cli.py setup_vault && echo "SETUP_VAULT OK"
uv run python cli.py research "test query" --depth shallow --output stdout && echo "RESEARCH OK"
uv run python cli.py analyze SPY --start 2025-01-01 --output stdout && echo "ANALYZE OK"

# Knowledge base
ls ~/Documents/Obsidian\ Vault/quant-autoresearch/knowledge/overfit-defense.md && echo "OVERFIT DEFENSE OK"
ls ~/Documents/Obsidian\ Vault/quant-autoresearch/knowledge/market-microstructure.md && echo "MICROSTRUCTURE OK"
ls ~/Documents/Obsidian\ Vault/quant-autoresearch/knowledge/strategy-pattern-catalog.md && echo "PATTERNS OK"
ls ~/Documents/Obsidian\ Vault/quant-autoresearch/knowledge/experiment-methodology.md && echo "METHODOLOGY OK"

# program.md sections
grep -c "Research Capabilities" program.md && echo "RESEARCH SECTION OK"
grep -c "Memory Access Patterns" program.md && echo "MEMORY SECTION OK"

# Full test suite
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

- All sprints complete -- issue ready for review
- Future extensions: vector search, auto ingestion, multi-agent debate
