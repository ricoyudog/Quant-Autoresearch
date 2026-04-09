# V2 Minute Autoresearch — Merge Test Plan

## Goal

Ensure the planning package can be reviewed and merged into `main-dev` without hidden root drift or missing execution handoff.

## Merge Checks

- [ ] branch is `feature/v2-minute-autoresearch`
- [ ] base/target is documented as `main-dev`
- [ ] only one canonical feature root exists
- [ ] issue drafts point to sprint docs
- [ ] sprint docs point back to governing specs and issue drafts
- [ ] GitLab publication blocker is explicit and honest

## Commands

```bash
git branch --show-current
git diff --name-only main-dev..HEAD
find docs/feature/v2-minute-autoresearch -maxdepth 3 -type f | sort
```

## Update Space

### Merge Readiness Notes

- leave blank until closeout

### Publication Follow-up

- publish local issue drafts to GitLab
- replace draft references with real IDs

