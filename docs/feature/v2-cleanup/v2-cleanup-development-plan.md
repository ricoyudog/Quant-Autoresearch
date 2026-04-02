# V2 Cleanup — Development Plan

> Feature branch: `feature/v2-cleanup`
> Umbrella issue: #1
> Canonical root: `docs/feature/v2-cleanup/`

## Context

The V2 architecture replaces the Python-controlled 6-Phase OPENDEV loop with a program.md-driven approach where Claude Code/Codex autonomously runs the experiment loop. All V1 components that implemented the Python-side control (engine, context management, prompt composition, safety guardrails, tool registry, LLM routing, token counting) must be removed.

The backtester (`src/core/backtester.py`) and data connector (`src/data/connector.py`) are preserved — they serve the V2 architecture directly.

## Files to Remove

### Core framework (Issue #2)
| File | Size estimate | Key references to clean |
| --- | --- | --- |
| `src/core/engine.py` | ~500 LOC | `QuantAutoresearchEngine` class |
| `src/context/compactor.py` | ~200 LOC | `ContextCompactor` class |
| `src/context/composer.py` | ~150 LOC | `PromptComposer` class |
| `src/context/__init__.py` | ~10 LOC | module exports |

### Safety & Tools (Issue #3)
| File | Size estimate | Key references to clean |
| --- | --- | --- |
| `src/safety/guard.py` | ~300 LOC | `SafetyGuard` class, 5-layer defense |
| `src/tools/registry.py` | ~200 LOC | `LazyToolRegistry` class |
| `src/tools/bm25_search.py` | ~150 LOC | `BM25Search` class |
| `src/safety/__init__.py` | ~10 LOC | module exports |
| `src/tools/__init__.py` | ~10 LOC | module exports |

### Model & Tokens (Issue #4)
| File | Size estimate | Key references to clean |
| --- | --- | --- |
| `src/models/router.py` | ~250 LOC | `ModelRouter` class, `model_router` singleton |
| `src/models/__init__.py` | ~10 LOC | module exports |
| `src/utils/token_counter.py` | ~100 LOC | `token_counter` singleton |

### Prompts (Issue #5)
| File | Purpose |
| --- | --- |
| `src/prompts/identity.md` | Agent identity prompt |
| `src/prompts/safety_policy.md` | Safety policy prompt |
| `src/prompts/tool_guidance.md` | Tool usage guidance |
| `src/prompts/quant_rules.md` | Quant-specific rules |
| `src/prompts/git_rules.md` | Git commit rules |
| `src/prompts/program.md` | V1 "constitution" — check if V2 program.md supersedes |
| `src/prompts/__init__.py` | module exports |

### Tests (Issue #6)
| File | Tests what (being removed) |
| --- | --- |
| `tests/unit/test_engine_opendev.py` | engine.py |
| `tests/unit/test_guard_opendev.py` | safety/guard.py |
| `tests/unit/test_tool_registry.py` | tools/registry.py |
| `tests/unit/test_router_routing.py` | models/router.py |
| `tests/unit/test_compactor_acc.py` | context/compactor.py |
| `tests/unit/test_compactor_logic.py` | context/compactor.py |
| `tests/unit/test_composer_modular.py` | context/composer.py |
| `tests/unit/test_bm25_tool.py` | tools/bm25_search.py |
| `tests/integration/test_engine_integration.py` | engine integration |
| `tests/integration/test_loop.py` | engine loop |
| `tests/regression/test_engine_arity.py` | engine arity |
| `tests/regression/test_editable_region.py` | EDITABLE REGION (removed in V2) |

### Dependencies to remove from pyproject.toml (Issue #7)
| Package | Used by (being removed) |
| --- | --- |
| `groq>=0.4.0` | models/router.py |
| `tiktoken>=0.5.0` | utils/token_counter.py |
| `openai>=2.26.0` | models/router.py (Moonshot/OpenAI-compatible) |

## Files that MUST survive

These files are NOT touched:
- `src/core/backtester.py` — V2 evaluation harness (modified in Phase 1)
- `src/core/research.py` — preserved as skill for later
- `src/data/connector.py` — data loading
- `src/data/preprocessor.py` — data preprocessing
- `src/memory/playbook.py` — optional tool, preserved
- `src/strategies/active_strategy.py` — the strategy file (EDITABLE REGION removed in Phase 1)
- `src/utils/logger.py` — logging
- `src/utils/telemetry.py` — W&B telemetry
- `src/utils/iteration_tracker.py` — iteration tracking
- `src/utils/retries.py` — retry logic
- `cli.py` — CLI entry point (simplified in Phase 3)
- `tests/unit/test_data.py` — data connector tests
- `tests/unit/test_security.py` — backtester security tests
- `tests/unit/test_playbook_memory.py` — playbook tests
- `tests/unit/test_research.py` — research module tests
- `tests/unit/test_retry_logic.py` — retry tests
- `tests/unit/test_runner.py` — runner tests
- `tests/unit/test_telemetry_wandb.py` — telemetry tests
- `tests/unit/test_tracker_metrics.py` — tracker tests
- `tests/security/test_adversarial.py` — adversarial tests
- `tests/security/test_safety_workflow.py` — safety workflow tests
- `tests/integration/test_integration.py` — integration tests
- `tests/regression/test_determinism.py` — determinism tests
- `tests/conftest.py` — shared fixtures (needs cleanup of removed-module fixtures)

## Phase Plan

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Phase 0 — Preparation | Create branch, verify current tests pass | feature branch, green CI baseline | pending | start module removal |
| Phase 2.1 — Engine & Context | Remove engine.py and context/ directory (#2) | 4 files deleted, imports cleaned | pending | proceed to safety/tools |
| Phase 2.2 — Safety & Tools | Remove safety guard and tool registry (#3) | 5 files deleted, imports cleaned | pending | proceed to model/tokens |
| Phase 2.3 — Model & Tokens | Remove model router and token counter (#4) | 3 files deleted, singletons cleaned | pending | proceed to prompts |
| Phase 2.4 — Prompts | Clean prompts directory (#5) | 6-7 files deleted, prompts/ cleared | pending | proceed to tests |
| Phase 2.5 — Tests | Remove old architecture tests (#6) | 12 test files deleted, conftest cleaned | pending | proceed to deps |
| Phase 2.6 — Dependencies | Update pyproject.toml and verify (#7) | deps removed, uv sync green, pytest green | pending | merge readiness |

## Task Table

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| CORE-01 | Create `feature/v2-cleanup` branch | Dev | none | 0.1d | branch exists, tests green on main |
| CORE-02 | Remove `src/core/engine.py` | Dev | CORE-01 | 0.1d | file deleted, no import of `QuantAutoresearchEngine` |
| CORE-03 | Remove `src/context/` directory | Dev | CORE-01 | 0.1d | directory deleted, no import of `ContextCompactor`, `PromptComposer` |
| SAFE-01 | Remove `src/safety/guard.py` | Dev | CORE-02 | 0.1d | file deleted, no import of `SafetyGuard` |
| TOOL-01 | Remove `src/tools/registry.py` | Dev | CORE-02 | 0.1d | file deleted, no import of `LazyToolRegistry` |
| TOOL-02 | Remove `src/tools/bm25_search.py` | Dev | CORE-02 | 0.1d | file deleted, no import of `BM25Search` |
| TOOL-03 | Clean up `src/safety/__init__.py` and `src/tools/__init__.py` | Dev | SAFE-01, TOOL-02 | 0.05d | empty dirs removed or cleaned |
| MODEL-01 | Remove `src/models/router.py` | Dev | CORE-02 | 0.1d | file deleted, no import of `ModelRouter`, `model_router` |
| MODEL-02 | Remove `src/utils/token_counter.py` | Dev | CORE-02 | 0.1d | file deleted, no import of `token_counter` |
| MODEL-03 | Verify surviving utils (logger, telemetry, tracker, retries) | Dev | MODEL-01, MODEL-02 | 0.1d | no broken imports in remaining utils |
| PROMPT-01 | Remove all V1 prompt .md files | Dev | CORE-02 | 0.05d | `src/prompts/` only has `__init__.py` or is fully removed |
| PROMPT-02 | Evaluate if `src/prompts/program.md` (V1) is superseded by root `program.md` (V2) | Dev | PROMPT-01 | 0.05d | decision recorded, file kept or removed |
| TEST-01 | Remove test files for deleted modules (12 files) | Dev | SAFE-01, TOOL-01, MODEL-01, PROMPT-01 | 0.2d | all 12 test files deleted |
| TEST-02 | Clean `tests/conftest.py` of fixtures referencing removed modules | Dev | TEST-01 | 0.1d | conftest.py has no broken imports |
| TEST-03 | Check `tests/security/` and `tests/integration/` for broken refs | Dev | TEST-01 | 0.1d | all remaining tests import-valid |
| DEP-01 | Remove `groq`, `tiktoken`, `openai` from pyproject.toml | Dev | TEST-03 | 0.05d | pyproject.toml updated |
| DEP-02 | Global grep for imports of removed modules in surviving files | Dev | DEP-01 | 0.1d | zero hits for removed module names |
| DEP-03 | Run `uv sync` and `pytest` | Dev | DEP-02 | 0.1d | both commands succeed green |
| DEP-04 | Verify `cli.py setup_data` and `cli.py fetch` still work | Dev | DEP-03 | 0.05d | commands run without error |

## Acceptance Criteria

- [ ] `feature/v2-cleanup` branch exists
- [ ] All 18 source files listed above are deleted
- [ ] All 12 test files listed above are deleted
- [ ] `src/context/`, `src/safety/`, `src/tools/`, `src/models/` directories are empty or removed
- [ ] `src/prompts/` is empty or removed (except possibly `__init__.py`)
- [ ] `groq`, `tiktoken`, `openai` removed from pyproject.toml
- [ ] `uv sync` succeeds
- [ ] `pytest` passes with 0 failures
- [ ] `cli.py setup_data` and `cli.py fetch` run without error
- [ ] No surviving file imports from any removed module

## Verification Commands

```bash
# Verify files are gone
ls src/core/engine.py src/context/ src/safety/guard.py src/tools/registry.py src/models/router.py src/utils/token_counter.py 2>&1 | grep "No such file"

# Verify no broken imports
grep -r "from src.core.engine\|from src.context\|from src.safety.guard\|from src.tools.registry\|from src.tools.bm25\|from src.models.router\|from src.utils.token_counter" src/ tests/ cli.py 2>&1 || echo "CLEAN"

# Verify dependencies
uv sync && echo "DEPS OK"
pytest && echo "TESTS OK"
```

## Risks

| Risk | Mitigation |
| --- | --- |
| Surviving files import removed modules | DEP-02 global grep catches this |
| conftest.py has shared fixtures for removed modules | TEST-02 explicitly cleans conftest |
| `openai` used elsewhere (e.g. research.py for Moonshot) | Check before removing — may need to keep or restructure |
| Tests in security/integration/regression reference removed code | TEST-03 explicitly checks these directories |
