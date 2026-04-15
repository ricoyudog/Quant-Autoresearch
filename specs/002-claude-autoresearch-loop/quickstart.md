# Quickstart: Claude Code Autoresearch Loop

## Purpose

Use this workflow to launch, resume, and verify a bounded Claude Code-driven autoresearch run.

## Prerequisites

- Repository at `/Users/chunsingyu/softwares/Quant-Autoresearch`
- Claude Code available from the shell
- Existing deterministic evaluator surfaces are working
- Operator understands the current `program.md` rules

## Launch Workflow

1. Review:
   - `/Users/chunsingyu/softwares/Quant-Autoresearch/program.md`
   - `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/002-claude-autoresearch-loop/spec.md`
   - `/Users/chunsingyu/softwares/Quant-Autoresearch/specs/002-claude-autoresearch-loop/plan.md`

2. Initialize or inspect run state
   - Confirm the strategy target and stop conditions
   - Confirm prior results and notes are available

3. Start a bounded run
   - Launch the runner with an explicit iteration budget
   - Verify that the first round creates both run state and a strategy snapshot

4. Observe round progression
   - Confirm each round writes a structured iteration record
   - Confirm keep/revert decisions are based on evaluator output

5. Resume after interruption
   - Re-launch the runner against existing run state
   - Confirm the next round starts from the persisted state rather than from a reset

## Verification Checklist

- At least one run state file exists
- At least one iteration artifact exists
- Failed or non-improving rounds revert strategy edits
- Retained rounds update the best-known result
- Resume continues from the correct next iteration

## Verification Matrix

Run these checks to validate the contract without depending on a live Claude
iteration:

```bash
tmpdir=$(mktemp -d)
printf '# Program\n' > "$tmpdir/program.md"
printf 'VALUE = 0\n' > "$tmpdir/active_strategy.py"
printf '{}' > "$tmpdir/autoresearch_state.json"
printf 'commit\tscore\tbaseline_sharpe\tstatus\tdescription\n' > "$tmpdir/results.tsv"
mkdir -p "$tmpdir/notes"
printf '# Context\n\nRecent note.\n' > "$tmpdir/context.md"

# Unit + integration coverage for lifecycle, keep/revert, resume, and audit artifacts
.venv/bin/pytest tests/unit/test_autoresearch_runner.py tests/integration/test_autoresearch_runner_integration.py -q

# Wrapper prompt contract
bash scripts/run_claude_iteration.sh 2 --program "$tmpdir/program.md" --strategy "$tmpdir/active_strategy.py" \
  --state-file "$tmpdir/autoresearch_state.json" --output-dir "$tmpdir/iterations" --context-file "$tmpdir/context.md" --dry-run

# Runner dry-run contract + resume/status surface
.venv/bin/python scripts/autoresearch_runner.py --iterations 2 --strategy "$tmpdir/active_strategy.py" \
  --state-file "$tmpdir/autoresearch_state.json" --iteration-root "$tmpdir/iterations" --program "$tmpdir/program.md" \
  --results-file "$tmpdir/results.tsv" --notes-dir "$tmpdir/notes" --dry-run
.venv/bin/python scripts/autoresearch_runner.py --status-only --state-file "$tmpdir/autoresearch_state.json"

# Static safety checks
uv run python -m compileall scripts/autoresearch_runner.py
git diff --check
```

Latest local evidence on 2026-04-13:

- `tests/unit/test_autoresearch_runner.py` + `tests/integration/test_autoresearch_runner_integration.py` → 18 passed
- `bash scripts/run_claude_iteration.sh ... --dry-run` → prompt + invocation contract rendered successfully
- `scripts/autoresearch_runner.py --dry-run` and `--status-only` → contract summary and persisted status output both rendered successfully
- `uv run python -m compileall scripts/autoresearch_runner.py` → passed
- `git diff --check` → clean

## Contract Validation Notes

- Lifecycle contract is covered end to end: initialize/load state, assemble context, snapshot, invoke wrapper, evaluate, keep/revert, persist artifacts, and stop/resume.
- Keep/revert authority remains inside the runner; Claude output is only used for round summaries.
- Resume restores the retained best strategy before the next round executes.

## Residual Risks

- Live multi-round execution still depends on an installed and authenticated Claude Code CLI; the automated matrix validates the runner contract through dry runs and injected command fakes rather than a real agent session.
- No dedicated lint tool is configured in `pyproject.toml`, so verification currently relies on pytest, compileall, diff checks, and diagnostics rather than a project-native Ruff pass.

## Expected Outcome

At the end of this workflow, the repository should support a repeatable outer-loop autoresearch run driven by Claude Code, with deterministic evaluation and auditable keep/revert history.
