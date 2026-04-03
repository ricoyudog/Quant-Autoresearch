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
| `config/quant-autoresearch.service` | still launches `cli.py run --iterations 100 --safety high` | update or mark obsolete |
| `config/supervisord.conf` | still launches `cli.py run` and injects `GROQ_API_KEY` | update or mark obsolete |

## Step-by-Step Plan

### Step 1 — Confirm `.gitignore` behavior
- [ ] verify `results.tsv` and `run.log` are ignored by the current patterns
- [ ] verify markdown notes under `experiments/notes/` are not ignored
- [ ] document whether any `.gitignore` change is actually required

### Step 2 — Audit service/config drift
- [ ] inspect `config/quant-autoresearch.service`
- [ ] inspect `config/supervisord.conf`
- [ ] decide whether these files are still active deployment surfaces or stale examples
- [ ] if active, align them to supported V2 commands and current env vars
- [ ] if stale, mark them clearly so they stop misleading operators

### Step 3 — Closeout evidence
- [ ] record the exact verification commands used for ignore checks
- [ ] record the chosen config decision
- [ ] hand off to QA/test-plan verification

## Verification Commands

```bash
git check-ignore -v results.tsv run.log
git check-ignore -v experiments/notes/example.md || echo "notes markdown is tracked"
rg -n "cli.py run|GROQ_API_KEY|MOONSHOT_API_KEY" config
uv sync --all-extras --dev
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
