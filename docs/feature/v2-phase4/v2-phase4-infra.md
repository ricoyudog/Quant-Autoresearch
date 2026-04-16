> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# V2 Phase 4 — Infra Lane

> Feature branch: `feature/v2-phase4`
> Umbrella issue: #10
> Lane: Infra / repo hygiene

## Lane Mission

Confirm that repository hygiene and operator surfaces match the post-V2 command set. This lane owns ignore behavior, service/supervisor config drift, and the command/evidence expectations needed before the branch can close.

## In-Scope Files

| File | Current observation | Planned decision |
| --- | --- | --- |
| `.gitignore` | broad `*.log` and `*.tsv` patterns already exist; `experiments/notes/*.md` is currently tracked | verify behavior and only change if wrong |
| `config/quant-autoresearch.service` | retained only as a historical systemd template for the removed daemon | convert it to an inert no-op placeholder so accidental starts do not fail |
| `config/supervisord.conf` | retained only as a historical supervisor template for the removed daemon | convert it to an inert no-op placeholder |

## Step-by-Step Plan

### Step 1 — Confirm `.gitignore` behavior
- [x] verify `results.tsv` and `run.log` are ignored by the current patterns
- [x] verify markdown notes under `experiments/notes/` are not ignored
- [x] document that no `.gitignore` change is required

### Step 2 — Audit service/config drift
- [x] inspect `config/quant-autoresearch.service`
- [x] inspect `config/supervisord.conf`
- [x] decide that both files are stale daemon-era examples rather than active V2 deployment surfaces
- [x] mark both files clearly obsolete instead of force-aligning them to `backtest`

### Step 3 — Closeout evidence
- [x] record the exact verification commands used for ignore checks
- [x] record the chosen config decision
- [x] hand off to QA/test-plan verification

## Verification Commands

```bash
git check-ignore -v results.tsv run.log
git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"
! rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md config src/__init__.py
uv sync --all-extras --dev
```

## Update Space

### Completed Work

- Confirmed that `results.tsv` and `run.log` are still covered by the existing
  global `*.tsv` and `*.log` rules while markdown notes under
  `experiments/notes/` remain tracked.
- Reworked `config/quant-autoresearch.service` and `config/supervisord.conf`
  into inert `/bin/true` placeholders, so the retired `cli.py run` surface
  cannot accidentally execute or fail even if an operator starts the old
  templates.
- Re-ran the Phase 4 closeout verification set after the config cleanup.

### Command Results

- `git check-ignore -v results.tsv run.log`
  - `.gitignore:34:*.tsv  results.tsv`
  - `.gitignore:33:*.log  run.log`
- `git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"`
  - `notes markdown is tracked`
- `! rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md config src/__init__.py`
  - exit code `0` with no matches
- `uv sync --all-extras --dev`
  - `Resolved 134 packages in 3ms`
  - `Checked 117 packages in 2ms`

### Blockers / Deviations

- The stale service and supervisor files were not re-pointed to
  `uv run python cli.py backtest`. That command is a one-shot batch surface, so
  keeping daemon-style restart semantics would still mislead operators.

### Follow-ups

- None; Sprint 3 closeout documentation is posted and issue #10 now sits in `workflow::review`.
