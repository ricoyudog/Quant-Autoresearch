# V2 Minute Autoresearch — Merge Test Plan

## Goal

Ensure the planning package can be reviewed and merged into `main-dev` without hidden root drift or missing execution handoff.

## Merge Checks

- [ ] branch is `feature/v2-minute-autoresearch`
- [ ] base/target is documented as `main-dev`
- [ ] only one canonical feature root exists
- [ ] issue drafts point to sprint docs
- [ ] sprint docs point back to governing specs and issue drafts
- [ ] GitHub issue links are explicit and honest

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

- keep local issue-card drafts aligned with GitHub issues
- merge this docs package into `main-dev`
