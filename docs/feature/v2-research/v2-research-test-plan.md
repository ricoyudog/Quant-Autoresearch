# V2 Research -- Test Plan

> Feature branch: `feature/v2-research`
> Umbrella issue: #13
> Last updated: 2026-04-08
> Planning status: verification complete; execution evidence recorded

## Objective

Verify that the V2 research surface works end to end: vault configuration is correct, the Playbook
surface is removed cleanly, `research` and `analyze` generate the planned reports, knowledge notes
and memory guidance exist, and the surviving test suite stays green while the new coverage lands.

## Evidence Expectations

- Record the pre-change baseline before Sprint 1 starts
- Treat Playbook-import scans and CLI smoke runs as hard release gates, not optional spot checks
- Capture vault-write evidence separately from unit-test output when commands touch local paths
- Store merge-ready evidence in the issue or PR summary with links back to this workspace

## Coverage Matrix

| Phase | Lane | Surface | Commands / Evidence | Exit Criteria |
| --- | --- | --- | --- | --- |
| Phase 0 | QA | Repo baseline | `uv sync --all-extras --dev`, `pytest --tb=short` | baseline result recorded before branch work starts |
| Sprint 1 | QA + Infra | vault config, setup CLI, Playbook removal, research-writer surface | vault unit tests, `uv run python cli.py setup_vault`, grep scan | directories create cleanly, Playbook imports are gone, vault writer works |
| Sprint 2 | QA | analysis helpers, `research`, `analyze`, knowledge / memory docs | helper unit tests, CLI tests, integration tests, `program.md` diff | commands and helpers match the planned runtime surface |
| Phase 3 | QA + Infra | full regression and merge gate | `pytest --tb=short -v`, CLI smoke runs, issue evidence update | review-ready evidence exists with no unresolved regressions |

## Planned Test Files

### New Coverage

| Test File | Surface | Key Cases |
| --- | --- | --- |
| `tests/unit/test_vault_config.py` | `config/vault.py` | path resolution, env override, idempotent directory creation |
| `tests/unit/test_vault_writer.py` | research / analysis report writer | frontmatter, markdown structure, file creation |
| `tests/unit/test_technical.py` | `src/analysis/technical.py` | momentum, volatility, volume, key-level calculations |
| `tests/unit/test_regime.py` | `src/analysis/regime.py` | bull / bear and quiet / volatile classification outputs |
| `tests/unit/test_market_context.py` | `src/analysis/market_context.py` | SPY correlation, MA distance, structured output shape |
| `tests/unit/test_cli_research.py` | `cli.py research` | shallow mode, frontmatter, stdout vs vault output, dedup behavior |
| `tests/unit/test_cli_analyze.py` | `cli.py analyze` | report sections, output mode, graceful handling of bad ticker or missing data |
| `tests/unit/test_cli_setup_vault.py` | `cli.py setup_vault` | directory creation and idempotency |
| `tests/integration/test_research_pipeline.py` | full research flow | query -> markdown report -> vault write -> file exists |
| `tests/integration/test_analyze_pipeline.py` | full analysis flow | ticker -> report -> vault write -> file exists |

### Existing Files To Expand

| Test File | Planned Change |
| --- | --- |
| `tests/unit/test_cli.py` | replace the "research command removed" assertion with the new command-registration contract |
| `tests/unit/test_research.py` | expand around report formatting, dedup, and cache / vault interactions |
| `tests/conftest.py` | add vault tmp-path fixtures and sample data for analysis helpers |

### Existing Tests To Remove Or Retire

| Test File | Planned Change |
| --- | --- |
| `tests/unit/test_playbook_memory.py` | delete once `src/memory/playbook.py` is removed |

### Existing Tests To Keep Green

| Test File | Surface |
| --- | --- |
| `tests/unit/test_backtester_v2.py` | backtester runtime |
| `tests/unit/test_data.py` | current data-loading helpers until the analysis path replaces or reuses them |
| `tests/unit/test_retry_logic.py` | retry helpers |
| `tests/unit/test_runner.py` | runner flow |
| `tests/unit/test_security.py` | backtester sandbox and security rules |
| `tests/unit/test_strategy_interface.py` | strategy interface |
| `tests/unit/test_telemetry_wandb.py` | telemetry |
| `tests/unit/test_tracker_metrics.py` | iteration tracking |
| `tests/regression/test_determinism.py` | deterministic behavior |
| `tests/security/test_adversarial.py` | adversarial security coverage |

## Phase Gates

### Phase 0 -- Baseline

```bash
uv sync --all-extras --dev
pytest --tb=short
```

Record total tests, pass / fail count, and any existing skips before feature work starts.

### Sprint 1 -- Vault Foundation + Playbook Removal

```bash
pytest tests/unit/test_vault_config.py tests/unit/test_vault_writer.py -v

uv run python cli.py setup_vault

test ! -f src/memory/playbook.py
test ! -f tests/unit/test_playbook_memory.py
grep -rn "from src.memory.playbook\|from memory.playbook\|Playbook" src/ tests/ cli.py || echo "CLEAN"

pytest tests/unit/test_cli.py tests/unit/test_research.py -v
```

### Sprint 2 -- Research CLI + Analysis + Knowledge

```bash
pytest tests/unit/test_technical.py tests/unit/test_regime.py tests/unit/test_market_context.py -v
pytest tests/unit/test_cli_research.py tests/unit/test_cli_analyze.py tests/unit/test_cli_setup_vault.py -v
pytest tests/integration/test_research_pipeline.py tests/integration/test_analyze_pipeline.py -v

grep -n "Research Capabilities" program.md
grep -n "Memory Access Patterns" program.md
```

### Phase 3 -- Full Regression

```bash
pytest --tb=short -v

uv run python cli.py research "intraday momentum strategy minute bars" --depth shallow --output stdout
uv run python cli.py analyze SPY --start 2025-01-01 --output stdout
```

Any failures in surviving tests outside the research scope still block closeout until they are
explained or resolved.

## Merge Gate Checklist

- [x] Baseline test result recorded before feature work
- [x] `tests/unit/test_vault_config.py` and `tests/unit/test_vault_writer.py` pass
- [x] `tests/unit/test_playbook_memory.py` is removed and no surviving import references Playbook
- [x] `tests/unit/test_cli.py` matches the new registered commands
- [x] `tests/unit/test_technical.py`, `tests/unit/test_regime.py`, and `tests/unit/test_market_context.py` pass
- [x] `tests/unit/test_cli_research.py`, `tests/unit/test_cli_analyze.py`, and `tests/unit/test_cli_setup_vault.py` pass
- [x] `tests/integration/test_research_pipeline.py` and `tests/integration/test_analyze_pipeline.py` pass or have an explicitly documented guarded-smoke replacement
- [x] `program.md` contains the final research and memory guidance sections
- [x] `pytest --tb=short -v` passes
- [x] `uv run python cli.py setup_vault` works end to end
- [x] `uv run python cli.py research ...` works end to end
- [x] `uv run python cli.py analyze ...` works end to end
