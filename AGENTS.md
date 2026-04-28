# Agentic Coding Guidelines for Quant Autoresearch

This file provides guidelines for agents working in this repository.

## Project Overview

Quant Autoresearch is an autonomous quantitative strategy discovery framework using AI agents. It uses Python 3.12+, pytest for testing, and uv for package management.

## Repository Navigation

- `program.md` is the root runtime / agent operating contract
- `docs/index.md` is the canonical documentation entrypoint
- `docs/architecture/index.md` is the canonical architecture entrypoint
- `docs/program/index.md` is the planning and long-horizon hub
- `specs/index.md` is the canonical execution-spec index
- `docs/reference/index.md` contains non-canonical background material
- `docs/archive/index.md` contains historical material
- `docs/feature/README.md` marks retained legacy V2 feature workspaces

---

## Build / Lint / Test Commands

### Running Tests

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/unit/test_engine_opendev.py

# Run a single test function
pytest tests/unit/test_engine_opendev.py::test_engine_initialization

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run tests by marker
pytest -m "unit"
pytest -m "integration"

# Run tests in specific directory
pytest tests/unit/
pytest tests/integration/
```

### Package Management (uv)

```bash
# Install dependencies
uv sync

# Add a dependency
uv add <package>

# Add dev dependency
uv add --dev <package>

# Run Python scripts
uv run python cli.py run --iterations 10
```

### Type Checking

This project uses Python's typing system. Run type checking with:

```bash
# Install mypy first
uv add --dev mypy

# Run type checker
uv run mypy src/
```

---

## Code Style Guidelines

### General Principles

- Use Python 3.10+ compatible syntax (project uses 3.12.0)
- Keep lines under 120 characters
- Use 4 spaces for indentation (no tabs)
- Use meaningful variable and function names

### Imports

**Organize imports in this order (alphabetically within each group):**
1. Standard library (`os`, `sys`, `json`, `re`, `ast`, `subprocess`, `time`)
2. Third-party packages (`groq`, `dotenv`, `pytest`)
3. Local application imports (relative imports from `src/`)

```python
# Correct import order
import os
import json
import re
from typing import Dict, List, Optional, Tuple, Any

from groq import Groq
from dotenv import load_dotenv

from core.engine import QuantAutoresearchEngine
from safety.guard import SafetyLevel, ApprovalMode
from utils.logger import logger
```

### Type Annotations

- Use type hints for function arguments and return values
- Use `Dict`, `List`, `Optional`, `Tuple`, `Any` from `typing` module
- Prefer concrete types over `Any` when possible

```python
# Good
def process_data(data: Dict[str, int]) -> List[str]:
    ...

# Acceptable for complex types
async def run(max_iterations: int = 10) -> Optional[Dict[str, Any]]:
    ...
```

### Naming Conventions

- **Classes:** `PascalCase` (e.g., `QuantAutoresearchEngine`, `SafetyGuard`)
- **Functions/methods:** `snake_case` (e.g., `run_backtest`, `get_context_status`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_CONTEXT_PERCENT`)
- **Private methods:** prefix with underscore (e.g., `_phase_thinking`)
- **Module names:** `snake_case` (e.g., `tool_registry.py`)

### Error Handling

- Use try/except blocks for operations that may fail
- Log errors with appropriate level (`logger.error`, `logger.warning`)
- Provide meaningful error messages
- Catch specific exceptions when possible

```python
# Good error handling
try:
    result = subprocess.run(["uv", "run", "python", script], 
                          capture_output=True, text=True)
except FileNotFoundError:
    logger.error("Python interpreter not found")
    return None
except Exception as e:
    logger.error(f"Execution failed: {e}")
    return None
```

### Docstrings

Use Google-style docstrings for classes and functions:

```python
def run_backtest_with_output() -> Tuple[float, float, int, float, Dict]:
    """Execute backtest and parse results.
    
    Returns:
        Tuple of (score, drawdown, trades, p_value, output_dict)
    """
    ...
```

### Class Structure

```python
class QuantAutoresearchEngine:
    """OPENDEV Enhanced ReAct Loop engine for Quant Autoresearch"""
    
    def __init__(self, safety_level: SafetyLevel = SafetyLevel.HIGH,
                 max_context_percent: int = 95):
        self.safety_level = safety_level
        self.max_context_percent = max_context_percent
        
        # Core components
        self.compactor = ContextCompactor(...)
    
    def run(self, max_iterations: int = 10):
        """Run the autonomous research loop."""
        ...
    
    def _phase_context_mgmt(self):
        """Phase 0: Adaptive Context Compaction."""
        ...
```

### Async/Await

- Use `async`/`await` for I/O-bound operations
- Use `asyncio.run()` to entry points
- Configure pytest with `asyncio_mode = auto` (already in pytest.ini)

```python
async def run(self, max_iterations: int = 10):
    for i in range(max_iterations):
        result = await self._some_async_call()
        ...

# Entry point
if __name__ == "__main__":
    import asyncio
    engine = QuantAutoresearchEngine()
    asyncio.run(engine.run())
```

### Testing Conventions

- Use pytest fixtures for setup/teardown
- Use `unittest.mock` for mocking external dependencies
- Name test files as `test_<module>.py`
- Name test functions as `test_<description>`

```python
@pytest.fixture
def engine(tmp_path):
    db_path = tmp_path / "test_playbook.db"
    with patch("core.engine.Groq"):
        engine = QuantAutoresearchEngine(db_path=str(db_path))
        return engine

def test_engine_initialization(engine):
    assert engine.safety_level == SafetyLevel.LOW
```

### File Organization

```
src/
├── core/           # Engine logic, backtester
├── safety/        # Guardrails, safety checks
├── models/         # LLM routing
├── memory/        # Pattern playbook
├── tools/         # Tool registry
├── prompts/       # System instructions
├── context/       # Context management
├── utils/         # Logger, telemetry, trackers
└── data/          # Data processing

tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
├── regression/    # Regression tests
└── security/     # Security tests
```

### Configuration

- Environment variables go in `.env` (not committed)
- Template in `.env.example`
- Use `python-dotenv` for loading

---

## Key Architecture Patterns

### OPENDEV 6-Phase Cycle

1. **Phase 0 - Context Management:** Adaptive Context Compaction (ACC)
2. **Phase 1 - Thinking:** Use separate model for reasoning
3. **Phase 2 - Action Selection:** Primary model selects tools
4. **Phase 3 - Doom-Loop Detection:** Fingerprint checking
5. **Phase 4 - Execution:** 5-layer defense-in-depth
6. **Phase 5 - Observation:** Output optimization and playbook storage

### Safety Layers

1. Prompt Guardrails
2. Schema Gating
3. Runtime Approval
4. Tool Validation
5. Look-Ahead Scanner (AST-based)

---

## Notes

- All tests must pass before merging (run `pytest` to verify)
- Use type hints where practical
- Keep functions focused and small
- Document complex logic with comments
- Always log important operations

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Quant-Autoresearch** (3402 symbols, 5644 relationships, 137 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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

## Active Technologies
- Python 3.12+ for repository tooling; Markdown and JSON for closeout artifacts + stdlib file handling, git CLI, pytest, uv, Typer-based repo tooling, existing planning docs (001-v2-closeout)
- Repository files under `/Users/chunsingyu/softwares/Quant-Autoresearch`, especially `specs/`, `docs/index.md`, `docs/reference/`, `docs/archive/`, and git metadata (001-v2-closeout)
- Python 3.12+ for the loop runner and repository tooling; shell wrapper for Claude Code invocation + existing `cli.py` commands, `src/core/backtester.py`, `src/core/research.py`, `src/memory/idea_keep_revert.py`, `src/memory/candidate_generation.py`, Claude Code CLI, git CLI (002-claude-autoresearch-loop)
- Repository files plus persisted run artifacts under `/Users/chunsingyu/softwares/Quant-Autoresearch/experiments/` and optional vault notes under the configured Obsidian path (002-claude-autoresearch-loop)
- Python 3.10+ (repo guidance targets Python 3.12+ in active development) + pandas, numpy, pytest, RestrictedPython-compatible strategy surface, existing Typer CLI/backtester stack (003-turnover-reduction)
- File-based repository artifacts (`src/strategies/active_strategy.py`, `experiments/results.tsv`, Obsidian vault notes) plus existing DuckDB daily cache inpu (003-turnover-reduction)

## Recent Changes
- 001-v2-closeout: Added Python 3.12+ for repository tooling; Markdown and JSON for closeout artifacts + stdlib file handling, git CLI, pytest, uv, Typer-based repo tooling, existing planning docs
