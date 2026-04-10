# V2 Minute Autoresearch — Merge Test Plan

## Goal

Ensure the planning package can be reviewed and merged into `main-dev` without hidden root drift or missing execution handoff.

## Merge Checks

- [x] branch is `feature/v2-minute-autoresearch`
- [x] base/target is documented as `main-dev`
- [x] only one canonical feature root exists
- [x] issue drafts point to sprint docs
- [x] sprint docs point back to governing specs and issue drafts
- [x] GitHub issue links are explicit and honest

## Commands

```bash
git branch --show-current
git diff --name-only main-dev..HEAD
find docs/feature/v2-minute-autoresearch -maxdepth 3 -type f | sort
```

## Update Space

### Merge Readiness Notes

- `git branch --show-current` → `feature/v2-minute-autoresearch`
- `git diff --name-only main-dev..HEAD` → umbrella-closeout doc sync only on this branch
- `find docs/feature/v2-minute-autoresearch -maxdepth 3 -type f | sort` → one canonical feature root with issue cards plus sprint1-4 execution docs
- planning workspace landed on `main-dev` via [PR #22](https://github.com/ricoyudog/Quant-Autoresearch/pull/22) on 2026-04-09
- child lanes landed via [PR #23](https://github.com/ricoyudog/Quant-Autoresearch/pull/23), [PR #24](https://github.com/ricoyudog/Quant-Autoresearch/pull/24), [PR #25](https://github.com/ricoyudog/Quant-Autoresearch/pull/25), [PR #26](https://github.com/ricoyudog/Quant-Autoresearch/pull/26), [PR #27](https://github.com/ricoyudog/Quant-Autoresearch/pull/27), and [PR #28](https://github.com/ricoyudog/Quant-Autoresearch/pull/28)
- issue #17 is the final umbrella closeout card; all child issues #18-#21 are already merged / done

### Publication Follow-up

- keep the umbrella issue body aligned with the merged local docs through closeout
- move live issue #17 from `workflow::todo` to `workflow::done` once this umbrella sync merges
