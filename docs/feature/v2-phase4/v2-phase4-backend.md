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

### Step 1 — Completed canonical doc refresh
- [x] Replaced the OPENDEV narrative in `CLAUDE.md` with the current V2 workflow centered on `program.md`, `cli.py`, the backtester, the connector, and the active strategy files
- [x] Modernized `README.md`, archived `architecture.md` as a historical note, and aligned entrypoint wording (e.g., `src/__init__.py`) with the surviving command surface
- [x] Captured the lane summary so readers can see that Sprint 1 and Sprint 2 delivered the backend/docs lane

### Step 2 — Close the lane and record evidence
- [x] Verified that no `OPENDEV` or removed-command references remain via the recorded `rg` search and CLI help output
- [x] Documented the Sprint 3 closeout note (`sprint3/sprint3-infra.md`) so issue #10 can stay in `workflow::review` with no follow-up actions

## Verification Commands

```bash
rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md src/__init__.py
uv run python cli.py --help
uv run python cli.py setup-data --help
uv run python cli.py fetch --help
uv run python cli.py backtest --help
```

## Update Space

### Completed Work

- Rewrote `CLAUDE.md` around the current V2 workflow, removing OPENDEV references and specifying the supported command surface plus survived environment variables.
- Modernized `README.md`, archived `architecture.md` as a historical note, and aligned entrypoint wording (including `src/__init__.py`) with the surviving CLI commands.
- Captured the verification evidence and referenced the Sprint 3 closeout note so the lane is clearly marked as done.

### Command Results

- `rg -n "OPENDEV|engine.py|ContextCompactor|PromptComposer|LazyToolRegistry|ModelRouter|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md src/__init__.py` → exit code `1` (no matches)
- `uv run python cli.py --help` → exit code `0` (commands shown: `fetch`, `setup-data`, `backtest`)
- `uv run python cli.py setup-data --help` → exit code `0`
- `uv run python cli.py fetch --help` → exit code `0` (required argument `SYMBOL`, option `--start` default `2020-01-01`)
- `uv run python cli.py backtest --help` → exit code `0` (options `--strategy/-s`, `--symbols/-y`)

### Blockers / Deviations

- None; the backend/docs lane executed as planned.

### Follow-ups

- None; Sprint 3 closeout note is published and issue #10 is already in `workflow::review`.
