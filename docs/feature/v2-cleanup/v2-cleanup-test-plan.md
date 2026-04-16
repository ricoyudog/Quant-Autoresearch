> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Cleanup — Test Plan

> Feature branch: `feature/v2-cleanup`
> Umbrella issue: #1

## Objective

Verify that all V1 components are cleanly removed without breaking the surviving codebase.

## Pre-removal Baseline

Before any deletion, confirm the current state is green:

```bash
uv sync --all-extras --dev
pytest --tb=short
```

Record the test count and result as baseline.

## Test Removal Matrix

### Files to delete (unit tests)
| Test File | Module Under Test | Delete? |
| --- | --- | --- |
| `tests/unit/test_engine_opendev.py` | engine.py | YES |
| `tests/unit/test_guard_opendev.py` | safety/guard.py | YES |
| `tests/unit/test_tool_registry.py` | tools/registry.py | YES |
| `tests/unit/test_router_routing.py` | models/router.py | YES |
| `tests/unit/test_compactor_acc.py` | context/compactor.py | YES |
| `tests/unit/test_compactor_logic.py` | context/compactor.py | YES |
| `tests/unit/test_composer_modular.py` | context/composer.py | YES |
| `tests/unit/test_bm25_tool.py` | tools/bm25_search.py | YES |

### Files to evaluate (integration/regression/security)
| Test File | References Removed Code? | Action |
| --- | --- | --- |
| `tests/integration/test_engine_integration.py` | engine.py | DELETE |
| `tests/integration/test_loop.py` | engine loop | DELETE |
| `tests/regression/test_engine_arity.py` | engine arity | DELETE |
| `tests/regression/test_editable_region.py` | EDITABLE REGION markers | DELETE |
| `tests/security/test_adversarial.py` | backtester sandbox | KEEP — verify no removed-module refs |
| `tests/security/test_safety_workflow.py` | safety guard workflow | EVALUATE — may reference SafetyGuard |
| `tests/integration/test_integration.py` | general integration | KEEP — verify no removed-module refs |

### Files to keep (must survive)
| Test File | Module Under Test | Keep? |
| --- | --- | --- |
| `tests/unit/test_data.py` | data/connector.py | YES |
| `tests/unit/test_security.py` | backtester security | YES |
| `tests/unit/test_playbook_memory.py` | memory/playbook.py | YES |
| `tests/unit/test_research.py` | core/research.py | YES |
| `tests/unit/test_retry_logic.py` | utils/retries.py | YES |
| `tests/unit/test_runner.py` | runner | EVALUATE |
| `tests/unit/test_telemetry_wandb.py` | utils/telemetry.py | YES |
| `tests/unit/test_tracker_metrics.py` | utils/iteration_tracker.py | YES |
| `tests/regression/test_determinism.py` | determinism | EVALUATE |
| `tests/conftest.py` | shared fixtures | CLEAN — remove fixtures for deleted modules |

## Verification Steps

### Step 1: After deleting test files
```bash
# Verify deleted files are gone
git status --short | grep "^D "
pytest --tb=short
```

### Step 2: Conftest cleanup
```bash
# Check conftest for references to removed modules
grep -n "engine\|guard\|router\|compactor\|composer\|registry\|token_counter\|bm25" tests/conftest.py
```
Clean any matching fixtures or imports.

### Step 3: Security/integration scan
```bash
# Check remaining test files for broken imports
grep -rn "from src.core.engine\|from src.context\|from src.safety.guard\|from src.tools.registry\|from src.tools.bm25\|from src.models.router\|from src.utils.token_counter\|SafetyGuard\|LazyToolRegistry\|ModelRouter\|ContextCompactor\|PromptComposer\|BM25Search" tests/
```
Must return zero hits.

### Step 4: Full test run
```bash
pytest --tb=short -v
```
All remaining tests must pass.

### Step 5: CLI verification
```bash
uv run python cli.py status
```
Must not crash with import errors.

## Acceptance Criteria

- [ ] All 12 test files marked DELETE are removed
- [ ] `tests/conftest.py` has no fixtures for removed modules
- [ ] No remaining test file imports from removed modules
- [ ] `pytest` passes with 0 failures
- [ ] `uv run python cli.py status` runs without error
