# CLAUDE.md

This file provides repository guidance for Claude Code and similar coding agents.

## Project Overview

Quant Autoresearch is a V2 strategy-research repository. The current workflow is driven by
`program.md` plus the supported `cli.py` commands. Agents iterate on strategy and research work
while validating through the fixed backtesting and analysis surfaces.

## Supported Commands

### Environment and tests

```bash
uv sync
uv sync --all-extras --dev
uv run pytest -q
```

### Data and research surfaces

```bash
# Build / refresh the DuckDB daily cache used by the minute-data pipeline
uv run python cli.py setup-data
uv run python cli.py update-data

# Query minute bars for a bounded window
uv run python cli.py fetch SPY --start 2025-01-01 --end 2025-03-31

# Prepare the vault-native research workspace
uv run python cli.py setup_vault

# Produce research / analysis notes
uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output vault
uv run python cli.py analyze SPY --start 2025-01-01 --end 2025-03-31 --output vault

# Run the minute-mode backtest surface
uv run python cli.py backtest --start 2024-01-01 --end 2024-12-31
```

Notes:
- Live Typer command names are hyphenated (`setup-data`, `update-data`).
- `analyze` can read from `data/daily_cache.duckdb`; legacy `data/cache` symbol files are optional.
- `research --depth shallow` must stay usable without `EXA_API_KEY` / `SERPAPI_KEY`.

## Architecture

### Primary truth surfaces

- `program.md` — agent operating contract
- `cli.py` — supported operator/runtime commands
- `src/core/backtester.py` — evaluation and sandbox rules
- `src/data/duckdb_connector.py` — DuckDB daily-cache build/load + minute-data queries
- `src/core/research.py` — vault-native research helpers
- `src/analysis/` — deterministic stock-analysis report helpers
- `src/strategies/active_strategy.py` — strategy file under iteration

### Runtime model

1. Build or refresh the DuckDB daily cache with `setup-data` / `update-data`.
2. Query minute data on demand with `fetch`.
3. Use `setup_vault`, `research`, and `analyze` for the vault-native research workflow.
4. Validate strategies with the minute-mode backtester.

There is no active Python-side legacy orchestration loop in the current `main_dev` closeout target.
Historical docs may still discuss older runtime phases, but current operator guidance should follow
`program.md` and the CLI/runtime surfaces above.

## Environment Variables

Common runtime variables:

- `OBSIDIAN_VAULT_PATH` — override the vault root used by `setup_vault`, `research`, and `analyze`
- `EXA_API_KEY` / `SERPAPI_KEY` — optional deep-research web search providers
- `MINUTE_AGGS_CLI` — path to the `minute-aggs` executable
- `MINUTE_AGGS_DATASET_ROOT` — root of the local minute parquet dataset
- `STRATEGY_FILE` — optional strategy override for backtests
- `BACKTEST_START_DATE` / `BACKTEST_END_DATE` / `BACKTEST_UNIVERSE_SIZE` — optional backtest runtime bounds

## Verification Expectations

When changing product behavior or closeout surfaces, collect fresh evidence with the relevant mix of:

- `uv run pytest -q`
- `uv run python cli.py --help`
- `uv run python cli.py setup_vault`
- `uv run python cli.py setup-data`
- `uv run python cli.py research ...`
- `uv run python cli.py analyze ...`
- `uv run python cli.py backtest ...`

Do not claim completion from historical comments alone when fresh current-session verification is required.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Quant-Autoresearch** (3771 symbols, 6588 relationships, 182 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Quant-Autoresearch/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Quant-Autoresearch/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Quant-Autoresearch/clusters` | All functional areas |
| `gitnexus://repo/Quant-Autoresearch/processes` | All execution flows |
| `gitnexus://repo/Quant-Autoresearch/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
