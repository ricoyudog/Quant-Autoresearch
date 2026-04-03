# V2 Phase 4 — Backend / Docs Lane

> Feature branch: `feature/v2-phase4`
> Umbrella issue: #10
> Lane: Backend / agent-facing docs

## Lane Mission

Bring the primary documentation and agent-guidance surfaces into line with the V2 architecture that already exists on `main-dev`. This lane owns the narrative truth of the repo: supported commands, current architecture, current file roles, and which documents are still current versus historical.

## In-Scope Files

| File | Current problem | Planned outcome |
| --- | --- | --- |
| `CLAUDE.md` | still documents OPENDEV, removed modules, old commands, old env vars | rewrite as V2 operator guide |
| `README.md` | still advertises OPENDEV architecture and `run/status/report` workflow | rewrite as V2 project entrypoint |
| `architecture.md` | fully V1 | rewrite, archive, or remove from the primary path with an explicit decision |
| `src/__init__.py` | stale package description | update to neutral V2 wording |

## Out of Scope

- functional feature development
- refactoring runtime Python modules beyond wording-only metadata
- changing test behavior except where doc examples or smoke commands need alignment
- broad cleanup of historical research notes unless they are linked from primary entrypoints

## Step-by-Step Plan

### Step 1 — Rewrite `CLAUDE.md`
- [ ] replace the project overview with a V2 description centered on `program.md`, `src/core/backtester.py`, `src/data/connector.py`, and `src/strategies/active_strategy.py`
- [ ] remove references to `src/core/engine.py`, `src/context/*`, `src/tools/registry.py`, `src/models/router.py`, and removed prompt composition
- [ ] update command examples to the supported V2 CLI only
- [ ] update environment variables to the surviving set
- [ ] verify with:
  - `rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md`

### Step 2 — Refresh `README.md`
- [ ] replace OPENDEV-first messaging with current V2 positioning
- [ ] update project structure to match what survived cleanup
- [ ] replace old setup/data/run examples with supported V2 commands
- [ ] decide whether historical research/RAG details belong in the main README or in secondary docs only
- [ ] verify with:
  - `rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" README.md`

### Step 3 — Resolve `architecture.md`
- [ ] choose one path and record the decision:
  - rewrite as V2 architecture
  - archive as historical V1 reference with clear banner
  - remove from the primary repo surface
- [ ] if kept, ensure the file no longer claims removed OPENDEV components are current
- [ ] verify the chosen path from the repo root entrypoints

### Step 4 — Clean residual entrypoint wording
- [ ] update `src/__init__.py` package banner
- [ ] scan touched docs for stale OPENDEV wording
- [ ] note any adjacent follow-up candidates outside issue #10 scope

## Verification Commands

```bash
rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md src/__init__.py
uv run python cli.py --help
uv run python cli.py setup_data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
```

## Update Space

### Completed Work

- none yet

### Command Results

- pending

### Blockers / Deviations

- pending

### Follow-ups

- pending
