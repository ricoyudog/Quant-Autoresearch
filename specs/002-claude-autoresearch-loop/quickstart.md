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

## Expected Outcome

At the end of this workflow, the repository should support a repeatable outer-loop autoresearch run driven by Claude Code, with deterministic evaluation and auditable keep/revert history.
