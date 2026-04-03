# V2 Phase 4 — Test Plan

> Feature branch: `feature/v2-phase4`
> Umbrella issue: #10

## Objective

Verify that the closeout work removes stale V1 guidance without breaking the current V2 command surface, dependency setup, or tracked-note workflow.

## Baseline

Recorded on `feature/v2-phase4` immediately after branching from `main-dev`:

```bash
uv run pytest --tb=short -q
# 97 passed in 10.05s

uv run python cli.py --help
# commands: fetch, setup-data, backtest
```

## Verification Matrix

| Area | Command | Expected result |
| --- | --- | --- |
| Dependencies | `uv sync --all-extras --dev` | succeeds without introducing new dependency drift |
| Full tests | `uv run pytest --tb=short -q` | suite remains green |
| CLI root help | `uv run python cli.py --help` | only supported commands shown |
| CLI setup-data help | `uv run python cli.py setup_data --help` | help exits successfully |
| CLI fetch help | `uv run python cli.py fetch --help` | help exits successfully |
| CLI backtest help | `uv run python cli.py backtest --help` | help exits successfully |
| Stale doc wording | `rg -n "OPENDEV|cli.py run|cli.py status|cli.py report|GROQ_API_KEY|MOONSHOT_API_KEY" CLAUDE.md README.md architecture.md config src/__init__.py` | no stale references remain in the kept/current surfaces |
| Ignore rules | `git check-ignore -v results.tsv run.log` | ignored by current rules |
| Notes tracking | `git check-ignore -v experiments/notes/example.md || echo "tracked"` | notes markdown remains tracked |

## Manual Review Checklist

- [ ] `CLAUDE.md` now describes the current V2 workflow instead of the removed OPENDEV runtime
- [ ] `README.md` no longer instructs users to run unsupported commands
- [ ] `architecture.md` has an explicit keep/archive/remove decision
- [ ] config files no longer imply `cli.py run` is the supported runtime if that is no longer true
- [ ] issue #10 references the new docs workspace

## Evidence Capture

Record the following in the sprint/update docs during execution:

- exact command outputs for `uv sync`, `pytest`, and CLI help
- grep output proving stale guidance is gone from kept/current surfaces
- config decision notes for `config/quant-autoresearch.service` and `config/supervisord.conf`
- any deliberate exceptions, such as a historical document retained with an archive banner

## Acceptance Criteria

- [ ] all verification commands succeed
- [ ] the docs updated by Phase 4 are V2-correct
- [ ] `.gitignore` behavior is verified and documented
- [ ] config drift decisions are recorded
- [ ] issue #10 points to the canonical planning workspace
